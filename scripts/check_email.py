"""Check Gmail SMTP login only; never sends email or prints credentials."""
import sys
import smtplib
import ssl
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import create_app

def main():
    smtp = None
    try:
        app = create_app()
        if app.config['MAIL_MODE'] != 'gmail':
            print('Set MAIL_MODE=gmail in .env first.')
            return 1
        smtp = smtplib.SMTP_SSL('smtp.gmail.com',465,context=ssl.create_default_context(),timeout=20)
        smtp.login(app.config['SMTP_USER'],app.config['SMTP_APP_PASSWORD'])
        print('SUCCESS: Gmail SMTP login works. No email was sent. Test sign-in in Bridge next.')
        return 0
    except smtplib.SMTPAuthenticationError:
        print('CHECK FAILED: Gmail rejected login. Check sender address and app password.')
    except (OSError, smtplib.SMTPException):
        print('CHECK FAILED: Could not complete Gmail SMTP connection/login. Check network and account restrictions.')
    except RuntimeError as exc:
        print('CHECK FAILED:',str(exc))
    finally:
        if smtp is not None:
            try:smtp.close()
            except (OSError,smtplib.SMTPException):pass
    return 1

if __name__=='__main__':
    raise SystemExit(main())
