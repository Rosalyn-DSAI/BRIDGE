"""Persistent reminders. Small-project design: one worker and one SQLite volume."""
from .db import get_db
from .mail import MailError, send_mail
from .security import clock

def deliver_due(now=None, user_id=None):
    now = clock() if now is None else now
    db = get_db()
    query = ('SELECT r.id FROM reminders r JOIN tasks t ON t.id=r.task_id '
             "WHERE r.status='pending' AND r.next_attempt<=?")
    params = [now]
    if user_id is not None:
        query += ' AND t.user_id=?'
        params.append(user_id)
    ids = db.execute(query+' ORDER BY r.next_attempt LIMIT 20', params).fetchall()
    sent = failed = 0
    for item in ids:
        # Serialize claim/check/send with completion to prevent pre-send races.
        # Holds a write lock for the provider call; appropriate only for a small prototype.
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT r.*,t.status task_status,t.due_at,u.email,u.auth_scope '
                             'FROM reminders r JOIN tasks t ON t.id=r.task_id '
                             'JOIN users u ON u.id=t.user_id WHERE r.id=?', (item['id'],)).fetchone()
            if not row or row['status'] != 'pending' or row['next_attempt'] > now:
                continue
            if row['task_status'] != 'pending':
                db.execute("UPDATE reminders SET status='canceled' WHERE id=?", (row['id'],))
                continue
            # Bound retries to a 23-hour period; SMTP does not guarantee deduplication.
            if row['first_attempt'] and now-row['first_attempt'] >= 23*3600:
                db.execute("UPDATE reminders SET status='failed',last_error=? WHERE id=?",
                           ('Retry window expired; inspect delivery manually.', row['id']))
                failed += 1
                continue
            try:
                provider_id = send_mail(db, recipient=row['email'], subject=row['subject'],
                                        body=row['body'], action_url=row['action_url'], kind='reminder',
                                        key='reminder-'+row['id'], scope=row['auth_scope'])
                db.execute("UPDATE reminders SET status='sent',provider_id=?,attempts=attempts+1,"
                           'first_attempt=COALESCE(first_attempt,?),last_error=NULL WHERE id=?',
                           (provider_id, now, row['id']))
                sent += 1
            except MailError as exc:
                attempts = row['attempts']+1
                status = 'failed' if attempts >= 5 or not exc.retryable else 'pending'
                db.execute('UPDATE reminders SET attempts=?,status=?,next_attempt=?,last_error=?, '
                           'first_attempt=COALESCE(first_attempt,?) WHERE id=?',
                           (attempts, status, now+min(60*2**attempts,3600), str(exc), now, row['id']))
                failed += 1
    return {'processed': sent+failed, 'sent': sent, 'failed': failed}
