import smtplib
import ssl
import pytest
from bridge import create_app
from bridge.mail import send_mail, MailError
from bridge.db import get_db
from bridge.reminders import deliver_due
from conftest import post, login

@pytest.fixture
def smtp(app, monkeypatch):
    app.config.update(MAIL_MODE='gmail', SMTP_USER='bridge.sender@gmail.com',
                      SMTP_APP_PASSWORD='abcdefghijklmnop', MAIL_FROM='BRIDGE <bridge.sender@gmail.com>')
    class Fake:
        messages=[]
        def __init__(self, host, port, context, timeout):
            assert (host,port)==('smtp.gmail.com',465)
            assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname
        def login(self, user, password):
            assert user=='bridge.sender@gmail.com' and password=='abcdefghijklmnop'
        def send_message(self, msg, from_addr, to_addrs):
            assert from_addr=='bridge.sender@gmail.com'
            self.messages.append((msg,to_addrs));return {}
        def close(self):pass
    monkeypatch.setattr('bridge.mail.smtplib.SMTP_SSL',Fake)
    return Fake

def send(app):
    with app.app_context():
        return send_mail(get_db(),recipient='colleague@example.org',subject='提醒',body='请完成任务',action_url='http://localhost:5000',kind='reminder',key='stable',scope='x')

def test_other_recipient_and_unicode(app,smtp):
    assert send(app)==send(app)
    msg, recipients=smtp.messages[0]
    assert recipients==['colleague@example.org']
    assert '请完成任务' in msg.get_content()

def test_signin_uses_gmail(app,client,smtp):
    assert post(client,'/api/auth/request',{'email':'colleague@example.org'}).status_code==200
    assert smtp.messages[0][1]==['colleague@example.org']
    assert '/auth/confirm?' in smtp.messages[0][0].get_content()

@pytest.mark.parametrize('failure,phrase,retryable',[
    (smtplib.SMTPAuthenticationError(535,b'private password'),'login failed',False),
    (smtplib.SMTPRecipientsRefused({'private@example.org':(550,b'private')}),'refused',False),
    (smtplib.SMTPDataError(451,b'private'),'451',True),
    (smtplib.SMTPDataError(550,b'private'),'550',False),
    (TimeoutError('private'),'uncertain',False),
])
def test_safe_send_errors(app,smtp,monkeypatch,failure,phrase,retryable):
    def fail(*a,**k):raise failure
    monkeypatch.setattr(smtp,'send_message',fail)
    with pytest.raises(MailError) as err:send(app)
    assert phrase in str(err.value) and 'private' not in str(err.value)
    assert err.value.retryable is retryable

def test_connect_failure_retryable(app,smtp,monkeypatch):
    def fail(*a,**k):raise OSError('private')
    monkeypatch.setattr('bridge.mail.smtplib.SMTP_SSL',fail)
    with pytest.raises(MailError) as err:send(app)
    assert err.value.retryable and 'private' not in str(err.value)

def test_cleanup_failure_does_not_resend(app,smtp,monkeypatch):
    def fail(*a):raise OSError('closed')
    monkeypatch.setattr(smtp,'close',fail)
    assert send(app).startswith('<bridge-')

def test_config_derives_sender(tmp_path):
    app=create_app({'TESTING':True,'APP_ENV':'local','AI_MODE':'demo','MAIL_MODE':'gmail',
      'SMTP_USER':'bridge.sender@gmail.com','SMTP_APP_PASSWORD':'abcdefghijklmnop','MAIL_FROM':'',
      'SECRET_KEY':'test','DATABASE':str(tmp_path/'db'),'BASE_URL':'http://localhost:5000'})
    assert app.config['MAIL_FROM']=='BRIDGE <bridge.sender@gmail.com>'

@pytest.mark.parametrize('overrides',[
    {'SMTP_APP_PASSWORD':''},{'SMTP_USER':'not-an-email'},
    {'MAIL_FROM':'BRIDGE <other@gmail.com>'},{'MAIL_FROM':'bad\r\nheader'}])
def test_bad_config_rejected(tmp_path,overrides):
    c=dict(TESTING=True,APP_ENV='local',AI_MODE='demo',MAIL_MODE='gmail',SMTP_USER='bridge.sender@gmail.com',SMTP_APP_PASSWORD='abcdefghijklmnop',MAIL_FROM='',SECRET_KEY='test',DATABASE=str(tmp_path/'db'),BASE_URL='http://localhost:5000')
    c.update(overrides)
    with pytest.raises(RuntimeError):create_app(c)

def test_worker_gmail_and_done_cancellation(app,client,smtp):
    from test_app import task_payload
    app.config['MAIL_MODE']='local'
    login(client,'colleague@example.org')
    first=post(client,'/api/tasks',task_payload())
    assert first.status_code in (200,201)
    app.config['MAIL_MODE']='gmail'
    with app.app_context():
        row=get_db().execute('SELECT * FROM reminders').fetchone()
        assert deliver_due(row['next_attempt'])['sent']==1
        assert deliver_due(row['next_attempt'])['sent']==0
    assert smtp.messages[0][1]==['colleague@example.org']
    second=post(client,'/api/tasks',task_payload()).json['id']
    assert post(client,f'/api/tasks/{second}/complete',{'confirmed':True}).status_code==200
    with app.app_context():
        assert deliver_due(row['next_attempt']+60)['sent']==0
    assert len(smtp.messages)==1

def test_uncertain_failure_not_retried(app,client,monkeypatch):
    from test_app import task_payload
    login(client)
    post(client,'/api/tasks',task_payload())
    def fail(*a,**k):raise MailError('Delivery uncertain',False)
    monkeypatch.setattr('bridge.reminders.send_mail',fail)
    with app.app_context():
        row=get_db().execute('SELECT * FROM reminders').fetchone()
        assert deliver_due(row['next_attempt'])['failed']==1
        record=get_db().execute('SELECT * FROM reminders').fetchone()
        assert record['status']=='failed' and record['attempts']==1
        assert deliver_due(row['next_attempt']+999)['processed']==0


def test_password_spaces_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('SMTP_APP_PASSWORD','abcd efgh ijkl mnop')
    app=create_app(dict(TESTING=True, APP_ENV='local', AI_MODE='demo', MAIL_MODE='gmail',
        SMTP_USER='bridge.sender@gmail.com', MAIL_FROM='', SECRET_KEY='test',
        DATABASE=str(tmp_path/'db'), BASE_URL='http://localhost:5000'))
    assert app.config['SMTP_APP_PASSWORD']=='abcdefghijklmnop'
