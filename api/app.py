from flask import Flask, request, jsonify, session, redirect, render_template_string
from flask_cors import CORS
import os, json
import psycopg
from psycopg.rows import dict_row
app=Flask(__name__); app.secret_key=os.environ.get('SESSION_SECRET','change-this'); CORS(app, supports_credentials=True)
DEFAULT={"carpet":[["Living room",79],["Bedroom",37],["Dining room",57],["Stairs and landing",75],["Rug",35]],"upholstery":[["Armchair",30],["2-seat sofa",80],["3-seat sofa",120],["Dining chair",15]],"commercial":[["Small area — up to 150m²",375],["Medium area — 151–300m²",780],["Large area — 301–500m²",1200],["Hotel room — rotary clean",25],["Hotel room — hybrid deep clean",30],["Hotel room — hot water extraction",35]],"specialist":[["Mattress",55],["Curtains",45],["Odour treatment",35],["Stain treatment",30]]}
def db(): return psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row)
def setup():
 with db() as c:
  c.execute('create table if not exists calculator_settings (id int primary key default 1, pricing jsonb not null)')
  c.execute('create table if not exists calculator_enquiries (id bigserial primary key, created_at timestamptz default now(), customer jsonb not null)')
  c.execute('insert into calculator_settings(id,pricing) values(1,%s) on conflict(id) do nothing',(json.dumps(DEFAULT),))
def prices():
 setup()
 with db() as c: return c.execute('select pricing from calculator_settings where id=1').fetchone()['pricing']
def owner(): return bool(session.get('owner'))
@app.get('/api/pricing')
def get_pricing(): return jsonify(prices())
@app.post('/api/enquiries')
def enquiry():
 data=request.get_json(force=True)
 setup()
 with db() as c: c.execute('insert into calculator_enquiries(customer) values(%s)',(json.dumps(data),))
 return jsonify({'ok':True})
@app.route('/admin',methods=['GET','POST'])
def admin():
 if request.method=='POST':
  if request.form.get('password')==os.environ.get('ADMIN_PASSWORD'):
   session['owner']=True; return redirect('/admin')
  return 'Incorrect password',401
 if not owner(): return '''<style>body{font-family:Arial;background:#eef4f7;padding:8vw}.card{max-width:420px;margin:auto;background:#fff;padding:32px;border-radius:18px}</style><div class=card><h1>The Carpet Cleaning Company</h1><p>Owner settings</p><form method=post><input name=password type=password placeholder="Password" required><button>Sign in</button></form></div>'''
 return render_template_string('''<style>body{font-family:Arial;background:#eef4f7;padding:30px;color:#123}main{max-width:950px;margin:auto;background:white;padding:28px;border-radius:18px}textarea{width:100%;height:430px;font-family:monospace}button{padding:12px 16px;background:#0b2d4a;color:white;border:0;border-radius:8px;font-weight:bold}</style><main><h1>Calculator settings</h1><p>Edit the service groups and prices below. Changes apply to every customer immediately.</p><textarea id=p>{{ data|tojson(indent=2) }}</textarea><p><button onclick="save()">Save changes</button> <span id=m></span></p></main><script>async function save(){let r=await fetch('/admin/pricing',{method:'POST',headers:{'Content-Type':'application/json'},body:p.value});m.textContent=r.ok?'Saved for every customer.':'Could not save.'}</script>''',data=prices())
@app.post('/admin/pricing')
def save_pricing():
 if not owner(): return 'Unauthorised',401
 data=request.get_json(force=True)
 with db() as c: c.execute('update calculator_settings set pricing=%s where id=1',(json.dumps(data),))
 return jsonify({'ok':True})
@app.get('/health')
def health(): return {'ok':True}
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',10000)))
