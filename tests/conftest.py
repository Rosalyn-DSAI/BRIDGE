from urllib.parse import urlsplit, parse_qs
import pytest
from bridge import create_app

@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING':True, 'SECRET_KEY':'test-key-not-for-deployment',
        'DATABASE':str(tmp_path/'test.sqlite3'), 'APP_ENV':'local', 'AI_MODE':'demo',
        'MAIL_MODE':'local', 'BASE_URL':'http://localhost:5000'})

@pytest.fixture
def client(app):
    return app.test_client()

def post(client, path, data):
    csrf=client.get('/api/config').json['csrf']
    return client.post(path,json=data,headers={'X-CSRF-Token':csrf})

def login(client, email='reviewer@example.com'):
    assert post(client,'/api/auth/request',{'email':email}).status_code==200
    mail=client.get('/api/inbox').json['messages'][0]
    token=parse_qs(urlsplit(mail['action_url']).query)['token'][0]
    assert post(client,'/api/auth/local-confirm',{'token':token}).status_code==200
    return token
