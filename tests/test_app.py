from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, parse_qs
from concurrent.futures import ThreadPoolExecutor
import pytest
from bridge.analysis import SAMPLES, sample_result, validate_result, AnalysisError
from bridge.db import get_db
from bridge.dates import parse_local
from bridge.reminders import deliver_due
from bridge.mail import MailError
from conftest import post, login

def task_payload(language='en'):
    now=datetime.now(timezone.utc)
    return {'title':'Submit the confirmed form','language':language,'timezone':'UTC',
            'due_local':(now+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'remind_local':(now+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'source_title':'Test message','confirmed':True}

@pytest.mark.parametrize('key',list(SAMPLES))
@pytest.mark.parametrize('language',['en','zh','ja','es'])
def test_all_offline_translations_have_exact_evidence(key,language):
    text='\n'.join(SAMPLES[key]['source'])
    result=validate_result(sample_result(key,language),text)
    assert result['summary'] and result['actions']

def test_demo_does_not_fake_custom_ai(client):
    response=post(client,'/api/analyze',{'text':'This is a new message, not a sample.','language':'en'})
    assert response.status_code==422
    assert 'Offline' in response.json['error']

def test_csrf_and_auth_required(client):
    client.get('/api/config')
    assert client.post('/api/tasks',json=task_payload()).status_code==403
    assert post(client,'/api/tasks',task_payload()).status_code==401

def test_login_expiry_and_single_use(app,client):
    token=login(client)
    assert post(client,'/api/auth/local-confirm',{'token':token}).status_code==400
    post(client,'/api/auth/request',{'email':'next@example.com'})
    mail=client.get('/api/inbox').json['messages'][0]
    token=parse_qs(urlsplit(mail['action_url']).query)['token'][0]
    with app.app_context():
        with get_db() as db:
            db.execute('UPDATE login_tokens SET expires_at=0')
    assert post(client,'/api/auth/local-confirm',{'token':token}).status_code==400

def test_link_get_does_not_consume(app,client):
    post(client,'/api/auth/request',{'email':'scanner@example.com'})
    url=client.get('/api/inbox').json['messages'][0]['action_url']
    assert client.get(urlsplit(url).path+'?'+urlsplit(url).query).status_code==200
    token=parse_qs(urlsplit(url).query)['token'][0]
    assert post(client,'/api/auth/local-confirm',{'token':token}).status_code==200

def test_reminder_once_localized_and_persistent(app,client):
    login(client)
    assert post(client,'/api/tasks',task_payload('ja')).status_code==201
    task=client.get('/api/tasks').json['tasks'][0]
    with app.app_context():
        assert deliver_due(task['remind_at']-1)['sent']==0
        assert deliver_due(task['remind_at'])['sent']==1
        assert deliver_due(task['remind_at']+60)['sent']==0
    mails=client.get('/api/inbox').json['messages']
    assert len(mails)==2 and 'リマインダー' in mails[0]['subject']
    assert client.get('/api/tasks').json['tasks'][0]['reminder_status']=='sent'

def test_done_prevents_pending_email_and_other_users_cannot_change(app,client):
    login(client)
    task_id=post(client,'/api/tasks',task_payload()).json['id']
    task=client.get('/api/tasks').json['tasks'][0]
    outsider=app.test_client();login(outsider,'other@example.com')
    assert outsider.get('/api/tasks').json['tasks']==[]
    assert post(outsider,f'/api/tasks/{task_id}/complete',{'confirmed':True}).status_code==404
    assert len(outsider.get('/api/inbox').json['messages'])==1
    assert post(client,f'/api/tasks/{task_id}/complete',{'confirmed':True}).status_code==200
    with app.app_context():
        assert deliver_due(task['remind_at']+1)['sent']==0
    assert client.get('/api/tasks').json['tasks'][0]['reminder_status']=='canceled'

def test_parallel_workers_do_not_duplicate(app,client):
    login(client);post(client,'/api/tasks',task_payload())
    when=client.get('/api/tasks').json['tasks'][0]['remind_at']
    def tick():
        with app.app_context():
            return deliver_due(when)['sent']
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _:tick(),range(2)))==1

def test_invalid_deadlines_and_confirmation(client):
    login(client)
    p=task_payload();p['confirmed']=False
    assert post(client,'/api/tasks',p).status_code==400
    p=task_payload();p['remind_local']=p['due_local']
    assert post(client,'/api/tasks',p).status_code==400
    p=task_payload();p['timezone']='Not/AZone'
    assert post(client,'/api/tasks',p).status_code==400

def test_dst_and_international_time():
    assert parse_local('2026-10-09T17:00','America/Chicago')==parse_local('2026-10-09T22:00','UTC')
    assert parse_local('2026-10-15T17:00','Asia/Shanghai')==parse_local('2026-10-15T09:00','UTC')
    with pytest.raises(ValueError):parse_local('2026-11-01T01:30','America/Chicago')
    with pytest.raises(ValueError):parse_local('2026-03-08T02:30','America/Chicago')

def test_invalid_quote_is_rejected():
    result=sample_result('tech','en');result['actions'][0]['source_quote']='Invented evidence'
    with pytest.raises(AnalysisError):validate_result(result,'\n'.join(SAMPLES['tech']['source']))

def test_retry_is_bounded_and_keeps_idempotency_key(app,client,monkeypatch):
    login(client);post(client,'/api/tasks',task_payload())
    task=client.get('/api/tasks').json['tasks'][0];keys=[]
    def fail(*args,**kwargs):
        keys.append(kwargs['key']);raise MailError('Simulated provider outage')
    monkeypatch.setattr('bridge.reminders.send_mail',fail)
    with app.app_context():
        for _ in range(5):
            row=get_db().execute('SELECT * FROM reminders').fetchone()
            deliver_due(row['next_attempt'])
        assert get_db().execute('SELECT status FROM reminders').fetchone()['status']=='failed'
    assert len(set(keys))==1

def test_live_adapter_contract_without_network(app,client,monkeypatch):
    app.config.update(AI_MODE='openai',OPENAI_API_KEY='mock-only')
    new_text='Please send your project notes by Friday.'
    result={'source_language':'English', 'summary':'Envía tus notas del proyecto antes del viernes.',
            'actions':[{'title':'Enviar las notas del proyecto','source_quote':new_text,
                        'conditions':'','steps': [], 'location': None, 'deadline_text':'Antes del viernes'}],
            'missing_information':['No se indica la fecha exacta, la hora ni la zona horaria.'],
            'words':[]}
    import json
    class Response:
        status_code=200
        def raise_for_status(self):pass
        def json(self):return {'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}
    def fake_post(url,**kwargs):
        assert url=='https://api.openai.com/v1/responses'
        assert kwargs['json']['store'] is False
        assert kwargs['json']['text']['format']['strict'] is True
        assert json.loads(kwargs['json']['input'])['input_language_hint']=='English'
        return Response()
    monkeypatch.setattr('bridge.analysis.requests.post',fake_post)
    data={'text':new_text,'language':'es','input_language':'en','consent':True}
    assert post(client,'/api/analyze',data).json['result']['summary']==result['summary']
    data['consent']=False
    assert post(client,'/api/analyze',data).status_code==400

def test_production_disables_local_tools(app,client):
    app.config.update(APP_ENV='production',MAIL_MODE='gmail')
    assert client.get('/api/inbox').status_code==404
    assert post(client,'/api/auth/local-confirm',{'token':'x'}).status_code==404

def test_input_language_is_separate_from_output(client):
    data={'text':'\n'.join(SAMPLES['tech']['source']),'language':'es','input_language':'zh'}
    response=post(client,'/api/analyze',data)
    assert response.status_code==200
    assert response.json['result']['source_language']=='Simplified Chinese'
    assert 'Completa' in response.json['result']['summary']
    data['input_language']='ja'
    assert post(client,'/api/analyze',data).status_code==422
    data['input_language']='auto'
    assert post(client,'/api/analyze',data).status_code==200

def test_invalid_input_language_is_rejected(client):
    response=post(client,'/api/analyze',{'text':'\n'.join(SAMPLES['tech']['source']),
                                      'language':'en','input_language':['zh']})
    assert response.status_code==422
