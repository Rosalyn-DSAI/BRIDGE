"""Local inbox and Gmail SMTP delivery. Never logs credentials or SMTP bodies."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate
from hashlib import sha256
from flask import current_app
from .security import clock

class MailError(RuntimeError):
    def __init__(self, message, retryable=True):
        super().__init__(message)
        self.retryable = retryable

def send_mail(db, *, recipient, subject, body, action_url, kind, key, scope):
    c = current_app.config
    if c['MAIL_MODE'] == 'local':
        db.execute('INSERT OR IGNORE INTO local_messages '
                   '(scope,recipient,subject,body,action_url,kind,created_at,message_key) '
                   'VALUES (?,?,?,?,?,?,?,?)',
                   (scope, recipient, subject, body, action_url, kind, clock(), key))
        return 'local-' + key
    if c['MAIL_MODE'] != 'gmail':
        raise MailError('This edition supports MAIL_MODE=gmail or local.', False)
    msg = EmailMessage()
    msg['From'] = c['MAIL_FROM']
    msg['To'] = recipient
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=False)
    msg['Message-ID'] = '<bridge-' + sha256(key.encode()).hexdigest() + '@gmail.com>'
    msg.set_content(body + '\n\n' + action_url)
    smtp = None
    sending = False
    try:
        smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465,
                               context=ssl.create_default_context(), timeout=20)
        smtp.login(c['SMTP_USER'], c['SMTP_APP_PASSWORD'])
        sending = True
        refused = smtp.send_message(msg, from_addr=c['SMTP_USER'], to_addrs=[recipient])
        if refused:
            raise MailError('Gmail refused the recipient. Check the email address.', False)
        return str(msg['Message-ID'])
    except smtplib.SMTPAuthenticationError as exc:
        raise MailError('Gmail login failed. Check SMTP_USER and the Google app password, then restart both terminals.', False) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise MailError('Gmail refused the recipient. Check the email address.', False) from exc
    except smtplib.SMTPResponseException as exc:
        code = int(exc.smtp_code)
        raise MailError(f'Gmail SMTP {code}: sending was rejected. Check the sender account for limits or restrictions.', 400 <= code < 500) from exc
    except (OSError, smtplib.SMTPException) as exc:
        if sending:
            raise MailError('Delivery uncertain: connection interrupted while sending. Check the sender Sent folder and recipient inbox before creating another reminder.', False) from exc
        raise MailError('Cannot connect securely to Gmail SMTP. Check internet access and whether port 465 is blocked.') from exc
    finally:
        if smtp is not None:
            # Do not turn an accepted delivery into a failure if connection cleanup fails.
            try:
                smtp.close()
            except (OSError, smtplib.SMTPException):
                pass

COPY = {
 'en': ('Reminder: task still marked not done', 'This task is still marked as not done:', 'Deadline', 'Open your task. If you have completed the instruction, mark it done.'),
 'zh': ('提醒：任务仍标记为未完成', '以下任务仍标记为未完成：', '截止时间', '打开任务。如果您已完成要求，请将其标记为已完成。'),
 'ja': ('リマインダー：未完了のタスク', 'このタスクはまだ未完了になっています：', '期限', 'タスクを開いてください。作業が終わっている場合は、完了にしてください。'),
 'es': ('Recordatorio: tarea pendiente', 'Esta tarea sigue marcada como pendiente:', 'Fecha límite', 'Abre tu tarea. Si ya completaste la instrucción, márcala como terminada.'),
}

def reminder_copy(title, due, zone, language):
    from .dates import display_time
    subject, intro, label, footer = COPY[language]
    return subject, f'{intro}\n\n{title}\n\n{label}: {display_time(due, zone, language)}\n\n{footer}'
