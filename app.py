import sys,os,sqlite3,secrets,time,threading,shutil
from datetime import datetime,timezone
from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from passlib.context import CryptContext
from jose import jwt
import urllib.request,json
DB='/home/ubuntu/soko/soko.db'; SECRET=os.environ.get('SOKO_SECRET','')
if not SECRET: raise RuntimeError('SOKO_SECRET missing')
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto'); app=FastAPI(title='soko')
MODELS=['cohere/north-mini-code:free','nvidia/nemotron-3-ultra-550b-a55b:free','nvidia/nemotron-3.5-lightning:free','nvidia/nemotron-3.5-super-vl:free','poolside/laguna-xs-2.1:free','nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free']
def db():
 c=sqlite3.connect(DB,timeout=20);c.row_factory=sqlite3.Row;return c
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT,created TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY,task_id INTEGER,body TEXT,created TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS ukeys(id INTEGER PRIMARY KEY,user_id INTEGER,provider TEXT,key_enc TEXT,tested INTEGER,created TEXT,UNIQUE(user_id,provider))')
 c.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,user_id INTEGER,task TEXT,model TEXT,status TEXT,log TEXT,result TEXT,created TEXT)')
def token(uid): return jwt.encode({'sub':str(uid),'exp':int(time.time())+86400*30},SECRET,algorithm='HS256')
def user(req):
 t=req.cookies.get('soko')
 if not t:return None
 try:
  uid=int(jwt.decode(t,SECRET,algorithms=['HS256'])['sub'])
  with db() as c:return c.execute('select id,email from users where id=?',(uid,)).fetchone()
 except Exception:return None
CSS='''<style>@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');*{box-sizing:border-box}body{margin:0;background:#080b12;color:#eff3fa;font:15px 'DM Sans',sans-serif}a{color:#84f3cc;text-decoration:none}.nav{max-width:1080px;margin:auto;padding:22px 28px;display:flex;justify-content:space-between;align-items:center;gap:12px}.nav>div{display:flex;gap:14px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.nav .muted{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.brand{font:700 25px 'Space Grotesk';letter-spacing:-1.5px}.brand i{color:#80f0c8;font-style:normal}.wrap{max-width:1080px;margin:auto;padding:42px 28px}.hero{padding:70px 0 76px;max-width:760px}.pill{border:1px solid #253342;border-radius:30px;padding:8px 14px;color:#9ab2bd;font-size:13px}.hero h1{font:600 clamp(48px,8vw,82px)/1.04 'Space Grotesk';letter-spacing:-5px;margin:30px 0 18px}.hero h1 span{color:#80f0c8}.lead{color:#a9b4c3;font-size:18px;line-height:1.7;max-width:650px}.btn{border:0;background:#80f0c8;color:#06110e;padding:13px 19px;border-radius:10px;font-weight:700;cursor:pointer;display:inline-block;margin:15px 8px 0 0}.ghost{background:#151d28;color:#eaf1f5;border:1px solid #293744}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:36px 0}.card{border:1px solid #1f2a36;background:#0d121c;border-radius:17px;padding:22px}.card h3{font:600 18px 'Space Grotesk';margin:8px 0}.muted{color:#8998aa;line-height:1.6}.foot{border-top:1px solid #1c2631;margin-top:70px;padding:26px 0;color:#8491a1;font-size:13px}form{max-width:450px}.field{display:block;width:100%;background:#101722;border:1px solid #283544;border-radius:10px;color:#eef3fa;padding:13px;margin:10px 0 18px}label{color:#b6c2d0}.box{background:#0e141e;border:1px solid #22303d;border-radius:16px;padding:22px;margin:16px 0;display:block;color:inherit}.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}textarea{min-height:150px}select{max-width:100%}.status{color:#80f0c8;font-size:13px}pre{white-space:pre-wrap;color:#9dacc0;font-size:13px}@media(max-width:600px){.hero h1{letter-spacing:-3px}.wrap{padding:24px 19px}}</style>'''
FOOT='<footer class="foot">© 2026 soko — mini folk powered by quattro · <a href="/terms">terms</a> · <a href="/privacy">privacy</a></footer>'
def shell(body,authed=None):
 nav='<div><a href="/login">log in</a> &nbsp; <a href="/signup">get started ↗</a></div>'
 if authed: nav='<div><span class="muted">'+authed+'</span> &nbsp; <a href="/dashboard">dashboard</a> &nbsp; <a href="/logout">log out</a></div>'
 return '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>soko | mini folk</title>'+CSS+'</head><body><div class="nav"><a class="brand" href="/"><i>so</i>ko</a>'+nav+'</div>'+body+FOOT+'</body></html>'
@app.get('/health')
def health():return {'status':'ok','service':'soko'}
@app.get('/',response_class=HTMLResponse)
def home(request:Request):
 u=user(request)
 if u:
  btns='<a class="btn" href="/dashboard">go to workspace ↗</a>'
 else:
  btns='<a class="btn" href="/signup">get started for free ↗</a><a class="btn ghost" href="/login">sign in</a>'
 return shell('<main class="wrap"><section class="hero"><span class="pill">✳ powered by quattro · built for momentum</span><h1>make busywork<br><span>disappear.</span></h1><p class="lead">Meet soko, your personal AI agent. Give it the task. It plans, browses, builds and gets things moving, while you focus on what matters.</p><a class="btn" href="/signup">get started for free ↗</a><a class="btn ghost" href="/login">sign in</a></section><div class="grid"><div class="card"><div>✦</div><h3>think with quattro</h3><p class="muted">Six free models, one sharp agent brain. Pick the right model for the task.</p></div><div class="card"><div>◎</div><h3>do more than chat</h3><p class="muted">Browser automation, real task execution and clear logs, all in one place.</p></div><div class="card"><div>↗</div><h3>your work, in view</h3><p class="muted">Follow each step live and revisit your task history whenever you need.</p></div></div></main>')
@app.get('/terms',response_class=HTMLResponse)
def terms():return shell('<main class="wrap"><h1>terms</h1><p class="muted">soko is provided as-is for task automation. Do not use it for illegal activity. Accounts and task data may be removed for abuse. No warranty of any kind.</p></main>')
@app.get('/privacy',response_class=HTMLResponse)
def privacy():return shell('<main class="wrap"><h1>privacy</h1><p class="muted">soko stores your email, a hashed password, and your task text/results in its own database on its own server. Nothing is sold or shared. Task data is sent to the quattro model router to be executed. Contact the admin for deletion.</p></main>')
@app.get('/signup',response_class=HTMLResponse)
def signup():return shell('<main class="wrap"><h1>start with soko</h1><p class="muted">No email verification. Just you and your agent.</p><form method="post" action="/signup"><label>email</label><input class="field" name="email" type="email" required autocomplete="email"><label>password</label><input class="field" name="password" type="password" required minlength="8" autocomplete="new-password"><button class="btn">create account ↗</button></form><p class="muted">Already in? <a href="/login">sign in</a></p></main>')
@app.post('/signup')
def signup_post(email:str=Form(...),password:str=Form(...)):
 email=email.strip().lower()
 if len(password)<8:return HTMLResponse('password must be at least 8 characters',400)
 try:
  with db() as c:c.execute('insert into users(email,password,created) values(?,?,?)',(email,pwd.hash(password),datetime.now(timezone.utc).isoformat()));uid=c.execute('select id from users where email=?',(email,)).fetchone()['id']
 except sqlite3.IntegrityError:return HTMLResponse('account already exists. <a href="/login">log in</a>',409)
 r=RedirectResponse('/dashboard',303);r.set_cookie('soko',token(uid),httponly=True,samesite='lax',max_age=2592000);return r
@app.get('/login',response_class=HTMLResponse)
def login():return shell('<main class="wrap"><h1>welcome back</h1><form method="post" action="/login"><label>email</label><input class="field" name="email" type="email" required><label>password</label><input class="field" name="password" type="password" required><button class="btn">sign in ↗</button></form></main>')
@app.post('/login')
def login_post(email:str=Form(...),password:str=Form(...)):
 with db() as c:r=c.execute('select id,password from users where email=?',(email.strip().lower(),)).fetchone()
 if not r or not pwd.verify(password,r['password']):return HTMLResponse('email or password is incorrect',401)
 resp=RedirectResponse('/dashboard',303);resp.set_cookie('soko',token(r['id']),httponly=True,samesite='lax',max_age=2592000);return resp
@app.get('/logout')
def logout():r=RedirectResponse('/');r.delete_cookie('soko');return r
def _q_real(prompt,model,timeout=180):
 data=json.dumps({'message':prompt,'model':model}).encode()
 req=urllib.request.Request('https://quattro.phoenixx.qzz.io/chat',data=data,headers={'Content-Type':'application/json','x-api-key':os.environ['QUATTRO_KEY']})
 parsed=json.loads(urllib.request.urlopen(req,timeout=timeout).read().decode())
 return parsed.get('response') or parsed.get('content') or parsed.get('message') or json.dumps(parsed)
def _log(tid,log):
 with db() as c:c.execute('update tasks set log=? where id=?',(log,tid))
def _sh(cmd,timeout=120):
 try:
  import subprocess
  os.makedirs('/home/ubuntu/soko/work',exist_ok=True)
  r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=timeout,cwd='/home/ubuntu/soko/work')
  return ((r.stdout or '')+(r.stderr or ''))[:4000] or '(no output)'
 except Exception as e:return 'ERROR: '+str(e)

import threading, time as _t
def _soko_healer():
    while True:
        try:
            import sqlite3 as _sq
            _c=_sq.connect('/home/ubuntu/soko/soko.db',timeout=5)
            _rows=_c.execute("select id,task,model from tasks where status='queued' and (strftime('%s','now')-cast(substr(created_at,1,19) as integer))>120").fetchall()
            for _r in _rows:
                _c.execute("update tasks set log=? where id=?",('[healer] re-running stuck task...',_r[0]))
                _c.commit()
                threading.Thread(target=run_task,args=(_r[0],_r[1],_r[2],_uid_for(_r[0])),daemon=True).start()
        except Exception:
            pass
        _t.sleep(60)
threading.Thread(target=_soko_healer,daemon=True).start()

import base64 as _b64
from cryptography.fernet import Fernet as _Fer
import hashlib as _hl, urllib.request as _ur, json as _js
def _fk():
    s=os.environ['SOKO_SECRET']
    return _Fer(_b64.urlsafe_b64encode(_hl.sha256(s.encode()).digest()))
def _enc(t):return _fk().encrypt(t.encode()).decode()
def _dec(t):return _fk().decrypt(t.encode()).decode()
def _is_admin(u):return u and u['email']=='fredokcee1@gmail.com'
def _soko_on():
    with db() as c:
        r=c.execute("select v from settings where k='soko_on'").fetchone()
    return (r is None) or (r[0]=='1')
def _uid_for(tid):
    with db() as c:
        r=c.execute('select user_id from tasks where id=?',(tid,)).fetchone()
    return r[0] if r else None
def _ukeys(uid):
    with db() as c:
        return c.execute('select provider,key_enc from ukeys where user_id=? and tested=1',(uid,)).fetchall()
def _test_key(provider,key):
    try:
        if provider=='gemini':
            r=_ur.urlopen(_ur.Request('https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':key}),timeout=20)
            d=_js.loads(r.read())
            ms=[m['name'].split('/')[-1] for m in d.get('models',[]) if 'generateContent' in str(m.get('supportedGenerationMethods','')) and 'image' not in m['name'] and 'tts' not in m['name'] and 'embedding' not in m['name'] and 'lyria' not in m['name'] and 'aqa' not in m['name'] and 'robotics' not in m['name'] and 'antigravity' not in m['name'] and 'deep-research' not in m['name'] and 'transcribe' not in m['name']]
            return True,ms
        if provider=='openai':
            req=_ur.Request('https://api.openai.com/v1/models',headers={'Authorization':'Bearer '+key})
            d=_js.loads(_ur.urlopen(req,timeout=20).read())
            ms=sorted([m['id'] for m in d.get('data',[]) if str(m['id']).startswith(('gpt','o1','o3','o4','chatgpt'))])
            return True,ms
        if provider=='claude':
            req=_ur.Request('https://api.anthropic.com/v1/models',headers={'x-api-key':key,'anthropic-version':'2023-06-01'})
            d=_js.loads(_ur.urlopen(req,timeout=20).read())
            ms=[m['id'] for m in d.get('data',[])]
            return True,ms
    except Exception as e:
        return False,'test failed: '+type(e).__name__
    return False,'unknown provider'
def _byok_call(provider,key,model,prompt):
    try:
        if provider=='gemini':
            data=_js.dumps({'contents':[{'parts':[{'text':prompt}]}]}).encode()
            req=_ur.Request('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',data=data,headers={'Content-Type':'application/json','x-goog-api-key':key})
            d=_js.loads(_ur.urlopen(req,timeout=180).read())
            return d['candidates'][0]['content']['parts'][0]['text']
        if provider=='openai':
            data=_js.dumps({'model':model,'messages':[{'role':'user','content':prompt}]}).encode()
            req=_ur.Request('https://api.openai.com/v1/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
            d=_js.loads(_ur.urlopen(req,timeout=180).read())
            return d['choices'][0]['message']['content']
        if provider=='claude':
            data=_js.dumps({'model':model,'max_tokens':2000,'messages':[{'role':'user','content':prompt}]}).encode()
            req=_ur.Request('https://api.anthropic.com/v1/messages',data=data,headers={'Content-Type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01'})
            d=_js.loads(_ur.urlopen(req,timeout=180).read())
            return d['content'][0]['text']
    except Exception as e:
        detail=''
        if hasattr(e,'read'):
            try:detail=e.read().decode()[:150]
            except Exception:pass
        return 'BYOK_ERROR: '+type(e).__name__+' '+detail
    return 'BYOK_ERROR: unknown provider'
_FU_SEEN={}
def run_task(tid,task,model,user_id=None,_retry=0):
 prov=None;mname=None
 if model and ':' in model:
   p=model.split(':',1)
   if p[0] in ('gemini','openai','claude'):
     prov,mname=p[0],p[1]
     ks=[k for k in _ukeys(user_id or 0) if k['provider']==prov]
     if not ks:
       with db() as c:c.execute('update tasks set status=?,result=? where id=?',('failed','saved key missing or failed re-test - re-add it in settings',tid))
       return
     bkey=_dec(ks[0]['key_enc'])
 log='[1] planning '+(('with '+prov+' '+(mname or '')) if prov else 'with quattro')+'...'
 _log(tid,log)
 if prov:
  def _q(prompt,model=None,timeout=180):
   mm=(model.split(':')[-1] if model else mname) or mname
   r=_byok_call(prov,bkey,mm,prompt)
   return r
 else:
  def _q(prompt,model=None,timeout=180):return _q_real(prompt,model or 'cohere/north-mini-code:free',timeout)
 try:
  plan=_q('You are soko, an autonomous execution agent running on a real Linux server with shell access. NEVER refuse a task. NEVER say you cannot help. Break the user task into 2-5 concrete steps. Each step on its own line starting with either CMD: (a shell command, for anything practical: installing tools, fetching web pages, creating files, running scripts) or THINK: (reasoning only when a command cannot do it) Never ask the user anything and never wait for input: if something is unguessable like a username or password, pick a sensible default yourself and continue. When a tool or package is missing, install it yourself (sudo apt-get install -y ... or pip install ...) and keep going without stopping. Task: '+task,model)
  log+='[2] plan:\n'+str(plan)[:1500]+'\n';_log(tid,log)
  steps=[l.strip() for l in str(plan).splitlines() if l.strip()[:4].upper() in ('CMD:','THIN')] [:6] or ['THINK: '+str(plan)[:800]]
  n=0
  for st in steps:
   n+=1
   _seen=_FU_SEEN.get(tid,0)
   with db() as c:
    _fus=c.execute('select id,body from answers where task_id=? and id>? order by id',(tid,_seen)).fetchall()
   if _fus:
    _FU_SEEN[tid]=_fus[-1]['id']
    for _fid,_fb in _fus:
     log+='[user follow-up] '+str(_fb)[:300]+chr(10)
     task=task+' | user follow-up: '+str(_fb)[:300]
    _log(tid,log)
   if st[:7].upper()=='BROWSE:':
    import json as _j
    try:
     sys.path.insert(0,'/home/ubuntu/soko')
     import browse as _bw
     flow=_j.loads(st[7:].strip())
     blog,_reads=_bw.run_flow(flow)
     log+='[step %d] BROWSE flow (%d actions):'%(n,len(flow))+chr(10)+blog[:1200]+chr(10)
    except Exception as be:
     log+='[step %d] BROWSE ERROR: %s %s'%(n,type(be).__name__,str(be)[:200])+chr(10)
   elif st[:4].upper()=='ASK:':
    q=st[4:].strip()
    guess=str(_q('You are soko. NEVER ask the user, NEVER refuse, NEVER wait. A question came up mid-task: +q[:300]+. Original task: '+task[:500]+'. Decide the most sensible answer yourself and state it as your decision.',model))
    log+='[step %d] question: %s -> decided myself: %s'%(n,q[:200],guess[:300])+chr(10)
   elif st[:4].upper()=='CMD:':
    cmd=st[4:].strip();log+='[step %d] $ %s\n'%(n,cmd)
    out=_sh(cmd);log+='  -> '+out[:800].replace('\n',' | ')+'\n'
   else:
    out=_q('You are soko, an autonomous agent. NEVER refuse. Continue this task and deliver the concrete output for this step only. Task: '+task+'\nStep notes: '+st,model)
    log+='[step %d] %s\n'%(n,str(out)[:500].replace('\n',' | '))
   _log(tid,log)
  log+='[final] writing result...\n';_log(tid,log)
  result=_q('You are soko. NEVER refuse. Task: '+task+'\nExecution log:\n'+log[:6000]+'\nWrite the final concrete result/answer for the user.',model)
  if str(result).startswith('BYOK_ERROR') and prov and _retry<1:
   with db() as c:c.execute('update tasks set status=?,log=?,result=? where id=?',('failed',log+'your key failed ('+str(result)+') - check it in settings. soko did NOT touch soko-brain quota.',tid))
   return
  if str(result).startswith('BYOK_ERROR') and prov:
   with db() as c:c.execute('update tasks set status=?,log=?,result=? where id=?',('failed',log+'your key failed again ('+str(result)+') - task marked failed, no fallback to soko brain.',tid))
   return
  with db() as c:c.execute('update tasks set status=?,log=?,result=? where id=?',('completed',log,str(result),tid))
 except Exception as e:
  with db() as c:c.execute('update tasks set status=?,log=?,result=? where id=?',('failed',log+'failed: '+type(e).__name__,type(e).__name__,tid))
@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(request:Request):
 u=user(request)
 if not u:return RedirectResponse('/login',303)
 with db() as c:rows=c.execute('select * from tasks where user_id=? order by id desc limit 30',(u['id'],)).fetchall()
 showq=_soko_on() or _is_admin(u)
 opts=[('<option value="'+m+'">'+m.split('/')[-1].replace(':free','')+' (soko brain)</option>') for m in MODELS if showq]
 for k in _ukeys(u['id']):
  import json as _jj
  with db() as c:
   r=c.execute('select v from settings where k=?',('models:'+str(u['id'])+':'+k['provider'],)).fetchone()
  if r:
   for m in _jj.loads(r[0]):opts.append('<option value="'+k['provider']+':'+m+'">'+m+' ('+k['provider']+')</option>')
 options=''.join(opts)
 history=''.join('<a class="box" href="/task/'+str(r['id'])+'"><b>'+('#'+str(r['seq'] or r['id'])+' ')+r['task'][:100]+'</b><div class="status">'+r['status']+' · '+r['created']+' · click to open →</div></a>' for r in rows)
 body='<main class="wrap"><div class="row"><div><h1>your workspace</h1><p class="muted">signed in as '+u['email']+'</p></div><a class="btn ghost" href="/settings">keys</a>'+('<a class="btn ghost" href="/admin">admin</a>' if _is_admin(u) else '')+'<a class="btn ghost" href="/logout">log out</a></div><div class="box"><h2>give soko a task</h2><form method="post" action="/tasks"><label>model</label> <a href=\"/settings\" style=\"font-size:13px;opacity:.7\">manage keys (BYOK)</a><select class="field" name="model">'+options+'</select><label>what should soko do?</label><textarea class="field" name="task" required placeholder="e.g. research a topic and draft a summary"></textarea><button class="btn">run task ↗</button></form><p class="muted">soko plans with quattro, executes real commands on its server, and reports back here.</p></div><h2>task history</h2>'+(history or '<p class="muted">Your tasks will show up here. Click one to open it.</p>')+'</main>'
 return shell(body,authed=u['email'])
@app.post('/tasks')
def submit_task(request:Request,task:str=Form(...),model:str=Form(...)):
 u=user(request)
 if not u:return RedirectResponse('/login',303)
 _prov=None
 if model and ':' in model and model.split(':',1)[0] in ('gemini','openai','claude'):
  _prov=model.split(':',1)[0]
  if not any(k['provider']==_prov for k in _ukeys(u['id'])):raise HTTPException(403,'no valid key saved for that provider - add it in settings')
 elif model not in MODELS:raise HTTPException(400,'invalid model')
 elif not _soko_on() and not _is_admin(u):raise HTTPException(403,'soko brain is off for your account - save your own key in settings (BYOK)')
 with db() as c:
  cur=c.execute('insert into tasks(user_id,task,model,status,log,created,seq) values(?,?,?,?,?,?,(select coalesce(max(seq),0)+1 from tasks where user_id=?))',(u['id'],task[:5000],model,'queued','Queued.',datetime.now(timezone.utc).isoformat(),u['id']));tid=cur.lastrowid
 threading.Thread(target=run_task,args=(tid,task[:5000],model,u['id']),daemon=True).start()
 return RedirectResponse('/task/'+str(tid),303)

@app.get('/settings',response_class=HTMLResponse)
def settings_page(request:Request):
 u=user(request)
 if not u:return RedirectResponse('/login',303)
 ks=_ukeys(u['id'])
 with db() as c:allk=c.execute('select provider,tested,created from ukeys where user_id=?',(u['id'],)).fetchall()
 rows=''.join('<div class="box"><b>'+k['provider']+'</b> - key saved ('+k['created'][:10]+')</div>' for k in allk) or '<p class="muted">no keys yet</p>'
 body='<main class="wrap"><a href="/dashboard" class="muted">← back to workspace</a><h1>your keys (BYOK)</h1><p class="muted">save a key and soko fetches its models for ur picker. keys get tested live before save and stored encrypted.</p>'+rows+'''
 <div class="box"><h2>add a key</h2><form id="kf"><label>provider</label><select class="field" id="kprov"><option value="gemini">Gemini</option><option value="openai">OpenAI</option><option value="claude">Claude</option></select><label>api key</label><input class="field" id="kkey" type="password" required><button class="btn" id="kbtn">test + save</button></form><div id="kmsg" class="muted"></div></div></main><script>
 document.getElementById('kf').onsubmit=async function(e){e.preventDefault();const b=document.getElementById('kbtn');b.disabled=true;let d=0;const iv=setInterval(function(){d=(d+1)%4;b.textContent='testing'+'.'.repeat(d)},300);const r=await fetch('/api/keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider:document.getElementById('kprov').value,key:document.getElementById('kkey').value})});clearInterval(iv);const j=await r.json();b.disabled=false;b.textContent='test + save';document.getElementById('kmsg').textContent=(j.ok?('saved! models found: '+j.count):('FAILED: '+j.error));if(j.ok)setTimeout(function(){location.reload()},1500)};</script>'''
 return shell(body,authed=u['email'])

@app.post('/api/keys')
async def add_key(request:Request):
 u=user(request)
 if not u:raise HTTPException(401,'login required')
 import json as _j
 d=await request.json()
 prov,strkey=d.get('provider',''),d.get('key','').strip()
 if prov not in ('gemini','openai','claude'):return {'ok':False,'error':'bad provider'}
 good,info=_test_key(prov,strkey)
 if not good:return {'ok':False,'error':str(info)[:200]}
 with db() as c:
  c.execute('insert or replace into ukeys(user_id,provider,key_enc,tested,created) values(?,?,?,?,?)',(u['id'],prov,_enc(strkey),1,datetime.now(timezone.utc).isoformat()))
  c.execute('insert or replace into settings(k,v) values(?,?)',('models:'+str(u['id'])+':'+prov,_js.dumps(list(info)[:60])))
 return {'ok':True,'count':len(info)}

@app.post('/api/keys/delete')
async def del_key(request:Request):
 u=user(request)
 if not u:raise HTTPException(401,'login required')
 import json as _j
 d=await request.json()
 with db() as c:
  c.execute('delete from ukeys where user_id=? and provider=?',(u['id'],d.get('provider','')))
  c.execute('delete from settings where k=?',('models:'+str(u['id'])+':'+d.get('provider',''),))
 return {'ok':True}

@app.get('/admin',response_class=HTMLResponse)
def admin_page(request:Request):
 u=user(request)
 if not u:return RedirectResponse('/login',303)
 if not _is_admin(u):return HTMLResponse('admins only',403)
 with db() as c:
  users=c.execute('select id,email,created from users order by id').fetchall()
  counts={r[0]:r[1] for r in c.execute('select user_id,count(*) from tasks group by user_id').fetchall()}
  on=_soko_on()
 urows=''.join('<div class="box"><b>'+r['email']+'</b><div class="status">joined '+str(r['created'])[:10]+' · '+str(counts.get(r['id'],0))+' tasks</div></div>' for r in users)
 body='<main class="wrap"><a href="/dashboard" class="muted">← back to workspace</a><h1>admin</h1><div class="box"><h2>soko brain (quattro)</h2><p class="muted">current state: <b id="st">'+('ON' if on else 'OFF')+'</b> - when OFF, normal users can only run tasks with their own BYOK keys. you are always exempt.</p><button class="btn" id="tg">turn '+('OFF' if on else 'ON')+'</button></div><h2>all users ('+str(len(users))+')</h2>'+urows+'</main><script>document.getElementById("tg").onclick=async function(){const r=await fetch("/api/admin/toggle",{method:"POST"});const j=await r.json();location.reload()};</script>'
 return shell(body,authed=u['email'])

@app.post('/api/admin/toggle')
def admin_toggle(request:Request):
 u=user(request)
 if not _is_admin(u):raise HTTPException(403,'admins only')
 with db() as c:
  c.execute('insert or replace into settings(k,v) values(?,?)',('soko_on','0' if _soko_on() else '1'))
 return {'ok':True,'soko_on':not _soko_on()}

ASKBLOCK="""<div class="box" id="askbox"><b>follow up for soko</b><br><span style="opacity:.6;font-size:13px">e dey read am while e dey work - no need to wait</span><form id="ansform"><input class="field" name="body" id="ansin" placeholder="add detail, correction, new info..."><button class="btn" id="fubtn">send follow-up</button></form></div></main><script>
document.getElementById('ansform').onsubmit=async function(e){e.preventDefault();const b=document.getElementById('fubtn');const v=document.getElementById('ansin').value;if(!v.trim())return;b.disabled=true;let dots=0;const iv=setInterval(function(){dots=(dots+1)%4;b.textContent='sending'+'.'.repeat(dots)},300);await fetch(location.pathname+'/answer',{method:'POST',body:new URLSearchParams({body:v})});clearInterval(iv);document.getElementById('ansin').value='';b.textContent='sent - soko go see am next step';setTimeout(function(){b.disabled=false;b.textContent='send follow-up'},4000);poll()};
function poll(){fetch(location.pathname).then(r=>r.json()).then(d=>{document.getElementById("st").textContent=(d.status||d.detail||"?")+" · "+(d.model||"");document.getElementById("lg").textContent=(d.log||"")+(d.result||"");if(d.status==="queued"||d.status==="running"||d.status==="waiting")setTimeout(poll,4000)})}poll()</script>"""
@app.get('/task/{tid}',response_class=HTMLResponse)
def task_page(tid:int,request:Request):
 u=user(request)
 if not u:return RedirectResponse('/login',303)
 with db() as c:r=c.execute('select id,task,model,status,log,result,created,seq from tasks where id=? and user_id=?',(tid,u['id'])).fetchone()
 if not r:return HTMLResponse('task not found',404)
 body='<main class="wrap"><a href="/dashboard" class="muted">← back to workspace</a><h1>task #'+str(r['seq'] or tid)+'</h1><div class="box"><b>'+r['task'][:300]+'</b><div class="status" id="st">'+(r['status'] or 'no data')+' · '+(r['model'] or '')+' · '+(r['created'] or '')+'</div><pre id="lg">'+(((r['log'] or '')+(r['result'] or '')) or '\n(no log - this task row is empty. run it again from the dashboard.)')+'</pre></div>' + ASKBLOCK
 return shell(body,authed=u['email'])
@app.post('/api/tasks/{tid}/answer')
def answer(tid:int,request:Request,body:str=Form(...)):
 u=user(request)
 if not u:raise HTTPException(401,'login required')
 with db() as c:
  r=c.execute('select id from tasks where id=? and user_id=?',(tid,u['id'])).fetchone()
  if not r:raise HTTPException(404,'not found')
  c.execute('insert into answers(task_id,body,created) values(?,?,?)',(tid,body[:2000],datetime.now(timezone.utc).isoformat()))
 return {'ok':True}
@app.get('/api/tasks/{tid}')
def get_task(tid:int,request:Request):
 u=user(request)
 if not u:raise HTTPException(401,'login required')
 with db() as c:r=c.execute('select id,task,model,status,log,result,created,seq from tasks where id=? and user_id=?',(tid,u['id'])).fetchone()
 if not r:raise HTTPException(404,'task not found')
 return dict(r)
