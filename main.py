import os
import sqlite3
import secrets
from functools import wraps
from urllib.parse import quote
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, abort
from werkzeug.security import check_password_hash, generate_password_hash

# SADX / Neon Dark Digital Store
# Install: pip install flask
# Run (Windows): set ADMIN_PASSWORD=YourStrongPassword
#                set SECRET_KEY=some-long-random-secret
#                set WHATSAPP_NUMBER=923001234567
#                python app.py

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024
)
DB_PATH = os.environ.get("DATABASE_PATH", "store.db")
WHATSAPP_NUMBER = "".join(c for c in os.environ.get("WHATSAPP_NUMBER", "923001234567") if c.isdigit())
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeThis-Immediately!")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'Scripts',
            description TEXT NOT NULL DEFAULT '', price REAL NOT NULL DEFAULT 0,
            badge TEXT NOT NULL DEFAULT 'DIGITAL', download_url TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER, product_name TEXT NOT NULL,
            customer_name TEXT NOT NULL, customer_contact TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            con.executemany("""INSERT INTO products(name,category,description,price,badge,download_url)
                VALUES(?,?,?,?,?,?)""", [
                ("Neon Portfolio Template", "HTML Templates", "Responsive animated portfolio template. Easy to customize.", 1200, "BESTSELLER", ""),
                ("Flask Starter Kit", "Python Scripts", "A clean starter structure for small Flask projects.", 1800, "NEW", ""),
                ("Uptime Monitor Lite", "Python Scripts", "Lightweight uptime checker with a simple dashboard.", 1500, "POPULAR", "")
            ])

BASE = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} · SADX STORE</title>
<style>
:root{--bg:#080812;--panel:#111122;--panel2:#17172b;--line:#292946;--text:#f4f3ff;--muted:#aaa9c7;--purple:#a855f7;--cyan:#42e8ff;--pink:#ff4fd8;--green:#54f3b1}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 15% 0%,#251044 0,transparent 35%),radial-gradient(ellipse at 90% 20%,#082a3a 0,transparent 30%),var(--bg);color:var(--text);font:15px/1.6 Inter,Segoe UI,Arial,sans-serif}
a{color:inherit;text-decoration:none}button,.btn{border:0;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:11px 16px;border-radius:12px;color:white;background:linear-gradient(100deg,#7c3aed,#b026ff);font-weight:750;box-shadow:0 0 24px #8b5cf633;transition:.2s}
button:hover,.btn:hover{transform:translateY(-2px);filter:brightness(1.13)}.btn.secondary{background:#20203a;border:1px solid var(--line);box-shadow:none}.btn.green{background:linear-gradient(100deg,#078b67,#22c98e);box-shadow:none}.btn.danger{background:#6d243a;box-shadow:none}
nav{position:sticky;top:0;z-index:20;background:#090916dc;backdrop-filter:blur(16px);border-bottom:1px solid #ffffff12}
.navin{max-width:1180px;margin:auto;padding:14px 22px;display:flex;align-items:center;justify-content:space-between;gap:14px}.brand{font-size:20px;font-weight:950;letter-spacing:1px}.brand span{color:var(--cyan);text-shadow:0 0 18px #42e8ff80}.links{display:flex;gap:18px;align-items:center;color:var(--muted);flex-wrap:wrap}.links a:hover{color:white}
.wrap{max-width:1180px;margin:auto;padding:28px 22px 70px}.hero{padding:64px 0 42px;display:grid;grid-template-columns:1.2fr .8fr;gap:35px;align-items:center}.eyebrow{display:inline-flex;gap:8px;align-items:center;padding:7px 12px;border:1px solid #8b5cf655;background:#8b5cf614;color:#d7b9ff;border-radius:99px;font-size:12px;font-weight:800;letter-spacing:1px}
h1{font-size:clamp(38px,6vw,70px);line-height:1.02;letter-spacing:-2px;margin:18px 0}h1 .shine{background:linear-gradient(90deg,#c084fc,#42e8ff,#ff4fd8);-webkit-background-clip:text;background-clip:text;color:transparent}
p{color:var(--muted)}.hero p{max-width:590px;font-size:17px}.hero-art{min-height:280px;border:1px solid #a855f755;border-radius:28px;background:linear-gradient(145deg,#19102d,#0b2331 70%,#1c1030);display:grid;place-items:center;position:relative;overflow:hidden;box-shadow:0 0 70px #7c3aed20}
.orb{width:150px;height:150px;border-radius:50%;background:radial-gradient(circle at 30% 25%,#fff,#42e8ff 12%,#a855f7 40%,#36105d 70%);box-shadow:0 0 45px #a855f7,0 0 100px #42e8ff40;animation:float 4s ease-in-out infinite}
.hero-art:before,.hero-art:after{content:"";position:absolute;width:240px;height:240px;border:1px solid #42e8ff55;border-radius:50%;animation:spin 14s linear infinite}.hero-art:after{width:300px;height:100px;transform:rotate(-28deg);border-color:#ff4fd866;animation:none}
@keyframes float{50%{transform:translateY(-12px) scale(1.03)}}@keyframes spin{to{transform:rotate(360deg)}}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:15px 0 38px}.stat,.card,.panel{background:linear-gradient(145deg,#141427ed,#0e0e1d);border:1px solid var(--line);border-radius:18px}.stat{padding:16px}.stat strong{display:block;font-size:24px}.stat span{font-size:12px;color:var(--muted)}
.sectionhead{display:flex;justify-content:space-between;align-items:end;gap:15px;margin:35px 0 18px}.sectionhead h2{margin:0;font-size:28px}.products{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.card{padding:18px;transition:.25s;position:relative;overflow:hidden}.card:hover{transform:translateY(-5px);border-color:#9b5cff;box-shadow:0 16px 40px #0005,0 0 24px #a855f718}.productart{height:130px;border-radius:13px;margin-bottom:17px;background:linear-gradient(135deg,#241044,#102b3b);display:grid;place-items:center;font-size:43px;border:1px solid #ffffff0d}.tag{font-size:10px;letter-spacing:1px;font-weight:900;color:var(--cyan);background:#42e8ff13;border:1px solid #42e8ff30;border-radius:7px;padding:4px 7px}.card h3{margin:12px 0 5px;font-size:19px}.card p{min-height:48px;font-size:13px}.price{font-size:22px;font-weight:900;margin:13px 0}.price small{font-size:11px;color:var(--muted);font-weight:500}.cardactions{display:flex;gap:9px;flex-wrap:wrap}.cardactions>*{flex:1}
.panel{padding:22px;margin:15px 0}.formgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.field{display:flex;flex-direction:column;gap:6px}.field.full{grid-column:1/-1}label{color:#d8d6f0;font-size:13px;font-weight:700}input,textarea,select{width:100%;padding:12px 13px;background:#090918;border:1px solid #343451;border-radius:10px;color:white;font:inherit;outline:none}input:focus,textarea:focus,select:focus{border-color:var(--purple);box-shadow:0 0 0 3px #a855f71c}textarea{min-height:100px;resize:vertical}
.flash{padding:12px 15px;border:1px solid #42e8ff55;background:#42e8ff12;border-radius:12px;margin:12px 0;color:#d9faff}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:700px}th,td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.7px}td{font-size:13px}.inline{display:inline}.muted{color:var(--muted)}.pill{display:inline-block;border-radius:99px;padding:4px 9px;background:#a855f71c;color:#d7b9ff;font-size:11px}
footer{border-top:1px solid #ffffff12;padding:25px;text-align:center;color:var(--muted);font-size:12px}
@media(max-width:800px){.hero{grid-template-columns:1fr;padding-top:38px}.hero-art{min-height:210px}.products{grid-template-columns:repeat(2,minmax(0,1fr))}.links{gap:10px;font-size:13px}}
@media(max-width:540px){.navin{align-items:flex-start;flex-direction:column}.links{width:100%;justify-content:space-between}.wrap{padding:18px 14px 45px}.products{grid-template-columns:1fr}.stats{gap:7px}.stat{padding:11px}.stat strong{font-size:19px}.formgrid{grid-template-columns:1fr}.field.full{grid-column:auto}.hero h1{letter-spacing:-1px}.sectionhead{align-items:flex-start;flex-direction:column}}
</style></head><body>
<nav><div class="navin"><a class="brand" href="{{ url_for('home') }}">SADX <span>STORE</span></a><div class="links"><a href="{{ url_for('home') }}#products">Products</a><a href="{{ url_for('home') }}#about">About</a><a href="{{ url_for('order_lookup') }}">My Order</a><a href="{{ url_for('admin_login') }}">Admin ↗</a></div></div></nav>
<div class="wrap">
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}
{{ content|safe }}
</div><footer>© {{ year }} SADX STORE · Digital goods, delivered simply.</footer>
<script>
const reveal = new IntersectionObserver(items=>items.forEach(i=>{if(i.isIntersecting){i.target.style.opacity=1;i.target.style.transform='translateY(0)';reveal.unobserve(i.target)}}),{threshold:.08});
document.querySelectorAll('.card,.stat').forEach(el=>{el.style.opacity=0;el.style.transform='translateY(12px)';el.style.transition='opacity .45s ease,transform .45s ease';reveal.observe(el)});
</script></body></html>
"""

def page(title, content, **context):
    # Content is intentionally rendered as a template-free string; inject the session CSRF token explicitly.
