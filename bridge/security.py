import hashlib
import hmac
import secrets
import time
from functools import wraps
from flask import abort, current_app, request, session
from .db import get_db

def clock():
    return int(time.time())

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']

def csrf_protect():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
        expected = session.get('csrf', '')
        if not expected or not hmac.compare_digest(expected, token):
            abort(403, description='Session expired or invalid request. Refresh the page and try again.')

def user_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            abort(401, description='Sign in before saving or viewing tasks.')
        return fn(*args, **kwargs)
    return wrapped

def rate_limit(kind, limit=10, seconds=600, identity=None):
    # Do not trust caller-supplied X-Forwarded-For. Configure proxy trust separately.
    raw = kind + ':' + (identity or request.remote_addr or 'unknown')
    key = hmac.new(current_app.secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()
    db, now = get_db(), clock()
    with db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM rate_limits WHERE bucket=?', (key,)).fetchone()
        if row and row['expires_at'] > now and row['hits'] >= limit:
            abort(429, description='Too many requests. Please wait a few minutes.')
        hits = row['hits'] + 1 if row and row['expires_at'] > now else 1
        expiry = row['expires_at'] if row and row['expires_at'] > now else now + seconds
        db.execute('INSERT OR REPLACE INTO rate_limits VALUES (?,?,?)', (key, hits, expiry))
        db.execute('DELETE FROM rate_limits WHERE expires_at < ?', (now-86400,))
