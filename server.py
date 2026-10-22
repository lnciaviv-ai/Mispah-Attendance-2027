#!/usr/bin/env python3
"""
Mispah School – Digital Daily Attendance Register
Self-contained server (stdlib only).
"""

import json
import os
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from datetime import date, datetime
import secrets
import html

import db

# In-memory session store: session_id -> user_id
SESSIONS = {}

PORT = int(os.environ.get("PORT", 8080))
HOST = "0.0.0.0"

# ---------- Helpers ----------
def make_session(user_id: int) -> str:
    sid = secrets.token_hex(16)
    SESSIONS[sid] = user_id
    return sid

def get_session_user(cookie_header: str):
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if "session" not in cookie:
        return None
    sid = cookie["session"].value
    uid = SESSIONS.get(sid)
    if not uid:
        return None
    return db.get_user(uid)

def redirect(handler, location: str, status=302):
    handler.send_response(status)
    handler.send_header("Location", location)
    handler.end_headers()

def set_cookie(handler, name, value, max_age=86400*7):
    handler.send_header(
        "Set-Cookie",
        f"{name}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}",
    )

def clear_cookie(handler, name):
    handler.send_header("Set-Cookie", f"{name}=; Path=/; Max-Age=0")

def html_escape(s):
    return html.escape(str(s) if s is not None else "")

def today_str():
    return date.today().isoformat()

# ---------- HTML fragments ----------
BASE_CSS = """
:root {
  --primary: #1a5276;
  --primary-dark: #0e2f44;
  --accent: #27ae60;
  --danger: #c0392b;
  --bg: #f4f6f8;
  --card: #ffffff;
  --border: #d5dbe0;
  --text: #2c3e50;
  --muted: #7f8c8d;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}
header {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  padding: 0.85rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
header h1 { font-size: 1.25rem; font-weight: 600; }
header .sub { font-size: 0.8rem; opacity: 0.9; }
nav a {
  color: white;
  text-decoration: none;
  margin-left: 1rem;
  font-size: 0.9rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
}
nav a:hover { background: rgba(255,255,255,0.15); }
.container { max-width: 1100px; margin: 1.5rem auto; padding: 0 1rem; }
.card {
  background: var(--card);
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
h2 { font-size: 1.2rem; margin-bottom: 1rem; color: var(--primary); }
label { display: block; font-weight: 500; margin-bottom: 0.3rem; font-size: 0.9rem; }
input[type=text], input[type=password], input[type=date], select {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 1rem;
  margin-bottom: 1rem;
}
button, .btn {
  display: inline-block;
  background: var(--primary);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}
button:hover, .btn:hover { background: var(--primary-dark); }
.btn-success { background: var(--accent); }
.btn-success:hover { background: #1e8449; }
.btn-danger { background: var(--danger); }
.btn-danger:hover { background: #922b21; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
}
.btn-outline:hover { background: var(--primary); color: white; }
.btn-sm { padding: 0.35rem 0.7rem; font-size: 0.85rem; }
.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}
.alert-success { background: #d5f5e3; color: #1e8449; }
.alert-error { background: #fadbd8; color: #922b21; }
.alert-info { background: #d6eaf8; color: #1a5276; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
th, td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
th { background: #eaf2f8; font-weight: 600; color: var(--primary); }
tr:hover { background: #f8fafc; }
.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}
.badge-present { background: #d5f5e3; color: #1e8449; }
.badge-absent { background: #fadbd8; color: #922b21; }
.badge-unsigned { background: #fef9e7; color: #b7950b; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 700px) {
  .grid-2 { grid-template-columns: 1fr; }
  header { flex-direction: column; align-items: flex-start; }
  nav a { margin-left: 0; margin-right: 0.5rem; }
}
/* Attendance checkboxes */
.learner-row {
  display: flex;
  align-items: center;
  padding: 0.6rem 0.5rem;
  border-bottom: 1px solid var(--border);
  gap: 0.75rem;
}
.learner-row:hover { background: #f8fafc; }
.learner-row label { margin: 0; flex: 1; cursor: pointer; }
.status-toggle {
  display: flex;
  gap: 0.4rem;
}
.status-toggle input { display: none; }
.status-toggle span {
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  font-size: 0.85rem;
  cursor: pointer;
  user-select: none;
}
.status-toggle input:checked + span.present { background: #27ae60; color: white; border-color: #27ae60; }
.status-toggle input:checked + span.absent { background: #c0392b; color: white; border-color: #c0392b; }
/* Print styles for admin register */
@media print {
  header, nav, .no-print { display: none !important; }
  body { background: white; }
  .card { box-shadow: none; border: 1px solid #ccc; }
  table { font-size: 11pt; }
}
.print-header {
  text-align: center;
  margin-bottom: 1rem;
}
.print-header h1 { font-size: 1.4rem; color: #000; }
.print-header p { font-size: 0.9rem; }
"""

def page(title: str, body: str, user=None, extra_head=""):
    nav = ""
    if user:
        nav = f"""
        <nav>
          <a href="/">Tuis / Home</a>
          {"<a href='/admin'>Admin</a>" if user["role"]=="admin" else ""}
          {"<a href='/admin/learners'>Leerders</a>" if user["role"]=="admin" else ""}
          <a href="/logout">Teken uit</a>
        </nav>
        """
    return f"""<!DOCTYPE html>
<html lang="af">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(title)} – Mispah Skool</title>
  <style>{BASE_CSS}</style>
  {extra_head}
</head>
<body>
  <header>
    <div>
      <h1>Mispah Skool – Daaglikse Bywoningsregister</h1>
      <div class="sub">Digital Daily Attendance Register</div>
    </div>
    {nav}
  </header>
  <div class="container">
    {body}
  </div>
</body>
</html>"""

# ---------- Page builders ----------
def login_page(error=None):
    err = f'<div class="alert alert-error">{html_escape(error)}</div>' if error else ""
    body = f"""
    <div class="card" style="max-width:420px;margin:3rem auto;">
      <h2>Teken in / Login</h2>
      {err}
      <form method="POST" action="/login">
        <label>Gebruikersnaam</label>
        <input type="text" name="username" required autofocus placeholder="bv. admin of maree">
        <label>Wagwoord</label>
        <input type="password" name="password" required>
        <button type="submit" style="width:100%;margin-top:0.5rem;">Teken in</button>
      </form>
      <p style="margin-top:1.5rem;font-size:0.85rem;color:var(--muted);">
        <strong>Demo rekeninge:</strong><br>
        Admin: <code>admin</code> / <code>admin123</code><br>
        Onderwysers: <code>maree</code>, <code>cupido</code>, <code>hess</code>,
        <code>veroni</code>, <code>april</code>, <code>fisher</code>, <code>vandyk</code><br>
        Wagwoord vir almal: <code>teacher123</code>
      </p>
    </div>
    """
    return page("Teken in", body)

def teacher_home(user, msg=None):
    classes = db.get_all_classes()
    my_class = None
    if user.get("class_id"):
        my_class = db.get_class(user["class_id"])

    msg_html = f'<div class="alert alert-success">{html_escape(msg)}</div>' if msg else ""

    # Quick link for own class
    own = ""
    if my_class:
        own = f"""
        <div class="card" style="border-left:4px solid var(--accent);">
          <h2>Jou klas / Your class</h2>
          <p style="margin-bottom:1rem;"><strong>{html_escape(my_class['name'])}</strong> – {html_escape(my_class['teacher_name'])}</p>
          <a class="btn btn-success" href="/mark?class_id={my_class['id']}&date={today_str()}">Merk bywoning vandag</a>
        </div>
        """

    rows = ""
    for c in classes:
        rows += f"""
        <tr>
          <td>{html_escape(c['name'])}</td>
          <td>{html_escape(c['teacher_name'])}</td>
          <td>
            <a class="btn btn-sm" href="/mark?class_id={c['id']}&date={today_str()}">Merk</a>
            <a class="btn btn-sm btn-outline" href="/view?class_id={c['id']}&date={today_str()}">Sien</a>
          </td>
        </tr>"""

    body = f"""
    {msg_html}
    <div class="card">
      <h2>Welkom, {html_escape(user['full_name'])}</h2>
      <p style="color:var(--muted);">Kies 'n klas om bywoning te merk of te bekyk.</p>
    </div>
    {own}
    <div class="card">
      <h2>Alle klasse</h2>
      <table>
        <thead><tr><th>Klas</th><th>Opvoeder</th><th>Aksie</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return page("Tuis", body, user)

def mark_page(user, class_id: int, attendance_date: str, msg=None, error=None):
    cls = db.get_class(class_id)
    if not cls:
        return page("Fout", '<div class="alert alert-error">Klas nie gevind nie.</div>', user)

    learners = db.get_class_attendance_detail(attendance_date, class_id)
    msg_html = ""
    if msg:
        msg_html = f'<div class="alert alert-success">{html_escape(msg)}</div>'
    if error:
        msg_html = f'<div class="alert alert-error">{html_escape(error)}</div>'

    rows = ""
    for l in learners:
        present_checked = 'checked' if l.get("status") == "present" else ""
        absent_checked = 'checked' if l.get("status") == "absent" else ""
        # Default to present if never marked
        if l.get("status") is None:
            present_checked = "checked"
        rows += f"""
        <div class="learner-row">
          <label>{html_escape(l['first_name'])} {html_escape(l['last_name'])}
            <span style="color:var(--muted);font-size:0.85rem;">({l['gender']})</span>
          </label>
          <div class="status-toggle">
            <label>
              <input type="radio" name="status_{l['id']}" value="present" {present_checked}>
              <span class="present">Teenwoordig</span>
            </label>
            <label>
              <input type="radio" name="status_{l['id']}" value="absent" {absent_checked}>
              <span class="absent">Afwesig</span>
            </label>
          </div>
        </div>
        """

    if not learners:
        rows = '<p class="alert alert-info">Geen aktiewe leerders in hierdie klas nie. Voeg leerders by via Admin → Leerders.</p>'

    body = f"""
    {msg_html}
    <div class="card">
      <h2>Merk bywoning – {html_escape(cls['name'])}</h2>
      <p style="margin-bottom:1rem;color:var(--muted);">
        Opvoeder: {html_escape(cls['teacher_name'])} &nbsp;|&nbsp;
        Datum: <strong>{html_escape(attendance_date)}</strong>
      </p>
      <form method="POST" action="/mark">
        <input type="hidden" name="class_id" value="{class_id}">
        <input type="hidden" name="date" value="{html_escape(attendance_date)}">
        <div style="margin-bottom:1rem;">
          <label style="display:inline;">Datum</label>
          <input type="date" name="date_change" value="{html_escape(attendance_date)}"
                 onchange="window.location='/mark?class_id={class_id}&date='+this.value"
                 style="width:auto;display:inline-block;margin-left:0.5rem;">
        </div>
        <div style="border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:1.25rem;">
          {rows}
        </div>
        <button type="submit" class="btn-success" style="font-size:1.05rem;">
          Stoor bywoning &amp; teken
        </button>
        <a href="/" class="btn btn-outline" style="margin-left:0.5rem;">Terug</a>
      </form>
    </div>
    """
    return page(f"Merk – {cls['name']}", body, user)

def view_class_page(user, class_id: int, attendance_date: str):
    cls = db.get_class(class_id)
    if not cls:
        return page("Fout", '<div class="alert alert-error">Klas nie gevind nie.</div>', user)
    learners = db.get_class_attendance_detail(attendance_date, class_id)
    rows = ""
    present = absent = 0
    for l in learners:
        st = l.get("status")
        if st == "present":
            present += 1
            badge = '<span class="badge badge-present">Teenwoordig</span>'
        elif st == "absent":
            absent += 1
            badge = '<span class="badge badge-absent">Afwesig</span>'
        else:
            badge = '<span class="badge badge-unsigned">Nog nie gemerk</span>'
        rows += f"""
        <tr>
          <td>{html_escape(l['first_name'])} {html_escape(l['last_name'])}</td>
          <td>{l['gender']}</td>
          <td>{badge}</td>
        </tr>"""

    body = f"""
    <div class="card">
      <h2>{html_escape(cls['name'])} – {html_escape(attendance_date)}</h2>
      <p>Teenwoordig: <strong>{present}</strong> &nbsp;|&nbsp; Afwesig: <strong>{absent}</strong></p>
      <table style="margin-top:1rem;">
        <thead><tr><th>Leerder</th><th>Geslag</th><th>Status</th></tr></thead>
        <tbody>{rows or '<tr><td colspan=3>Geen data</td></tr>'}</tbody>
      </table>
      <p style="margin-top:1rem;">
        <a class="btn" href="/mark?class_id={class_id}&date={attendance_date}">Wysig</a>
        <a class="btn btn-outline" href="/">Terug</a>
      </p>
    </div>
    """
    return page("Sien bywoning", body, user)

def admin_dashboard(user, attendance_date: str = None):
    if not attendance_date:
        attendance_date = today_str()
    register = db.get_full_daily_register(attendance_date)

    # Summary totals
    total_seuns = total_dogters = total_all = 0
    for r in register:
        if r["seuns"] is not None:
            total_seuns += r["seuns"]
            total_dogters += r["dogters"]
            total_all += r["totaal"]

    rows = ""
    for r in register:
        cls = r["class"]
        if r["seuns"] is None:
            seuns = dogters = totaal = "—"
            absent = "—"
            signed = '<span class="badge badge-unsigned">Nie ingedien</span>'
        else:
            seuns = r["seuns"]
            dogters = r["dogters"]
            totaal = r["totaal"]
            absent = ", ".join(r["absent_names"]) if r["absent_names"] else "—"
            signed = '<span class="badge badge-present">Geteken</span>' if r["signed"] else '<span class="badge badge-unsigned">Nie geteken</span>'

        rows += f"""
        <tr>
          <td>{html_escape(cls['name'])}<br><small style="color:var(--muted)">{html_escape(cls['teacher_name'])}</small></td>
          <td style="text-align:center;">{seuns}</td>
          <td style="text-align:center;">{dogters}</td>
          <td style="text-align:center;font-weight:600;">{totaal}</td>
          <td style="font-size:0.9rem;">{html_escape(absent)}</td>
          <td>{signed}</td>
          <td class="no-print">
            <a class="btn btn-sm" href="/mark?class_id={cls['id']}&date={attendance_date}">Merk</a>
          </td>
        </tr>"""

    body = f"""
    <div class="card no-print">
      <h2>Admin – Daaglikse register</h2>
      <form method="GET" action="/admin" style="display:flex;gap:0.75rem;align-items:flex-end;flex-wrap:wrap;">
        <div>
          <label>Datum</label>
          <input type="date" name="date" value="{html_escape(attendance_date)}" style="margin:0;width:auto;">
        </div>
        <button type="submit">Wys</button>
        <button type="button" class="btn-outline" onclick="window.print()">🖨 Druk register</button>
        <a class="btn btn-outline" href="/admin/learners">Bestuur leerders</a>
      </form>
    </div>

    <div class="card">
      <div class="print-header">
        <h1>MISPAH SKOOL VIR LSEN</h1>
        <p>Daaglikse Leerder Bywoningsregister</p>
        <p><strong>Datum: {html_escape(attendance_date)}</strong></p>
      </div>
      <table>
        <thead>
          <tr>
            <th>KLAS</th>
            <th style="text-align:center;">SEUNS</th>
            <th style="text-align:center;">DOGTERS</th>
            <th style="text-align:center;">TOTAAL</th>
            <th>NAME VAN LEERDERS AFWESIG</th>
            <th>OPVOEDER<br>HANDTEKENING</th>
            <th class="no-print">Aksie</th>
          </tr>
        </thead>
        <tbody>
          {rows}
          <tr style="font-weight:700;background:#eaf2f8;">
            <td>TOTAAL</td>
            <td style="text-align:center;">{total_seuns}</td>
            <td style="text-align:center;">{total_dogters}</td>
            <td style="text-align:center;">{total_all}</td>
            <td colspan="3"></td>
          </tr>
        </tbody>
      </table>
      <p style="margin-top:1rem;font-size:0.85rem;color:var(--muted);" class="no-print">
        Slegs klasse wat alreeds gemerk is, word met syfers gewys. Druk die bladsy om 'n harde kopie te kry.
      </p>
    </div>
    """
    return page("Admin Register", body, user)

def learners_admin_page(user, msg=None, error=None):
    learners = db.get_all_learners(active_only=False)
    classes = db.get_all_classes()
    msg_html = ""
    if msg:
        msg_html = f'<div class="alert alert-success">{html_escape(msg)}</div>'
    if error:
        msg_html = f'<div class="alert alert-error">{html_escape(error)}</div>'

    class_options = "".join(
        f'<option value="{c["id"]}">{html_escape(c["name"])}</option>' for c in classes
    )

    rows = ""
    for l in learners:
        status = "Aktief" if l["active"] else "Gedeaktiveer"
        rows += f"""
        <tr>
          <td>{html_escape(l['first_name'])} {html_escape(l['last_name'])}</td>
          <td>{html_escape(l['class_name'])}</td>
          <td>{l['gender']}</td>
          <td>{status}</td>
          <td>
            <a class="btn btn-sm btn-outline" href="/admin/learners?edit={l['id']}">Wysig</a>
            {"<a class='btn btn-sm btn-danger' href='/admin/learners?deactivate=" + str(l['id']) + "' onclick=\"return confirm('Deaktiveer hierdie leerder?')\">Deaktiveer</a>" if l["active"] else ""}
          </td>
        </tr>"""

    # Edit form if requested
    edit_form = ""
    edit_id = None  # handled in handler

    body = f"""
    {msg_html}
    <div class="card">
      <h2>Bestuur leerders</h2>
      <p style="color:var(--muted);margin-bottom:1rem;">
        Voeg nuwe leerders by of wysig bestaande. Deaktiveer leerders wat die skool verlaat het
        (hulle bly in die geskiedenis maar verskyn nie meer in die register nie).
      </p>

      <h3 style="margin:1.5rem 0 0.75rem;font-size:1.05rem;">Voeg nuwe leerder by</h3>
      <form method="POST" action="/admin/learners" class="grid-2">
        <input type="hidden" name="action" value="add">
        <div>
          <label>Voornaam</label>
          <input type="text" name="first_name" required>
        </div>
        <div>
          <label>Van</label>
          <input type="text" name="last_name" required>
        </div>
        <div>
          <label>Klas</label>
          <select name="class_id" required>{class_options}</select>
        </div>
        <div>
          <label>Geslag</label>
          <select name="gender" required>
            <option value="seun">Seun</option>
            <option value="dogter">Dogter</option>
          </select>
        </div>
        <div style="grid-column:1/-1;">
          <button type="submit" class="btn-success">Voeg leerder by</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h2>Alle leerders</h2>
      <table>
        <thead>
          <tr><th>Naam</th><th>Klas</th><th>Geslag</th><th>Status</th><th>Aksie</th></tr>
        </thead>
        <tbody>{rows or '<tr><td colspan=5>Geen leerders nie</td></tr>'}</tbody>
      </table>
    </div>
    <p><a class="btn btn-outline" href="/admin">← Terug na register</a></p>
    """
    return page("Leerders", body, user)

def edit_learner_page(user, learner_id: int, msg=None):
    learners = db.get_all_learners(active_only=False)
    learner = next((l for l in learners if l["id"] == learner_id), None)
    if not learner:
        return learners_admin_page(user, error="Leerder nie gevind nie.")
    classes = db.get_all_classes()
    class_options = "".join(
        f'<option value="{c["id"]}" {"selected" if c["id"]==learner["class_id"] else ""}>{html_escape(c["name"])}</option>'
        for c in classes
    )
    body = f"""
    <div class="card" style="max-width:500px;">
      <h2>Wysig leerder</h2>
      <form method="POST" action="/admin/learners">
        <input type="hidden" name="action" value="edit">
        <input type="hidden" name="learner_id" value="{learner_id}">
        <label>Voornaam</label>
        <input type="text" name="first_name" value="{html_escape(learner['first_name'])}" required>
        <label>Van</label>
        <input type="text" name="last_name" value="{html_escape(learner['last_name'])}" required>
        <label>Klas</label>
        <select name="class_id" required>{class_options}</select>
        <label>Geslag</label>
        <select name="gender" required>
          <option value="seun" {"selected" if learner["gender"]=="seun" else ""}>Seun</option>
          <option value="dogter" {"selected" if learner["gender"]=="dogter" else ""}>Dogter</option>
        </select>
        <label>Aktief</label>
        <select name="active">
          <option value="1" {"selected" if learner["active"] else ""}>Ja</option>
          <option value="0" {"selected" if not learner["active"] else ""}>Nee</option>
        </select>
        <button type="submit" class="btn-success">Stoor</button>
        <a href="/admin/learners" class="btn btn-outline" style="margin-left:0.5rem;">Kanselleer</a>
      </form>
    </div>
    """
    return page("Wysig leerder", body, user)

# ---------- Request handler ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    def parse_qs(self, data: bytes):
        return urllib.parse.parse_qs(data.decode("utf-8", errors="replace"))

    def get_user(self):
        return get_session_user(self.headers.get("Cookie", ""))

    def require_login(self):
        user = self.get_user()
        if not user:
            redirect(self, "/login")
            return None
        return user

    def require_admin(self):
        user = self.require_login()
        if not user:
            return None
        if user["role"] != "admin":
            self.send_error(403, "Slegs administrateurs")
            return None
        return user

    def send_html(self, content: str, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/login":
            if self.get_user():
                redirect(self, "/")
                return
            self.send_html(login_page())
            return

        if path == "/logout":
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            if "session" in cookie:
                SESSIONS.pop(cookie["session"].value, None)
            self.send_response(302)
            clear_cookie(self, "session")
            self.send_header("Location", "/login")
            self.end_headers()
            return

        user = self.require_login()
        if not user:
            return

        if path == "/" or path == "/index":
            msg = qs.get("msg", [None])[0]
            self.send_html(teacher_home(user, msg=msg))
            return

        if path == "/mark":
            class_id = int(qs.get("class_id", [0])[0])
            att_date = qs.get("date", [today_str()])[0]
            msg = qs.get("msg", [None])[0]
            self.send_html(mark_page(user, class_id, att_date, msg=msg))
            return

        if path == "/view":
            class_id = int(qs.get("class_id", [0])[0])
            att_date = qs.get("date", [today_str()])[0]
            self.send_html(view_class_page(user, class_id, att_date))
            return

        if path == "/admin":
            if user["role"] != "admin":
                # Teachers can still see the summary if desired, but keep simple
                pass
            att_date = qs.get("date", [today_str()])[0]
            self.send_html(admin_dashboard(user, att_date))
            return

        if path == "/admin/learners":
            admin = self.require_admin()
            if not admin:
                return
            if "edit" in qs:
                self.send_html(edit_learner_page(admin, int(qs["edit"][0])))
                return
            if "deactivate" in qs:
                db.deactivate_learner(int(qs["deactivate"][0]))
                redirect(self, "/admin/learners?msg=Leerder+gedeaktiveer")
                return
            msg = qs.get("msg", [None])[0]
            self.send_html(learners_admin_page(admin, msg=msg))
            return

        self.send_error(404, "Bladsy nie gevind nie")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        form = self.parse_qs(body)

        if path == "/login":
            username = form.get("username", [""])[0]
            password = form.get("password", [""])[0]
            user = db.authenticate(username, password)
            if not user:
                self.send_html(login_page(error="Verkeerde gebruikersnaam of wagwoord."))
                return
            sid = make_session(user["id"])
            self.send_response(302)
            set_cookie(self, "session", sid)
            self.send_header("Location", "/")
            self.end_headers()
            return

        user = self.require_login()
        if not user:
            return

        if path == "/mark":
            class_id = int(form.get("class_id", [0])[0])
            att_date = form.get("date", [today_str()])[0]
            records = []
            for key, vals in form.items():
                if key.startswith("status_"):
                    lid = int(key.split("_", 1)[1])
                    status = vals[0]
                    if status in ("present", "absent"):
                        records.append({"learner_id": lid, "status": status})
            if records:
                db.save_attendance(att_date, class_id, records, user["id"])
                redirect(self, f"/mark?class_id={class_id}&date={att_date}&msg=Bywoning+gestoor")
            else:
                self.send_html(mark_page(user, class_id, att_date, error="Geen leerders gemerk nie."))
            return

        if path == "/admin/learners":
            admin = self.require_admin()
            if not admin:
                return
            action = form.get("action", [""])[0]
            if action == "add":
                try:
                    db.add_learner(
                        int(form["class_id"][0]),
                        form["first_name"][0],
                        form["last_name"][0],
                        form["gender"][0],
                    )
                    redirect(self, "/admin/learners?msg=Leerder+bygevoeg")
                except Exception as e:
                    self.send_html(learners_admin_page(admin, error=str(e)))
                return
            if action == "edit":
                try:
                    db.update_learner(
                        int(form["learner_id"][0]),
                        int(form["class_id"][0]),
                        form["first_name"][0],
                        form["last_name"][0],
                        form["gender"][0],
                        int(form.get("active", ["1"])[0]),
                    )
                    redirect(self, "/admin/learners?msg=Leerder+opgedateer")
                except Exception as e:
                    self.send_html(learners_admin_page(admin, error=str(e)))
                return

        self.send_error(404)

def main():
    db.init_db()
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Mispah Attendance System running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()

if __name__ == "__main__":
    main()
