import copy
import sqlite3
import pytest
from bridge import create_app
from bridge.analysis import validate_result, AnalysisError
from bridge.db import get_db, init_db
from bridge.reminders import deliver_due
from conftest import login, post
from test_app import task_payload

SOURCE='请在10月5日下午2点到3点在计算机实验室测试注册：创建账户、验证邮件、登录并更新状态。'
def grouped():
    return {'source_language':'Chinese','summary':'Test registration in the computer lab.',
      'actions':[{'title':'Test registration','source_quote':SOURCE,'conditions':'None',
       'deadline_text':'October 5, 2–3 p.m.','location':'Computer lab',
       'steps':['Create an account.','Verify the email.','Log in and update status.']}],
      'missing_information':['None'],'words':[]}

def test_grouped_output_and_empty_conditions():
    r=validate_result(grouped(),SOURCE,'en')
    assert len(r['actions'])==1 and len(r['actions'][0]['steps'])==3
    assert r['actions'][0]['conditions']=='' and r['missing_information']==[]

def test_untranslated_deadline_not_silently_displayed():
    r=grouped();r['actions'][0]['deadline_text']='规定时间内'
    with pytest.raises(AnalysisError,match='not translated'):validate_result(r,SOURCE,'en')

def test_grouped_source_must_be_exact():
    r=grouped();r['actions'][0]['source_quote']='invented'
    with pytest.raises(AnalysisError,match='exact source'):validate_result(r,SOURCE,'en')

def test_independent_tasks_remain_separate():
    r=grouped();r['actions'].append(copy.deepcopy(r['actions'][0]))
    r['actions'][1]['title']='A separate required outcome'
    assert len(validate_result(r,SOURCE,'en')['actions'])==2

def test_details_persist_in_single_task_and_reminder(app,client):
    login(client)
    details={k:v for k,v in validate_result(grouped(),SOURCE,'en')['actions'][0].items() if k in ('steps','location','deadline_text','conditions')}
    p=task_payload();p['details']=details
    assert post(client,'/api/tasks',p).status_code==201
    task=client.get('/api/tasks').json['tasks'][0]
    assert task['details']==details
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM reminders').fetchone()[0]==1
        assert deliver_due(task['remind_at'])['sent']==1
        body=get_db().execute('SELECT body FROM reminders').fetchone()[0]
        assert 'Verify the email.' in body and 'Computer lab' in body

@pytest.mark.parametrize('details',[{'steps':'wrong'},{'steps':[1]},{'location':['lab']},{'unknown':'x'}])
def test_invalid_details_rejected(client,details):
    login(client);p=task_payload();p['details']=details
    assert post(client,'/api/tasks',p).status_code==400

def test_old_database_migrates_without_losing_task(tmp_path):
    from pathlib import Path
    path=tmp_path/'old.sqlite'
    schema=Path('bridge/schema.sql').read_text().replace(" details TEXT NOT NULL DEFAULT '{}',",'')
    with sqlite3.connect(path) as db:
        db.executescript(schema)
        db.execute("INSERT INTO users VALUES(1,'test@example.com','scope',0)")
        db.execute("INSERT INTO tasks VALUES('old',1,'Old task','en',100,'UTC','Document','Reviewed','pending',0,NULL)")
    app=create_app({'TESTING':True,'APP_ENV':'local','MAIL_MODE':'local','AI_MODE':'demo','SECRET_KEY':'test','BASE_URL':'http://localhost:5000','DATABASE':str(path)})
    with app.app_context():
        init_db()
        row=get_db().execute('SELECT title,details FROM tasks').fetchone()
        assert row['title']=='Old task' and row['details']=='{}'
