import json
import json
import re
import secrets
from urllib.parse import urlencode
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session
from .analysis import AnalysisError, LANGUAGES, SAMPLES, analyze
from .dates import parse_local
from .db import get_db
from .mail import MailError, reminder_copy, send_mail
from .security import clock, csrf_token, digest, rate_limit, user_required

bp = Blueprint('main', __name__)

def body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        abort(400, description='Expected a JSON object.')
    return value

def string(data, field, maximum=1000):
    value = data.get(field)
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:
        abort(400, description='Invalid '+field+'.')
    return value.strip()

@bp.get('/')
def index():
    return render_template('index.html', csrf=csrf_token())

@bp.get('/health')
def health():
    return {'status':'ok'}

@bp.get('/api/config')
def config():
    user = get_db().execute('SELECT email FROM users WHERE id=?', (session.get('user_id'),)).fetchone()
    return {'csrf':csrf_token(), 'ai_mode':current_app.config['AI_MODE'], 'mail_mode':current_app.config['MAIL_MODE'],
            'user':user['email'] if user else None, 'server_time':clock()}

@bp.get('/api/samples')
def samples():
    return {'samples':[{'id':k,'title':d['title'],'language':d['lang'],'text':'\n'.join(d['source'])} for k,d in SAMPLES.items()]}

@bp.post('/api/analyze')
def explanation():
    rate_limit('analysis',20)
    data = body()
    if current_app.config['AI_MODE']!='demo' and data.get('consent') is not True:
        abort(400, description='Confirm that you agree to send this text to the AI service.')
    try:
        result = analyze(data.get('text'),data.get('language'),data.get('input_language','auto'))
        return {'result':result,'mode':current_app.config['AI_MODE']}
    except AnalysisError as exc:
        abort(422, description=str(exc))

@bp.post('/api/auth/request')
def request_link():
    rate_limit('login',6)
    email = string(body(),'email',254).lower()
    if not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+",email):
        abort(400, description='Enter a valid email address.')
    rate_limit('login-address',3,600,identity=email)
    token = secrets.token_urlsafe(32)
    db, now = get_db(), clock()
    with db:
        db.execute('DELETE FROM login_tokens WHERE expires_at<? OR used=1', (now,))
        db.execute('INSERT INTO login_tokens(digest,email,expires_at) VALUES(?,?,?)', (digest(token),email,now+900))
        link = current_app.config['BASE_URL']+'/auth/confirm?'+urlencode({'token':token})
        try:
            send_mail(db, recipient=email, subject='Sign in to BRIDGE',
                      body='Open the link and confirm sign-in. It expires in 15 minutes and can be used once. If you did not request this, ignore it.',
                      action_url=link, kind='login', key='login-'+digest(token), scope=session['dev_scope'])
        except MailError as exc:
            db.execute('DELETE FROM login_tokens WHERE digest=?', (digest(token),))
            abort(502, description=str(exc))
    return {'message':'Open the sign-in email in your local inbox.' if current_app.config['MAIL_MODE']=='local' else 'Check your email for a sign-in link.'}

def consume_token(token):
    if not isinstance(token,str) or len(token)>200:
        abort(400, description='Invalid sign-in link.')
    db, now = get_db(), clock()
    with db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM login_tokens WHERE digest=?', (digest(token),)).fetchone()
        if not row or row['used'] or row['expires_at']<=now:
            abort(400, description='This sign-in link expired or was already used. Request another.')
        db.execute('UPDATE login_tokens SET used=1 WHERE digest=?',(digest(token),))
        db.execute('INSERT OR IGNORE INTO users(email,auth_scope,created_at) VALUES(?,?,?)',
                   (row['email'],secrets.token_urlsafe(24),now))
        user = db.execute('SELECT * FROM users WHERE email=?',(row['email'],)).fetchone()
    dev_scope = session.get('dev_scope')
    session.clear()
    session['dev_scope'] = dev_scope or secrets.token_urlsafe(24)
    session['user_id'] = user['id']
    session.permanent = True
    csrf_token()

@bp.route('/auth/confirm', methods=['GET','POST'])
def confirm():
    # GET does not consume the link: email scanners cannot sign in a user.
    if request.method=='POST':
        consume_token(request.form.get('token',''))
        return redirect('/#tasks')
    token = request.args.get('token','')
    if len(token)>200:
        abort(400)
    return render_template('confirm.html',token=token,csrf=csrf_token())

@bp.post('/api/auth/local-confirm')
def local_confirm():
    if current_app.config['MAIL_MODE']!='local' or current_app.config['APP_ENV']!='local':
        abort(404)
    token = string(body(),'token',200)
    consume_token(token)
    return {'csrf':csrf_token()}

@bp.post('/api/auth/logout')
def logout():
    session.clear()
    return {'message':'Signed out.'}

@bp.get('/api/tasks')
@user_required
def task_list():
    rows = get_db().execute('SELECT t.*,r.remind_at,r.status reminder_status,r.last_error '
                            'FROM tasks t JOIN reminders r ON r.task_id=t.id '
                            'WHERE t.user_id=? ORDER BY t.created_at DESC', (session['user_id'],)).fetchall()
    return {'tasks':[dict(dict(r), details=json.loads(r['details'])) for r in rows], 'server_time':clock()}

@bp.post('/api/tasks')
@user_required
def create_task():
    rate_limit('tasks',30)
    data=body()
    if data.get('confirmed') is not True:
        abort(400, description='Confirm the task and deadline before saving.')
    title=string(data,'title',600)
    language=string(data,'language',5)
    if language not in LANGUAGES:
        abort(400, description='Unsupported language.')
    zone=string(data,'timezone',100)
    try:
        due=parse_local(string(data,'due_local',30),zone)
        remind=parse_local(string(data,'remind_local',30),zone)
    except ValueError as exc:
        abort(400, description=str(exc))
    if not clock()<remind<due:
        abort(400, description='Reminder must be in the future and before the deadline.')
    if due>clock()+2*366*86400:
        abort(400, description='Choose a deadline within the next two years.')
    details=data.get('details', {})
    if not isinstance(details,dict) or set(details)-{'steps','location','deadline_text','conditions'}:
        abort(400, description='Invalid task details.')
    steps=details.get('steps',[])
    if not isinstance(steps,list) or len(steps)>12 or any(not isinstance(x,str) or not x.strip() or len(x)>600 for x in steps):
        abort(400, description='Invalid task checklist.')
    details={'steps':steps, **{k:('' if details.get(k) is None else details[k]) for k in ('location','deadline_text','conditions')}}
    if any(not isinstance(details[k],str) or len(details[k])>1200 for k in ('location','deadline_text','conditions')):
        abort(400, description='Invalid task details.')
    source_title=string(data,'source_title',180)
    task_id,reminder_id=secrets.token_hex(12),secrets.token_hex(12)
    subject,text=reminder_copy(title,due,zone,language)
    extra=[details[k] for k in ('deadline_text','location','conditions') if details[k]]
    extra.extend('- '+step for step in steps)
    if extra:
        text += '\n\n'+'\n'.join(extra)
    link=current_app.config['BASE_URL']+'/#task='+task_id
    db=get_db()
    with db:
        db.execute('INSERT INTO tasks(id,user_id,title,language,due_at,timezone,source_title,provenance,created_at,details) '
                   'VALUES(?,?,?,?,?,?,?,?,?,?)',
                   (task_id,session['user_id'],title,language,due,zone,source_title,'Deadline entered and confirmed by user',clock(),json.dumps(details,ensure_ascii=False)))
        db.execute('INSERT INTO reminders(id,task_id,remind_at,next_attempt,subject,body,action_url) VALUES(?,?,?,?,?,?,?)',
                   (reminder_id,task_id,remind,remind,subject,text,link))
    return {'id':task_id},201

@bp.post('/api/tasks/<task_id>/complete')
@user_required
def complete(task_id):
    if body().get('confirmed') is not True:
        abort(400, description='Confirm that you completed the instruction.')
    db=get_db()
    with db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM tasks WHERE id=? AND user_id=?',(task_id,session['user_id'])).fetchone()
        if not row:
            abort(404)
        db.execute("UPDATE tasks SET status='done',completed_at=COALESCE(completed_at,?) WHERE id=?",(clock(),task_id))
        db.execute("UPDATE reminders SET status='canceled' WHERE task_id=? AND status='pending'",(task_id,))
    return {'status':'done'}

@bp.delete('/api/tasks/<task_id>')
@user_required
def delete_task(task_id):
    db=get_db()
    with db:
        changed=db.execute('DELETE FROM tasks WHERE id=? AND user_id=?',(task_id,session['user_id'])).rowcount
    if not changed:
        abort(404)
    return {'deleted':True}

@bp.get('/api/inbox')
def inbox():
    if current_app.config['MAIL_MODE']!='local' or current_app.config['APP_ENV']!='local':
        abort(404)
    scopes=[session['dev_scope']]
    if session.get('user_id'):
        row=get_db().execute('SELECT auth_scope FROM users WHERE id=?',(session['user_id'],)).fetchone()
        if row:
            scopes.append(row['auth_scope'])
    marks=','.join('?' for _ in scopes)
    rows=get_db().execute(f'SELECT * FROM local_messages WHERE scope IN ({marks}) ORDER BY id DESC LIMIT 50',scopes).fetchall()
    return {'messages':[dict(r) for r in rows]}

@bp.post('/api/local/run-reminders')
@user_required
def run_local():
    if current_app.config['MAIL_MODE']!='local' or current_app.config['APP_ENV']!='local':
        abort(404)
    # Does not fast-forward: sends only reminders actually due for this user.
    from .reminders import deliver_due
    return deliver_due(user_id=session['user_id'])
