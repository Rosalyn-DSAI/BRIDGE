import os
import secrets
import re
from email.utils import parseaddr
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from werkzeug.exceptions import HTTPException
from .db import close_db, init_db
from .security import csrf_protect, csrf_token

def create_app(test_config=None):
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / '.env')
    app = Flask(__name__, instance_path=str(root/'instance'))
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    env = os.getenv('APP_ENV', 'local')
    app.config.update(
        APP_ENV=env, AI_MODE=os.getenv('AI_MODE','demo'), MAIL_MODE=os.getenv('MAIL_MODE','local'),
        SECRET_KEY=os.getenv('SECRET_KEY',''), BASE_URL=os.getenv('BASE_URL','http://127.0.0.1:5000').rstrip('/'),
        DATABASE=os.getenv('DATABASE_PATH') or str(root/'instance'/'bridge.sqlite3'),
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY',''), OPENAI_MODEL=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY',''), GEMINI_MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash'),
        SMTP_USER=os.getenv('SMTP_USER','').strip(),
        SMTP_APP_PASSWORD=''.join(os.getenv('SMTP_APP_PASSWORD','').split()),
        MAIL_FROM=os.getenv('MAIL_FROM','').strip(),
        WORKER_INTERVAL=int(os.getenv('WORKER_INTERVAL','10')),
        MAX_CONTENT_LENGTH=100000, SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    )
    if test_config:
        app.config.update(test_config)
    c = app.config
    if c['APP_ENV'] not in ('local','production') or c['AI_MODE'] not in ('demo','openai','gemini') or c['MAIL_MODE'] not in ('local','gmail'):
        raise RuntimeError('Invalid APP_ENV, AI_MODE, or MAIL_MODE.')
    base = urlsplit(c['BASE_URL'])
    if not base.hostname or base.path or base.query or base.fragment or base.username or base.password:
        raise RuntimeError('BASE_URL must be an origin such as https://bridge.example.com.')
    if c['APP_ENV'] == 'production':
        if c['MAIL_MODE'] != 'gmail' or base.scheme != 'https' or len(c['SECRET_KEY']) < 32:
            raise RuntimeError('Production requires Gmail SMTP, an HTTPS BASE_URL, and a random SECRET_KEY of at least 32 characters.')
        c['SESSION_COOKIE_SECURE'] = True
    elif base.hostname not in ('localhost','127.0.0.1') or base.scheme != 'http':
        raise RuntimeError('Local review must use a localhost HTTP BASE_URL.')
    c['TRUSTED_HOSTS'] = [base.hostname] + (['localhost','127.0.0.1'] if c['APP_ENV']=='local' else [])
    if not c['SECRET_KEY']:
        keyfile = Path(app.instance_path)/'.secret-key'
        try:
            with keyfile.open('x') as f:
                f.write(secrets.token_hex(32))
            keyfile.chmod(0o600)
        except FileExistsError:
            pass
        c['SECRET_KEY'] = keyfile.read_text().strip()
    if c['AI_MODE']=='openai' and not c['OPENAI_API_KEY']:
        raise RuntimeError('Set OPENAI_API_KEY before enabling live AI.')
    if c['AI_MODE']=='gemini' and not c['GEMINI_API_KEY']:
        raise RuntimeError('Set GEMINI_API_KEY in .env before enabling Gemini.')
    if c['MAIL_MODE']=='gmail':
        if not re.fullmatch(r'[A-Za-z0-9._%+\-]+@gmail\.com', c['SMTP_USER'], re.I):
            raise RuntimeError('Set SMTP_USER to your new Gmail sender address in .env.')
        if len(c['SMTP_APP_PASSWORD']) != 16:
            raise RuntimeError('Set SMTP_APP_PASSWORD to your 16-character Google app password in .env.')
        if not c['MAIL_FROM']:
            c['MAIL_FROM'] = 'BRIDGE <' + c['SMTP_USER'] + '>'
        if any(ch in c['MAIL_FROM'] for ch in '\r\n') or parseaddr(c['MAIL_FROM'])[1].lower() != c['SMTP_USER'].lower():
            raise RuntimeError('MAIL_FROM must use the same Gmail address as SMTP_USER, or be left blank.')
    Path(c['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    app.before_request(csrf_protect)
    @app.before_request
    def establish_session():
        if 'dev_scope' not in session:
            session['dev_scope'] = secrets.token_urlsafe(24)
        csrf_token()
    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if c['APP_ENV']=='production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response
    @app.errorhandler(HTTPException)
    def error(exc):
        if request.path.startswith('/api/'):
            return jsonify(error=exc.description), exc.code
        return exc
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        init_db()
    return app
