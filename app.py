import os
import sqlite3
import csv
import base64
from datetime import datetime, timedelta
from functools import wraps
from io import StringIO
from flask import Flask, render_template_string, request, jsonify, session, g, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "januya_admin_control_v9_key_2026_supersecret")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
DB_NAME = os.getenv("DB_NAME", "januya_admin_control.db")

# --- PWA ICON (base64-енгізілген, сыртқы сілтемеге тәуелді емес) ---
APP_ICON_512 = "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"
APP_ICON_192 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAAFT0lEQVR4nO3dwXLbRBzH8VXGd0ggr8QN0iYxDwCHFmhp07ROeAK4AGmhUAh9AUpdyDv1UpomeQMOntFkYuxY+q60Wun7mZ0e0lRea3/5/6WtHRdbH70OUl1rqSegvBkgIQZIyKhIPQNlzQokxAAJsYUJsQIJGQVLkABbmBBbmJBRsIcJsIUJsYUJMUBCbGFCrEBC3EgUYgUS4jWQECuQEAMkZFR4FS3ACiTEAAnxLkyIG4lCbGFCbGFCrEBCDJAQW5gQK5AQ35UhxH0gIV4DCfEaSIgBEmILE2IFEmKAhNjChFiBhLiRKMR3ZQixhQkxQEK8CxNiBRJigITYwoRYgYS4kSjECiTEayAhViAhvq1HiC1MiC1MiAESMirsYQJGqSeg8Pxk88pXPv/k3yQzqaH47OM3qecwXPPRuSyLGK0VITiSjOXpCSE8P9lMPslrhxfRafxxXXoqfVtCBiiBSrHoeIbcSMxAl9doLXUPHdw4rl5Rjk82k0970bCFCfEFZa06/ufDmv+yq8vkNVB7fq+dnu7mx7swMQaoJaT8dJktrA2/sfTc2nrb2WWyAjUOpqfjDFCzeHpubb2NMpOG2MIa9Ayn53aHm9eMFagpUdITZSaNGgVfktiAZ39/AI9w+8ZpFktjC4vvV5yeL26c5rIutrDIoqQnykzaYYCE2MJi+gWXny/zaV4zVqBooqQnykzaZIDiGGZ6gi0siqc4PV/l1rlKvqCMevoKp+fmab6rYAtD4qQnZwaoPtMT/LCV2n5+tQGPcOfmux6cfCtQHVHSE2UmyeX62znml7A3S5KX4k5u2w8/Lf3pv9t8jJZPYBUtTLI1mbWwaxePr27Tx+9TekJeAVpx8ZrLkOmZV9zN5E7yybTa4n29HXmpqk5gXvQpdUFOFagSvt5xj9bL9IRcAlRv/WJlyPQskcevuKvtyXQDPjRPz73td8lPYHMjjwpEPAYJIP925l5/a89M/wMU6ubA9KxiKP8X9ni6cX/7bPXvP5quw0e8v302hHM7iAo0wzOheXkEqFLxWGLFDEUpP/AIuVhLfx2/4ojkaLq+/IEipGfnLP3pamvkcRtfhLC3E+1nesmjHL1chwff2zlLfq7aHHm0sJlYGfpxQUoWfX11EVOei5wCFJrMkOmpJ5sWVo4H8TJUHpOn58HAOlc5MqtAM7Ey9MPL9fJPItZ8clTsZbtbyhc+iiGnJ+TYwsqx34GV2x9q5ypH3r+hbH/3/Pu/3k85g5zPXhRZXgNdtr97PsCH7o6MW1g5HqZYyIe758mfeBdG9hVopuUMJYlsN/UkQKHFRTU9l/n7gap5tHvuGbusPxUohPCo4drQ9PFz1KsAhSbX2PT8rz7chV0ZkwZWeuI914KRzwvKqozJOGaGJuPz5M+os6NvLawUN0NapM+fGz8ZX/ATNBlfJH8iXR49vAa6PA5Yhg7GF8mfQsdHb1tYqXaGYPgGov8BCkahST1vYeU4rJihQ5vXamMQFWhm9QxVTduQFQfD22D97sV7S/7W9FRSHA51v+TbP6/G6JtPjU5lww2QohjQNZCa4OuBhIxCMEKqzxYmxBYmxAokxM9MFWIFEuI1kBArkBADJMQWJsQKJMQACRnKh62oIW4kCrGFCfEuTIgVSIgBEmILE2IFEmKAhNjChLiRKMS39QjxGkiI10BCrEBCDJAQW5gQK5AQ94GE2MKE2MKEGCAhvitDiBVIiAES4l2YECuQEDcShViBhHgNJMQKJMQACbGFCfFdGUJsYUJsYULcSBRiCxNiCxNiBRJigITYwoRYgYQYICGjorCJqb7/AIjK/4XYYHxTAAAAAElFTkSuQmCC"

# --- DATABASE SETUP ---

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL;")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, password TEXT NOT NULL, name TEXT NOT NULL, role TEXT DEFAULT 'master_repair'
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, type TEXT, client TEXT, phone TEXT, device TEXT, serial_num TEXT, 
            qty INTEGER DEFAULT 1, price REAL DEFAULT 0.0, status TEXT DEFAULT 'Жаңа', author TEXT, 
            master TEXT, notes TEXT, date TEXT, warranty_days INTEGER DEFAULT 30, pay_type TEXT DEFAULT 'Наличка',
            new_cart_model TEXT DEFAULT '', new_cart_qty INTEGER DEFAULT 0, parts_used TEXT DEFAULT '',
            invoice_status TEXT DEFAULT ''
        )''')
        
        cols = [row[1] for row in c.execute("PRAGMA table_info(orders)").fetchall()]
        if 'new_cart_model' not in cols: c.execute("ALTER TABLE orders ADD COLUMN new_cart_model TEXT DEFAULT ''")
        if 'new_cart_qty' not in cols: c.execute("ALTER TABLE orders ADD COLUMN new_cart_qty INTEGER DEFAULT 0")
        if 'parts_used' not in cols: c.execute("ALTER TABLE orders ADD COLUMN parts_used TEXT DEFAULT ''")
        if 'invoice_status' not in cols: c.execute("ALTER TABLE orders ADD COLUMN invoice_status TEXT DEFAULT ''")
        if 'pay_type' not in cols: c.execute("ALTER TABLE orders ADD COLUMN pay_type TEXT DEFAULT 'Наличка'")
        
        c.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, qty INTEGER DEFAULT 0, min_qty INTEGER DEFAULT 5
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS order_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, user TEXT, action TEXT, time TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS cash_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, opened_at TEXT, closed_at TEXT, opened_by TEXT, 
            closed_by TEXT, start_cash REAL DEFAULT 0.0, end_cash_actual REAL DEFAULT 0.0, 
            end_cash_calc REAL DEFAULT 0.0, status TEXT DEFAULT 'OPEN'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, user TEXT, action TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, name TEXT, message TEXT, time TEXT
        )''')
        
        if c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == 0:
            c.executemany("INSERT INTO inventory (name, qty, min_qty) VALUES (?, ?, ?)", [
                ('Тонер (Үнсіз қара)', 50, 10), ('Чип (Universal)', 20, 5), ('Барабан (Drum)', 15, 5)
            ])
        
        # Админді жасырын түрде құру (Еш жерде көрсетілмейді)
        c.execute("SELECT username FROM users WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users VALUES ('admin', ?, 'Бас Әкімші', 'admin')", (generate_password_hash("admin123"),))
        db.commit()

def log_action(user, action):
    try:
        db = get_db()
        db.execute("INSERT INTO logs (time, user, action) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, action))
        db.commit()
    except: pass

def log_order_action(order_id, user, action):
    try:
        db = get_db()
        db.execute("INSERT INTO order_logs (order_id, user, action, time) VALUES (?, ?, ?, ?)", 
                   (order_id, user, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
    except: pass

# --- PWA SUPPORT ---
@app.route('/icon-192.png')
def icon_192():
    return Response(base64.b64decode(APP_ICON_192), mimetype='image/png')

@app.route('/icon-512.png')
def icon_512():
    return Response(base64.b64decode(APP_ICON_512), mimetype='image/png')

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Januya Service Center", "short_name": "Januya", "start_url": "/",
        "display": "standalone", "background_color": "#0f172a", "theme_color": "#4f46e5",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })

@app.route('/sw.js')
def service_worker():
    return Response("const CACHE_NAME='januya-v6';self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));", mimetype='application/javascript')

# --- AUTH & ROLE MIDDLEWARE ---
def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session: return jsonify({'success': False, 'message': 'Авторизация қажет!'}), 401
            if session.get('role') not in required_roles: return jsonify({'success': False, 'message': 'Рұқсат жоқ!'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- API ENDPOINTS ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Тіркелу жойылды, тек Кіру қалды
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = get_db().execute("SELECT * FROM users WHERE username=?", (data.get('username', '').strip().lower(),)).fetchone()
    if user and check_password_hash(user['password'], data.get('password', '')):
        session.permanent = True
        session['username'] = user['username']; session['name'] = user['name']; session['role'] = user['role']
        log_action(user['name'], 'Жүйеге кірді')
        return jsonify({'success': True, 'user': {'username': user['username'], 'name': user['name'], 'role': user['role']}})
    return jsonify({'success': False, 'message': 'Логин немесе құпиясөз қате!'}), 400

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear(); return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    if 'username' in session:
        return jsonify({'logged_in': True, 'user': {'username': session['username'], 'name': session['name'], 'role': session['role']}})
    return jsonify({'logged_in': False})

@app.route('/api/auth/password', methods=['POST'])
def change_password():
    if 'username' not in session: return jsonify({'success': False}), 401
    data = request.get_json()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    if user and check_password_hash(user['password'], data.get('old_password', '')):
        db.execute("UPDATE users SET password=? WHERE username=?", (generate_password_hash(data.get('new_password', '')), session['username']))
        db.commit()
        return jsonify({'success': True, 'message': 'Құпиясөз сәтті өзгертілді!'})
    return jsonify({'success': False, 'message': 'Ескі құпиясөз қате!'}), 400

# --- ҚЫЗМЕТКЕРЛЕРДІ БАСҚАРУ (Тек Админ) ---
@app.route('/api/users', methods=['GET'])
@role_required(['admin'])
def get_users():
    users = get_db().execute("SELECT username, name, role FROM users ORDER BY role ASC").fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
@role_required(['admin'])
def add_user():
    data = request.get_json() or {}
    username = data.get('username', '').strip().lower()
    db = get_db()
    if db.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone():
        return jsonify({'success': False, 'message': 'Бұл логин бұрын алынған!'}), 400
    db.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)", 
               (username, generate_password_hash(data.get('password', '')), data.get('name', ''), data.get('role', 'master_repair')))
    db.commit()
    log_action(session.get('name'), f'Жаңа қызметкер қосылды: {username}')
    return jsonify({'success': True, 'message': 'Қызметкер сәтті қосылды!'})

@app.route('/api/users/<username>/role', methods=['POST'])
@role_required(['admin'])
def upd_role(username):
    role = request.json.get('role')
    db = get_db()
    db.execute("UPDATE users SET role=? WHERE username=?", (role, username))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/users/<username>/password', methods=['POST'])
@role_required(['admin'])
def reset_password(username):
    new_pass = request.json.get('password')
    db = get_db()
    db.execute("UPDATE users SET password=? WHERE username=?", (generate_password_hash(new_pass), username))
    db.commit()
    log_action(session.get('name'), f'{username} құпиясөзін өзгертті')
    return jsonify({'success': True, 'message': 'Құпиясөз жаңартылды!'})

@app.route('/api/users/<username>', methods=['DELETE'])
@role_required(['admin'])
def del_user(username):
    if username == 'admin': return jsonify({'success': False, 'message': 'Бас әкімшін өшіруге болмайды!'}), 400
    db = get_db()
    db.execute("DELETE FROM users WHERE username=?", (username,))
    db.commit()
    log_action(session.get('name'), f'{username} жүйеден өшірілді')
    return jsonify({'success': True})

# --- ЗАКАЗДАР ---
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'username' not in session: return jsonify([]), 401
    role = session.get('role')
    db = get_db()
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if role == 'master_cart': query += " AND type='Заправка картриджа'"
    elif role == 'master_repair': query += " AND type IN ('Ремонт принтера', 'Ремонт ПК/Ноутбука')"
    
    search = request.args.get('search', '').strip()
    if search:
        query += " AND (client LIKE ? OR phone LIKE ? OR serial_num LIKE ? OR id LIKE ?)"
        params.extend([f"%{search}%"] * 4)
        
    filter_type = request.args.get('filter', 'active')
    if filter_type == 'active': query += " AND status NOT IN ('Дайын', 'Бас тартылды')"
    elif filter_type == 'done': query += " AND status = 'Дайын'"
    query += " ORDER BY id DESC"
    return jsonify([dict(o) for o in db.execute(query, params).fetchall()])

@app.route('/api/orders', methods=['POST'])
@role_required(['admin', 'subadmin'])
def add_order():
    data = request.get_json() or {}
    db = get_db()
    new_id = f"ORD-{1000 + db.execute('SELECT COUNT(*) FROM orders').fetchone()[0] + 1}"
    date = datetime.now().strftime("%Y-%m-%d")
    db.execute('''INSERT INTO orders (id, type, client, phone, device, serial_num, qty, price, status, author, notes, date, warranty_days, pay_type, new_cart_model, new_cart_qty) 
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
               (new_id, data.get('type'), data.get('client'), data.get('phone'), data.get('device'),
                data.get('serial_num', '').strip().upper(), int(data.get('qty', 1)), float(data.get('price', 0.0)),
                'Жаңа', session.get('name'), data.get('notes', ''), date, 30, data.get('pay_type', 'Наличка'),
                data.get('new_cart_model', ''), int(data.get('new_cart_qty', 0))))
    db.commit()
    log_order_action(new_id, session.get('name'), 'Заказ қабылданды')
    return jsonify({'success': True, 'message': 'Заказ сәтті қосылды!'})

@app.route('/api/orders/<order_id>', methods=['PUT'])
@role_required(['admin', 'subadmin'])
def edit_order(order_id):
    data = request.get_json() or {}
    db = get_db()
    db.execute('''UPDATE orders SET type=?, client=?, phone=?, device=?, serial_num=?, price=?, pay_type=?, notes=?, new_cart_model=?, new_cart_qty=?, parts_used=? WHERE id=?''', 
               (data.get('type'), data.get('client'), data.get('phone'), data.get('device'), data.get('serial_num'), 
                float(data.get('price', 0)), data.get('pay_type'), data.get('notes'), 
                data.get('new_cart_model'), int(data.get('new_cart_qty', 0)), data.get('parts_used'), order_id))
    db.commit()
    return jsonify({'success': True, 'message': 'Мәліметтер сақталды!'})

@app.route('/api/orders/<order_id>/status', methods=['POST'])
@role_required(['admin', 'subadmin', 'master_cart', 'master_repair'])
def update_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    db = get_db()
    if new_status == 'Дайын':
        order = db.execute("SELECT pay_type FROM orders WHERE id=?", (order_id,)).fetchone()
        if order and order['pay_type'] == 'Счет':
            db.execute("UPDATE orders SET status=?, master=?, invoice_status='Күтуде' WHERE id=?", (new_status, session.get('name'), order_id))
        else:
            db.execute("UPDATE orders SET status=?, master=? WHERE id=?", (new_status, session.get('name'), order_id))
    else:
        db.execute("UPDATE orders SET status=?, master=? WHERE id=?", (new_status, session.get('name'), order_id))
    db.commit()
    log_order_action(order_id, session.get('name'), f'Статус өзгертілді: {new_status}')
    return jsonify({'success': True})

# --- БУХГАЛТЕРИЯ ---
@app.route('/api/accounting/pending', methods=['GET'])
@role_required(['admin', 'accountant'])
def get_pending_invoices():
    orders = get_db().execute("SELECT * FROM orders WHERE status='Дайын' AND pay_type='Счет' AND invoice_status='Күтуде' ORDER BY id DESC").fetchall()
    return jsonify([dict(o) for o in orders])

@app.route('/api/orders/<order_id>/pay-invoice', methods=['POST'])
@role_required(['admin', 'accountant'])
def pay_invoice(order_id):
    db = get_db()
    db.execute("UPDATE orders SET invoice_status='Төленді' WHERE id=?", (order_id,))
    db.commit()
    log_action(session.get('name'), f'{order_id} счет төленді деп белгіленді')
    log_order_action(order_id, session.get('name'), 'Счет төленді')
    return jsonify({'success': True, 'message': 'Счет төленді деп белгіленді!'})

@app.route('/api/orders/<order_id>/logs', methods=['GET'])
def get_order_logs(order_id):
    if 'username' not in session: return jsonify([]), 401
    logs = get_db().execute("SELECT * FROM order_logs WHERE order_id=? ORDER BY id ASC", (order_id,)).fetchall()
    return jsonify([dict(l) for l in logs])

# --- СКЛАД ---
@app.route('/api/inventory', methods=['GET'])
@role_required(['admin', 'subadmin', 'master_cart', 'master_repair'])
def get_inventory():
    items = get_db().execute("SELECT * FROM inventory ORDER BY name ASC").fetchall()
    return jsonify([dict(i) for i in items])

@app.route('/api/inventory', methods=['POST'])
@role_required(['admin', 'subadmin', 'master_cart', 'master_repair'])
def add_inventory():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Атауын енгізіңіз!'}), 400
    db = get_db()
    exists = db.execute("SELECT id FROM inventory WHERE LOWER(name)=LOWER(?)", (name,)).fetchone()
    if exists:
        return jsonify({'success': False, 'message': 'Бұл тауар складта бар болып тұр!'}), 400
    try:
        qty = int(data.get('qty', 0))
        min_qty = int(data.get('min_qty', 5))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Сан дұрыс емес!'}), 400
    db.execute("INSERT INTO inventory (name, qty, min_qty) VALUES (?, ?, ?)", (name, qty, min_qty))
    db.commit()
    log_action(session.get('name'), f"Складқа жаңа тауар қосты: {name} ({qty} шт)")
    return jsonify({'success': True, 'message': 'Тауар складқа қосылды!'})

@app.route('/api/inventory/<item_id>', methods=['PUT'])
@role_required(['admin'])
def update_inventory(item_id):
    data = request.get_json() or {}
    db = get_db()
    db.execute("UPDATE inventory SET qty=?, min_qty=? WHERE id=?", (int(data.get('qty', 0)), int(data.get('min_qty', 5)), item_id))
    db.commit()
    return jsonify({'success': True})

# --- КЛИЕНТТЕР ---
@app.route('/api/clients', methods=['GET'])
@role_required(['admin', 'subadmin', 'accountant'])
def get_clients():
    clients = get_db().execute("SELECT phone, client, COUNT(id) as visits, SUM(CASE WHEN status='Дайын' THEN price ELSE 0 END) as total_spent FROM orders GROUP BY phone ORDER BY visits DESC").fetchall()
    return jsonify([dict(c) for c in clients])

# --- EXCEL ---
@app.route('/api/orders/export', methods=['GET'])
@role_required(['admin'])
def export_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    output = StringIO(); output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['ID', 'Күні', 'Типі', 'Клиент', 'Телефон', 'Құрылғы', 'Бағасы', 'Төлем', 'Статус', 'Счет', 'Мастер'])
    for o in orders:
        writer.writerow([o['id'], o['date'], o['type'], o['client'], o['phone'], o['device'], o['price'], o['pay_type'], o['status'], o['invoice_status'], o['master']])
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=januya_accounts.csv"})

# --- АНАЛИТИКА ---
@app.route('/api/analytics')
def get_analytics():
    if 'username' not in session: return jsonify({}), 401
    role = session.get('role')
    db = get_db()
    
    weekly_data = [0] * 7
    today = datetime.now()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.execute("SELECT COUNT(*) FROM orders WHERE date=?", (day.strftime("%Y-%m-%d"),)).fetchone()[0]
        weekly_data[6-i] = count

    if role in ['admin', 'subadmin', 'accountant']:
        orders = db.execute("SELECT * FROM orders WHERE date >= ?", ((today - timedelta(days=30)).strftime("%Y-%m-%d"),)).fetchall()
        done_paid = [o for o in orders if o['status'] == 'Дайын' and (o['pay_type'] == 'Наличка' or o['invoice_status'] == 'Төленді')]
        pending_inv = [o for o in orders if o['status'] == 'Дайын' and o['pay_type'] == 'Счет' and o['invoice_status'] == 'Күтуде']
        masters_data = db.execute("SELECT master, COUNT(id) as done_count FROM orders WHERE status='Дайын' AND master IS NOT NULL GROUP BY master ORDER BY done_count DESC").fetchall()
        return jsonify({
            'type': 'global', 'total_revenue': sum(o['price'] for o in done_paid),
            'pending_invoices_sum': sum(o['price'] for o in pending_inv), 'pending_invoices_count': len(pending_inv),
            'total_orders': len(orders), 'done_orders': len([o for o in orders if o['status'] == 'Дайын']),
            'weekly': weekly_data, 'masters_kpi': [dict(m) for m in masters_data]
        })
    else:
        my_orders = db.execute("SELECT * FROM orders WHERE master=? OR author=?", (session.get('name'), session.get('name'))).fetchall()
        done = [o for o in my_orders if o['status'] == 'Дайын']
        active = [o for o in my_orders if o['status'] not in ['Дайын', 'Бас тартылды']]
        return jsonify({'type': 'personal', 'my_total': len(my_orders), 'my_done': len(done), 'my_active': len(active), 'weekly': weekly_data})

# --- КАССА ---
@app.route('/api/cash/shift/status', methods=['GET'])
@role_required(['admin'])
def shift_status():
    shift = get_db().execute("SELECT * FROM cash_shifts WHERE status='OPEN' ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify({'is_open': bool(shift), 'shift': dict(shift) if shift else None})

@app.route('/api/cash/shift/open', methods=['POST'])
@role_required(['admin'])
def open_shift():
    db = get_db()
    if db.execute("SELECT id FROM cash_shifts WHERE status='OPEN'").fetchone(): return jsonify({'success': False, 'message': 'Ауысым ашық!'}), 400
    db.execute("INSERT INTO cash_shifts (opened_at, opened_by, start_cash, status) VALUES (?, ?, ?, 'OPEN')", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session.get('name'), float(request.json.get('start_cash', 0.0))))
    db.commit()
    return jsonify({'success': True})

@app.route('/api/cash/shift/close', methods=['POST'])
@role_required(['admin'])
def close_shift():
    db = get_db()
    shift = db.execute("SELECT * FROM cash_shifts WHERE status='OPEN' ORDER BY id DESC LIMIT 1").fetchone()
    if not shift: return jsonify({'success': False, 'message': 'Ашық ауысым жоқ'}), 400
    end_cash_actual = float(request.json.get('end_cash_actual', 0.0))
    cash_orders = db.execute("SELECT SUM(price) FROM orders WHERE date >= ? AND pay_type='Наличка' AND status='Дайын'", (shift['opened_at'][:10],)).fetchone()[0] or 0.0
    end_cash_calc = shift['start_cash'] + cash_orders
    db.execute('''UPDATE cash_shifts SET closed_at=?, closed_by=?, end_cash_actual=?, end_cash_calc=?, status='CLOSED' WHERE id=?''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session.get('name'), end_cash_actual, end_cash_calc, shift['id']))
    db.commit()
    return jsonify({'success': True, 'diff': end_cash_actual - end_cash_calc})

@app.route('/api/logs', methods=['GET'])
@role_required(['admin'])
def get_logs():
    logs = get_db().execute("SELECT * FROM logs ORDER BY id DESC LIMIT 30").fetchall()
    return jsonify([dict(l) for l in logs])

# --- ЖАҢА ЗАКАЗДЫ БАЙҚАУ (дыбыс үшін polling) ---
@app.route('/api/orders/latest', methods=['GET'])
def get_latest_order():
    if 'username' not in session: return jsonify({'latest_id': None, 'count': 0}), 401
    role = session.get('role')
    db = get_db()
    query = "SELECT id FROM orders WHERE 1=1"
    params = []
    if role == 'master_cart': query += " AND type='Заправка картриджа'"
    elif role == 'master_repair': query += " AND type IN ('Ремонт принтера', 'Ремонт ПК/Ноутбука')"
    query += " ORDER BY id DESC LIMIT 1"
    row = db.execute(query, params).fetchone()
    count_row = db.execute("SELECT COUNT(*) FROM orders").fetchone()
    return jsonify({'latest_id': row['id'] if row else None, 'count': count_row[0] if count_row else 0})

# --- ОРТАҚ ЧАТ ---
@app.route('/api/chat/messages', methods=['GET'])
def get_chat_messages():
    if 'username' not in session: return jsonify([]), 401
    try:
        after_id = int(request.args.get('after_id', 0))
    except (TypeError, ValueError):
        after_id = 0
    db = get_db()
    rows = db.execute("SELECT * FROM chat_messages WHERE id > ? ORDER BY id ASC LIMIT 200", (after_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/chat/messages', methods=['POST'])
def post_chat_message():
    if 'username' not in session: return jsonify({'success': False, 'message': 'Авторизация қажет!'}), 401
    data = request.get_json() or {}
    text = (data.get('message') or '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'Хабарлама бос болмауы керек!'}), 400
    db = get_db()
    db.execute("INSERT INTO chat_messages (username, name, message, time) VALUES (?, ?, ?, ?)",
               (session['username'], session['name'], text[:2000], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return jsonify({'success': True})

# --- PREMIUM FRONTEND ---
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="kk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Januya Service Center CRM</title>
    <meta name="theme-color" content="#0f172a">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/icon-192.png">
    <link rel="apple-touch-icon" href="/icon-192.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Januya">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config = { darkMode: 'class' }</script>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style> 
        body { font-family: 'Manrope', sans-serif; user-select: none; -webkit-tap-highlight-color: transparent; } 
        .fade-in { animation: fadeIn 0.4s ease-out; } 
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } } 
        .toast { animation: slideIn 0.3s ease-out; } 
        @keyframes slideIn { from { transform: translateX(120%); opacity: 0; } to { transform: translateX(0); opacity: 1; } } 
        .sidebar-mobile { transform: translateX(-100%); transition: transform 0.3s ease-in-out; }
        @media (min-width: 768px) { .sidebar-mobile { transform: translateX(0); } }
        .bar-chart { display: flex; align-items: flex-end; height: 140px; gap: 10px; padding-top: 24px; }
        .bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; gap: 6px; }
        .bar { width: 100%; background: linear-gradient(180deg, #818cf8, #4f46e5); border-radius: 8px 8px 3px 3px; transition: height 0.6s cubic-bezier(.34,1.56,.64,1), transform 0.15s; position: relative; min-height: 4px; cursor: default; box-shadow: 0 2px 8px -2px rgba(79,70,229,0.4); }
        .bar:hover { transform: scaleY(1.02); filter: brightness(1.1); }
        .bar-label { position: absolute; top: -22px; left: 50%; transform: translateX(-50%); font-size: 11px; font-weight: 800; color: #4f46e5; }
        .dark .bar-label { color: #a5b4fc; }
        .bar-day { font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.03em; }
        .kpi-row { display: flex; align-items: center; gap: 12px; }
        .kpi-track { flex: 1; height: 10px; border-radius: 6px; background: rgba(148,163,184,0.15); overflow: hidden; }
        .kpi-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #4f46e5, #8b5cf6); transition: width 0.8s cubic-bezier(.34,1.56,.64,1); }
    </style>
</head>
<body class="bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-h-screen flex flex-col transition-colors duration-300">

    <div id="toast" class="hidden fixed top-5 right-5 z-[110] px-6 py-3 rounded-xl shadow-2xl toast font-medium text-white"></div>

    <div id="install-prompt" class="hidden fixed bottom-4 left-1/2 -translate-x-1/2 bg-white dark:bg-slate-800 border border-indigo-500/50 p-4 rounded-2xl shadow-2xl z-[100] flex items-center gap-4 max-w-sm w-[90%]">
        <div class="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-2xl">📱</div>
        <div class="flex-1"><h4 class="font-bold text-sm text-slate-900 dark:text-white">Басты бетке қосу?</h4><p class="text-xs text-slate-500 dark:text-slate-400">Программа ретінде жылдам ашыңыз.</p></div>
        <div class="flex flex-col gap-1"><button id="install-btn" class="bg-indigo-600 text-white text-xs px-3 py-1.5 rounded-lg font-bold">Иә</button><button id="close-install" class="text-slate-500 text-xs">Жоқ</button></div>
    </div>

    <!-- AUTH (Тек Кіру) -->
    <div id="auth-container" class="fixed inset-0 bg-slate-100 dark:bg-slate-950 z-50 flex items-center justify-center p-4 transition-colors duration-300">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 rounded-3xl max-w-sm w-full space-y-5 shadow-2xl fade-in">
            <div class="text-center space-y-1">
                <div class="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center font-bold text-3xl text-white mx-auto shadow-lg">J</div>
                <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white pt-2">Januya Service</h2>
                <p class="text-xs text-slate-500 dark:text-slate-400">Жүйеге кіру үшін логин мен құпиясөзді енгізіңіз</p>
            </div>
            <form id="form-login" onsubmit="handleLogin(event)" class="space-y-3 text-xs">
                <input id="loginUsername" required type="text" placeholder="Логин" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500">
                <input id="loginPassword" required type="password" placeholder="Құпиясөз" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500">
                <button type="submit" class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold p-3 rounded-xl transition">Кіру</button>
            </form>
        </div>
    </div>

    <!-- APP LAYOUT -->
    <div id="app-container" class="hidden flex-1 flex flex-col md:flex-row">
        <aside id="sidebar" class="sidebar-mobile fixed md:relative w-64 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col z-40 transition-colors duration-300">
            <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center font-bold text-white shadow-lg">J</div>
                <div><h3 class="font-bold text-slate-900 dark:text-white">Januya Service</h3><p class="text-[10px] text-slate-500">Enterprise CRM v9.0</p></div>
            </div>
            <nav class="flex-1 p-4 space-y-1 text-sm" id="sidebar-nav">
                <button onclick="navigate('dashboard')" class="nav-btn w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">📊 Басқару панелі</button>
                <button onclick="navigate('orders')" id="nav-orders" class="nav-btn w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">📦 Тапсырыстар</button>
                <button onclick="navigate('accounting')" id="nav-accounting" class="nav-btn hidden w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">💼 Бухгалтерия</button>
                <button onclick="navigate('inventory')" id="nav-inventory" class="nav-btn w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">🗂️ Склад</button>
                <button onclick="navigate('clients')" id="nav-clients" class="nav-btn hidden w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">👥 Клиенттер</button>
                <button onclick="navigate('users')" id="nav-users" class="nav-btn hidden w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">👑 Қызметкерлер</button>
                <button onclick="navigate('cash')" id="nav-cash" class="nav-btn hidden w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">💵 Касса</button>
                <button onclick="navigate('logs')" id="nav-logs" class="nav-btn hidden w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">📜 Жүйе логтары</button>
                <button onclick="navigate('chat')" class="nav-btn w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">💬 Ортақ чат</button>
                <button onclick="navigate('profile')" class="nav-btn w-full text-left flex items-center gap-3 p-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">👤 Профиль</button>
            </nav>
            <div class="p-4 border-t border-slate-200 dark:border-slate-800">
                <div class="flex items-center gap-3 mb-3">
                    <div class="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center font-bold text-indigo-500" id="user-avatar">?</div>
                    <div><p id="user-display-name" class="text-sm font-bold text-slate-900 dark:text-white">...</p><p id="user-display-role" class="text-[10px] text-slate-500">...</p></div>
                </div>
                <button onclick="handleLogout()" class="w-full bg-red-500/10 hover:bg-red-500/20 text-rose-500 py-2 rounded-lg text-xs font-medium transition">Шығу</button>
            </div>
        </aside>

        <div class="flex-1 flex flex-col overflow-hidden">
            <header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 p-4 flex items-center justify-between md:hidden transition-colors duration-300">
                <button onclick="toggleSidebar()" class="text-slate-900 dark:text-white"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg></button>
                <span class="font-bold text-slate-900 dark:text-white">Januya CRM</span>
                <button onclick="toggleTheme()" class="text-xl">🌙</button>
            </header>

            <main class="flex-1 overflow-y-auto p-4 md:p-8 bg-slate-100 dark:bg-slate-950 transition-colors duration-300">
                <!-- DASHBOARD -->
                <section id="view-dashboard" class="fade-in">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white">Басқару панелі</h2>
                        <button onclick="toggleTheme()" class="hidden md:block text-xl bg-white dark:bg-slate-800 p-2 rounded-xl border border-slate-200 dark:border-slate-700">🌙</button>
                    </div>
                    <div id="dashboard-widgets" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"></div>
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                            <div class="flex justify-between items-baseline mb-2">
                                <h3 class="text-base font-bold text-slate-900 dark:text-white">Соңғы 7 күн (Тапсырыстар)</h3>
                                <span id="weekly-total" class="text-xs font-bold text-indigo-500"></span>
                            </div>
                            <div class="bar-chart" id="weekly-chart"></div>
                        </div>
                        <div id="kpi-card" class="hidden bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
                            <h3 class="text-base font-bold text-slate-900 dark:text-white mb-4">🏆 Мастерлер топ-рейтингі</h3>
                            <div id="masters-kpi" class="space-y-3"></div>
                        </div>
                    </div>
                </section>

                <!-- ORDERS -->
                <section id="view-orders" class="hidden fade-in">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white">Тапсырыстар</h2>
                        <div class="flex gap-2">
                            <button id="export-btn" onclick="exportToExcel()" class="hidden bg-emerald-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition">📥 Excel</button>
                            <button id="add-order-btn" onclick="openNewOrderModal()" class="hidden bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition">+ Жаңа</button>
                        </div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 mb-4">
                        <input id="search-input" oninput="loadOrders('active')" type="text" placeholder="🔍 Іздеу..." class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs text-slate-900 dark:text-white mb-3 focus:outline-none focus:border-indigo-500">
                        <div class="flex gap-2">
                            <button onclick="loadOrders('active')" class="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-200 px-3 py-1.5 rounded-xl text-xs flex-1">Белсенді</button>
                            <button onclick="loadOrders('done')" class="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-200 px-3 py-1.5 rounded-xl text-xs flex-1">Аяқталған</button>
                        </div>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                            <thead class="bg-slate-50 dark:bg-slate-800/50 uppercase text-slate-400 font-bold border-b border-slate-200 dark:border-slate-800">
                                <tr><th class="p-3">ID</th><th class="p-3">Құрылғы</th><th class="p-3">Клиент (WA)</th><th class="p-3">Төлем</th><th class="p-3">Статус</th><th class="p-3 text-right">Әрекет</th></tr>
                            </thead>
                            <tbody id="orders-tbody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                        </table>
                    </div>
                </section>

                <!-- ACCOUNTING -->
                <section id="view-accounting" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">💼 Бухгалтерия (Счеттар)</h2>
                    <div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/30 text-amber-600 dark:text-amber-400 p-4 rounded-2xl mb-4 text-sm">
                        ⚠️ Мұнда "Счет" арқылы төлейтін және жұмысы дайын болған, бірақ төлемі күтуде тұрған заказдар шығады. "Төленді" басқан кезде ғана ақша жалпы қаржыға қосылады.
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                            <thead class="bg-slate-50 dark:bg-slate-800/50 uppercase text-slate-400 font-bold border-b border-slate-200 dark:border-slate-800">
                                <tr><th class="p-3">ID</th><th class="p-3">Клиент</th><th class="p-3">Құрылғы</th><th class="p-3">Сомма</th><th class="p-3 text-right">Әрекет</th></tr>
                            </thead>
                            <tbody id="accounting-tbody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                        </table>
                    </div>
                </section>

                <!-- INVENTORY -->
                <section id="view-inventory" class="hidden fade-in">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white">🗂️ Склад (Қойма)</h2>
                        <button onclick="openAddInvModal()" class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition">+ Жаңа тауар</button>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                            <thead class="bg-slate-50 dark:bg-slate-800/50 uppercase text-slate-400 font-bold border-b border-slate-200 dark:border-slate-800">
                                <tr><th class="p-3">Атауы</th><th class="p-3">Қалдық</th><th id="inv-action-th" class="p-3 text-right hidden">Әрекет</th></tr>
                            </thead>
                            <tbody id="inventory-tbody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                        </table>
                    </div>
                </section>

                <!-- CLIENTS -->
                <section id="view-clients" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">👥 Клиенттер базасы</h2>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                            <thead class="bg-slate-50 dark:bg-slate-800/50 uppercase text-slate-400 font-bold border-b border-slate-200 dark:border-slate-800">
                                <tr><th class="p-3">Клиент</th><th class="p-3">Телефон</th><th class="p-3">Келу саны</th><th class="p-3">Жалпы шығын</th></tr>
                            </thead>
                            <tbody id="clients-tbody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                        </table>
                    </div>
                </section>

                <!-- USERS (Қызметкерлерді басқару) -->
                <section id="view-users" class="hidden fade-in">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white">👑 Қызметкерлер</h2>
                        <button onclick="openAddUserModal()" class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition">+ Жаңа қызметкер</button>
                    </div>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table class="w-full text-left text-xs text-slate-600 dark:text-slate-300">
                            <thead class="bg-slate-50 dark:bg-slate-800/50 uppercase text-slate-400 font-bold border-b border-slate-200 dark:border-slate-800">
                                <tr><th class="p-3">Аты</th><th class="p-3">Логин</th><th class="p-3">Рөлі</th><th class="p-3 text-right">Әрекет</th></tr>
                            </thead>
                            <tbody id="users-tbody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                        </table>
                    </div>
                </section>

                <!-- CASH -->
                <section id="view-cash" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">💵 Кассалық Ауысым</h2>
                    <div class="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-md">
                        <div id="shift-status-box" class="text-sm space-y-4"></div>
                    </div>
                </section>

                <!-- LOGS -->
                <section id="view-logs" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">📜 Жүйелік логтар</h2>
                    <div class="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3" id="logs-container"></div>
                </section>

                <!-- CHAT -->
                <section id="view-chat" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">💬 Ортақ чат</h2>
                    <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col h-[65vh]">
                        <div id="chat-messages" class="flex-1 overflow-y-auto p-4 space-y-3 text-xs"></div>
                        <form id="form-chat" onsubmit="sendChatMessage(event)" class="border-t border-slate-200 dark:border-slate-800 p-3 flex gap-2">
                            <input id="chat-input" autocomplete="off" type="text" placeholder="Хабарлама жазу..." class="flex-1 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500">
                            <button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold transition">➤</button>
                        </form>
                    </div>
                </section>

                <!-- PROFILE -->
                <section id="view-profile" class="hidden fade-in">
                    <h2 class="text-2xl font-extrabold text-slate-900 dark:text-white mb-6">👤 Жеке профиль</h2>
                    <div class="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-md">
                        <h3 class="text-base font-bold text-slate-900 dark:text-white mb-4">Құпиясөзді өзгерту</h3>
                        <form onsubmit="changePassword(event)" class="space-y-3 text-xs">
                            <input id="oldPass" required type="password" placeholder="Ескі құпиясөз" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                            <input id="newPass" required type="password" placeholder="Жаңа құпиясөз" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                            <button type="submit" class="w-full bg-indigo-600 text-white font-bold p-3 rounded-xl transition">Сақтау</button>
                        </form>
                    </div>
                </section>
            </main>
        </div>
    </div>

    <!-- ЖАҢА ЗАКАЗ МОДАЛЫ -->
    <div id="modal-order" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 fade-in max-h-[90vh] overflow-y-auto">
            <h3 class="text-base font-bold text-slate-900 dark:text-white">Жаңа Тапсырыс Тіркеу</h3>
            <form id="form-order" onsubmit="submitOrder(event)" class="space-y-3 text-xs">
                <select id="ordType" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"><option>Заправка картриджа</option><option>Ремонт принтера</option><option>Ремонт ПК/Ноутбука</option></select>
                <input id="ordClient" required type="text" placeholder="Клиент аты" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <input id="ordPhone" required type="text" placeholder="Телефон (8707...)" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <input id="ordDevice" required type="text" placeholder="Құрылғы" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <input id="ordSn" type="text" placeholder="S/N" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <div class="grid grid-cols-2 gap-2">
                    <input id="ordPrice" required type="number" placeholder="Бағасы" class="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                    <select id="ordPaytype" class="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"><option>Наличка</option><option>Счет</option></select>
                </div>
                <textarea id="ordNotes" rows="2" placeholder="Ақау сипаттамасы" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"></textarea>
                <div class="flex justify-end gap-2 pt-2">
                    <button type="button" onclick="closeModal('modal-order')" class="bg-slate-200 dark:bg-slate-800 px-4 py-2 rounded-xl text-slate-600 dark:text-slate-300">Бас тарту</button>
                    <button type="submit" class="bg-indigo-600 px-4 py-2 rounded-xl text-white font-bold">Сақтау</button>
                </div>
            </form>
        </div>
    </div>

    <!-- ЖАҢА ҚЫЗМЕТКЕР МОДАЛЫ -->
    <div id="modal-user" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4" onclick="if(event.target.id==='modal-user')closeModal('modal-user')">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 fade-in">
            <div class="flex justify-between items-center"><h3 class="text-base font-bold text-slate-900 dark:text-white">Жаңа Қызметкер</h3><button onclick="closeModal('modal-user')" class="text-slate-400">✕</button></div>
            <form onsubmit="submitUser(event)" class="space-y-3 text-xs">
                <input id="usrName" required type="text" placeholder="Аты-жөні" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                <input id="usrUsername" required type="text" placeholder="Логин" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                <input id="usrPassword" required type="password" placeholder="Құпиясөз" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                <select id="usrRole" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                    <option value="admin">Админ</option>
                    <option value="subadmin">Кіші админ</option>
                    <option value="master_cart">Мастер (Картридж)</option>
                    <option value="master_repair">Мастер (Ремонт)</option>
                    <option value="accountant">Бухгалтер</option>
                </select>
                <button type="submit" class="w-full bg-indigo-600 text-white font-bold p-3 rounded-xl transition">Қызметкерді қосу</button>
            </form>
        </div>
    </div>

    <!-- ЖАҢА ТАУАР ҚОСУ МОДАЛЫ -->
    <div id="modal-inv-add" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4" onclick="if(event.target.id==='modal-inv-add')closeModal('modal-inv-add')">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 fade-in">
            <div class="flex justify-between items-center"><h3 class="text-base font-bold text-slate-900 dark:text-white">Складқа жаңа тауар</h3><button onclick="closeModal('modal-inv-add')" class="text-slate-400">✕</button></div>
            <form onsubmit="submitInvAdd(event)" class="space-y-3 text-xs">
                <input id="invName" required type="text" placeholder="Тауар атауы (мыс. HP 85A картриджі)" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white">
                <div class="grid grid-cols-2 gap-3">
                    <div><label class="text-[10px] text-slate-500">Бастапқы саны</label><input id="invQty" required type="number" min="0" value="1" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white"></div>
                    <div><label class="text-[10px] text-slate-500">Min мөлшер (ескерту)</label><input id="invMinQty" required type="number" min="0" value="5" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white"></div>
                </div>
                <button type="submit" class="w-full bg-indigo-600 text-white font-bold p-3 rounded-xl transition">Складқа қосу</button>
            </form>
        </div>
    </div>

    <!-- ЗАКАЗДЫ ӨЗГЕРТУ МОДАЛЫ -->
    <div id="modal-edit" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4" onclick="if(event.target.id==='modal-edit')closeModal('modal-edit')">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 fade-in max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center"><h3 class="text-base font-bold text-slate-900 dark:text-white">Заказды өзгерту</h3><button onclick="closeModal('modal-edit')" class="text-slate-400">✕</button></div>
            <form id="form-edit" onsubmit="submitEdit(event)" class="space-y-3 text-xs">
                <input type="hidden" id="editId">
                <select id="editType" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"><option>Заправка картриджа</option><option>Ремонт принтера</option><option>Ремонт ПК/Ноутбука</option></select>
                <input id="editClient" required type="text" placeholder="Клиент аты" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <input id="editPhone" required type="text" placeholder="Телефон" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <input id="editDevice" required type="text" placeholder="Құрылғы" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                <div class="grid grid-cols-2 gap-2">
                    <input id="editPrice" required type="number" placeholder="Бағасы" class="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white">
                    <select id="editPaytype" class="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"><option>Наличка</option><option>Счет</option></select>
                </div>
                <textarea id="editNotes" rows="2" placeholder="Ескерту" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"></textarea>
                <button type="submit" class="w-full bg-indigo-600 px-4 py-2 rounded-xl text-white font-bold">Өзгерістерді сақтау</button>
            </form>
        </div>
    </div>

    <!-- ЗАКАЗ ТОЛЫҚ АҚПАРАТЫ МОДАЛЫ -->
    <div id="modal-details" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4" onclick="if(event.target.id==='modal-details')closeModal('modal-details')">
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 fade-in max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center"><h3 class="text-base font-bold text-slate-900 dark:text-white">Заказ ақпараты</h3><button onclick="closeModal('modal-details')" class="text-slate-400">✕</button></div>
            <div id="details-content" class="space-y-2 text-xs"></div>
            <div class="pt-4 mt-4 border-t border-slate-200 dark:border-slate-700">
                <h4 class="text-xs font-bold text-slate-500 mb-2 uppercase">📜 Тарих</h4>
                <div id="details-history" class="space-y-2 text-xs"></div>
            </div>
            <div id="details-actions" class="flex flex-wrap gap-2 pt-4"></div>
        </div>
    </div>

    <script>
        let currentRole = 'guest';
        let allOrdersCache = [];
        let lastOrderId = null;
        let orderPollTimer = null;
        let chatPollTimer = null;
        let lastChatId = 0;
        let audioCtx = null;

        function unlockAudio() {
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                if (audioCtx.state === 'suspended') audioCtx.resume();
            } catch (e) {}
        }

        function playNewOrderSound() {
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const now = audioCtx.currentTime;
                [880, 1174.66].forEach((freq, i) => {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.type = 'sine'; osc.frequency.value = freq;
                    const t0 = now + i * 0.16;
                    gain.gain.setValueAtTime(0.0001, t0);
                    gain.gain.exponentialRampToValueAtTime(0.35, t0 + 0.02);
                    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.28);
                    osc.connect(gain); gain.connect(audioCtx.destination);
                    osc.start(t0); osc.stop(t0 + 0.3);
                });
            } catch (e) {}
        }

        async function pollLatestOrder() {
            try {
                const res = await fetch('/api/orders/latest');
                if (!res.ok) return;
                const data = await res.json();
                if (lastOrderId === null) { lastOrderId = data.latest_id; return; }
                if (data.latest_id && data.latest_id !== lastOrderId) {
                    lastOrderId = data.latest_id;
                    playNewOrderSound();
                    showToast(`🆕 Жаңа тапсырыс түсті: ${data.latest_id}`, 'success');
                    const activeView = document.getElementById('view-orders');
                    if (activeView && !activeView.classList.contains('hidden')) loadOrders('active');
                    if (!document.getElementById('view-dashboard').classList.contains('hidden')) fetchAnalytics();
                }
            } catch (e) {}
        }

        function startOrderPolling() {
            if (orderPollTimer) clearInterval(orderPollTimer);
            pollLatestOrder();
            orderPollTimer = setInterval(pollLatestOrder, 7000);
        }

        // --- ОРТАҚ ЧАТ ---
        function renderChatMessages(msgs, replace) {
            const box = document.getElementById('chat-messages');
            const atBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 30;
            const html = msgs.map(m => `
                <div class="flex flex-col ${m.username === (window.currentUsername||'') ? 'items-end' : 'items-start'}">
                    <div class="max-w-[80%] ${m.username === (window.currentUsername||'') ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'} px-3 py-2 rounded-2xl">
                        <div class="text-[10px] font-bold opacity-70 mb-0.5">${m.name}</div>
                        <div>${m.message.replace(/</g,'&lt;')}</div>
                    </div>
                    <div class="text-[9px] text-slate-400 mt-0.5">${m.time}</div>
                </div>`).join('');
            if (replace) box.innerHTML = html; else box.insertAdjacentHTML('beforeend', html);
            if (msgs.length && (replace || atBottom)) box.scrollTop = box.scrollHeight;
        }

        async function loadChatMessages(initial) {
            try {
                const res = await fetch(`/api/chat/messages?after_id=${initial ? 0 : lastChatId}`);
                if (!res.ok) return;
                const data = await res.json();
                if (data.length) {
                    lastChatId = data[data.length - 1].id;
                    renderChatMessages(data, initial);
                } else if (initial) {
                    document.getElementById('chat-messages').innerHTML = '<div class="text-center text-slate-500 py-6">Хабарламалар жоқ. Алғашқы болып жазыңыз!</div>';
                }
            } catch (e) {}
        }

        function startChatPolling() {
            if (chatPollTimer) clearInterval(chatPollTimer);
            chatPollTimer = setInterval(() => loadChatMessages(false), 3000);
        }
        function stopChatPolling() {
            if (chatPollTimer) { clearInterval(chatPollTimer); chatPollTimer = null; }
        }

        async function sendChatMessage(e) {
            e.preventDefault();
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            const res = await fetch('/api/chat/messages', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ message: text }) });
            const data = await res.json();
            if (data.success) { await loadChatMessages(false); } else { showToast(data.message || 'Қате!', 'error'); input.value = text; }
        }

        if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) document.documentElement.classList.add('dark');
        function toggleTheme() { const isDark = document.documentElement.classList.toggle('dark'); localStorage.setItem('theme', isDark ? 'dark' : 'light'); }

        function showToast(msg, type = 'success') {
            const t = document.getElementById('toast');
            t.innerText = msg; t.className = `fixed top-5 right-5 z-[110] px-6 py-3 rounded-xl shadow-2xl toast font-medium text-white ${type === 'error' ? 'bg-red-500' : 'bg-emerald-500'}`;
            t.classList.remove('hidden'); setTimeout(() => t.classList.add('hidden'), 3000);
        }
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-mobile'); }

        function navigate(view) {
            ['dashboard', 'orders', 'accounting', 'inventory', 'clients', 'users', 'cash', 'logs', 'profile', 'chat'].forEach(v => { const el = document.getElementById('view-'+v); if(el) el.classList.add('hidden'); });
            document.getElementById('view-'+view).classList.remove('hidden');
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('bg-indigo-50', 'dark:bg-indigo-600/20', 'text-indigo-600', 'dark:text-white'));
            event.target.closest('.nav-btn').classList.add('bg-indigo-50', 'dark:bg-indigo-600/20', 'text-indigo-600', 'dark:text-white');
            if (window.innerWidth < 768) document.getElementById('sidebar').classList.add('sidebar-mobile');
            if (view === 'dashboard') fetchAnalytics();
            if (view === 'orders') loadOrders('active');
            if (view === 'accounting') loadAccounting();
            if (view === 'inventory') loadInventory();
            if (view === 'clients') loadClients();
            if (view === 'users') loadUsers();
            if (view === 'cash') loadShiftStatus();
            if (view === 'logs') loadLogs();
            if (view === 'chat') { loadChatMessages(true); startChatPolling(); } else { stopChatPolling(); }
        }

        async function init() {
            const res = await fetch('/api/auth/me'); const data = await res.json();
            if (data.logged_in) {
                currentRole = data.user.role;
                window.currentUsername = data.user.username;
                unlockAudio();
                startOrderPolling();
                document.getElementById('auth-container').classList.add('hidden');
                document.getElementById('app-container').classList.remove('hidden');
                document.getElementById('user-display-name').innerText = data.user.name;
                document.getElementById('user-avatar').innerText = data.user.name.charAt(0).toUpperCase();
                
                const roleNames = { 'admin': '👑 Әкімші', 'subadmin': '📝 Кіші әкімші', 'master_cart': '🔧 Мастер (Картридж)', 'master_repair': '🖥️ Мастер (Ремонт)', 'accountant': '💼 Бухгалтер' };
                document.getElementById('user-display-role').innerText = roleNames[currentRole];

                document.getElementById('nav-orders').classList.toggle('hidden', currentRole === 'accountant');
                document.getElementById('nav-inventory').classList.toggle('hidden', currentRole === 'accountant' || currentRole === 'subadmin');
                
                if (currentRole === 'admin' || currentRole === 'accountant') document.getElementById('nav-accounting').classList.remove('hidden');
                if (currentRole === 'admin' || currentRole === 'accountant') document.getElementById('nav-clients').classList.remove('hidden');
                
                if (currentRole === 'admin') {
                    document.getElementById('nav-users').classList.remove('hidden');
                    document.getElementById('nav-cash').classList.remove('hidden');
                    document.getElementById('nav-logs').classList.remove('hidden');
                    document.getElementById('add-order-btn').classList.remove('hidden');
                    document.getElementById('export-btn').classList.remove('hidden');
                    document.getElementById('inv-action-th').classList.remove('hidden');
                } else if (currentRole === 'subadmin') {
                    document.getElementById('add-order-btn').classList.remove('hidden');
                }

                document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
                if(currentRole === 'accountant') {
                    document.getElementById('view-accounting').classList.remove('hidden');
                    document.getElementById('nav-accounting').classList.add('bg-indigo-50', 'dark:bg-indigo-600/20', 'text-indigo-600', 'dark:text-white');
                    await loadAccounting();
                } else {
                    document.getElementById('view-dashboard').classList.remove('hidden');
                    document.querySelector('.nav-btn').classList.add('bg-indigo-50', 'dark:bg-indigo-600/20', 'text-indigo-600', 'dark:text-white');
                    await fetchAnalytics();
                }
            } else {
                document.getElementById('auth-container').classList.remove('hidden');
            }
        }

        async function handleLogin(e) {
            e.preventDefault();
            unlockAudio();
            const res = await fetch('/api/auth/login', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ username: loginUsername.value, password: loginPassword.value }) });
            const data = await res.json(); if (data.success) { await init(); } else { showToast(data.message, 'error'); }
        }
        async function handleLogout() { await fetch('/api/auth/logout', {method:'POST'}); location.reload(); }

        async function changePassword(e) {
            e.preventDefault();
            const res = await fetch('/api/auth/password', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ old_password: oldPass.value, new_password: newPass.value }) });
            const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error');
            if(data.success) { oldPass.value=''; newPass.value=''; }
        }

        async function fetchAnalytics() {
            const res = await fetch('/api/analytics'); const data = await res.json();
            const grid = document.getElementById('dashboard-widgets');
            if (data.type === 'global') {
                grid.innerHTML = `
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800"><p class="text-[11px] text-slate-500">Түсім (Айлық)</p><p class="text-xl font-bold text-emerald-500 mt-1">${data.total_revenue.toLocaleString()} ₸</p></div>
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800"><p class="text-[11px] text-slate-500">Жалпы Заказ</p><p class="text-xl font-bold text-slate-900 dark:text-white mt-1">${data.total_orders}</p></div>
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800"><p class="text-[11px] text-slate-500">Аяқталған</p><p class="text-xl font-bold text-indigo-500 mt-1">${data.done_orders}</p></div>
                    <div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-2xl border border-red-200 dark:border-red-800/30"><p class="text-[11px] text-red-500">Күтудегі Счеттар</p><p class="text-xl font-bold text-red-500 mt-1">${data.pending_invoices_sum.toLocaleString()} ₸</p><p class="text-[10px] text-red-400">${data.pending_invoices_count} шт</p></div>`;
            } else {
                grid.innerHTML = `
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800"><p class="text-[11px] text-slate-500">Менің заказдарым</p><p class="text-xl font-bold text-slate-900 dark:text-white mt-1">${data.my_total}</p></div>
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800"><p class="text-[11px] text-slate-500">Процесте</p><p class="text-xl font-bold text-amber-500 mt-1">${data.my_active}</p></div>
                    <div class="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 col-span-2"><p class="text-[11px] text-slate-500">Мен бітіргендер</p><p class="text-xl font-bold text-emerald-500 mt-1">${data.my_done} 💎</p></div>`;
            }
            const dayNames = ['Жс','Дс','Сс','Ср','Бс','Жм','Сб'];
            const maxW = Math.max(...data.weekly, 1);
            const totalWeekly = data.weekly.reduce((a,b) => a+b, 0);
            document.getElementById('weekly-total').textContent = totalWeekly > 0 ? `Барлығы: ${totalWeekly}` : '';
            const todayDate = new Date();
            document.getElementById('weekly-chart').innerHTML = data.weekly.map((c, idx) => {
                const d = new Date(todayDate); d.setDate(todayDate.getDate() - (6 - idx));
                const label = dayNames[d.getDay()];
                const heightPct = c > 0 ? Math.max((c / maxW) * 100, 8) : 2;
                return `<div class="bar-col" title="${label}: ${c} тапсырыс">
                    <div class="bar" style="height: ${heightPct}%">${c > 0 ? `<span class="bar-label">${c}</span>` : ''}</div>
                    <span class="bar-day">${label}</span>
                </div>`;
            }).join('');

            const kpiCard = document.getElementById('kpi-card');
            if (data.type === 'global' && data.masters_kpi && data.masters_kpi.length) {
                kpiCard.classList.remove('hidden');
                const maxDone = Math.max(...data.masters_kpi.map(m => m.done_count), 1);
                const medals = ['🥇', '🥈', '🥉'];
                document.getElementById('masters-kpi').innerHTML = data.masters_kpi.slice(0, 6).map((m, idx) => `
                    <div class="kpi-row">
                        <span class="text-sm w-5 text-center shrink-0">${medals[idx] || (idx + 1)}</span>
                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between text-[11px] mb-1"><span class="font-bold text-slate-700 dark:text-slate-200 truncate">${m.master}</span><span class="font-bold text-indigo-500 shrink-0">${m.done_count}</span></div>
                            <div class="kpi-track"><div class="kpi-fill" style="width: ${(m.done_count / maxDone) * 100}%"></div></div>
                        </div>
                    </div>`).join('');
            } else {
                kpiCard.classList.add('hidden');
            }
        }

        async function loadOrders(filter = 'active') {
            const res = await fetch(`/api/orders?filter=${filter}&search=${document.getElementById('search-input').value}`); 
            if (!res.ok) return; allOrdersCache = await res.json(); renderOrders();
        }

        function renderOrders() {
            const tbody = document.getElementById('orders-tbody');
            if(allOrdersCache.length === 0) { tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-slate-500">Заказдар жоқ</td></tr>'; return; }
            tbody.innerHTML = allOrdersCache.map(o => {
                let cleanPhone = o.phone.replace(/\D/g, ''); if (cleanPhone.startsWith('8')) cleanPhone = '7' + cleanPhone.slice(1);
                let payBadge = o.pay_type === 'Счет' ? `<span class="text-[10px] text-purple-500 mt-1 block">Счет ${o.invoice_status ? '('+o.invoice_status+')' : ''}</span>` : `<span class="text-[10px] text-emerald-500 mt-1 block">Наличка</span>`;
                return `<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer" onclick="viewDetails('${o.id}')">
                    <td class="p-3 font-bold text-indigo-500">${o.id}</td>
                    <td class="p-3"><div class="font-medium text-slate-900 dark:text-white">${o.device}</div><div class="text-[10px] text-slate-500">${o.type}</div></td>
                    <td class="p-3"><a href="https://wa.me/${cleanPhone}" target="_blank" class="text-emerald-500 hover:underline flex items-center gap-1 font-medium" onclick="event.stopPropagation()">💬 ${o.client}</a></td>
                    <td class="p-3 font-bold text-slate-700 dark:text-slate-200">${o.price} ₸ ${payBadge}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${o.status === 'Дайын' ? 'bg-emerald-500/10 text-emerald-500' : (o.status === 'Жаңа' ? 'bg-blue-500/10 text-blue-500' : 'bg-amber-500/10 text-amber-500')}">${o.status}</span></td>
                    <td class="p-3 text-right" onclick="event.stopPropagation()">
                        ${o.status === 'Жаңа' ? `<button onclick="changeStatus('${o.id}', 'Жұмыс істеп жатыр')" class="bg-amber-600 text-white text-[10px] px-2 py-1 rounded-lg font-bold mb-1">▶ Бастау</button>` : ''}
                        ${o.status === 'Жұмыс істеп жатыр' ? `<button onclick="changeStatus('${o.id}', 'Дайын')" class="bg-emerald-600 text-white text-[10px] px-2 py-1 rounded-lg font-bold mb-1">✓ Дайын</button>` : ''}
                    </td>
                </tr>`;
            }).join('');
        }

        async function viewDetails(id) {
            const o = allOrdersCache.find(x => x.id === id); if(!o) return;
            const cleanPhone = o.phone.replace(/\D/g, '').startsWith('8') ? '7' + o.phone.replace(/\D/g, '').slice(1) : o.phone.replace(/\D/g, '');
            const waText = encodeURIComponent(`Сәлеметсіз бе, ${o.client}! Сіздің ${o.id} номерлі заказыңыз дайын. (Januya Service)`);
            
            document.getElementById('details-content').innerHTML = `
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">ID / Күні:</span><span class="text-slate-900 dark:text-white">${o.id} | ${o.date}</span></div>
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">Клиент:</span><span class="text-slate-900 dark:text-white">${o.client}</span></div>
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">Телефон:</span><a href="https://wa.me/${cleanPhone}?text=${waText}" target="_blank" class="text-emerald-500">💬 ${o.phone}</a></div>
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">Құрылғы:</span><span class="text-slate-900 dark:text-white">${o.device}</span></div>
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">Бағасы / Төлем:</span><span class="text-slate-900 dark:text-white">${o.price} ₸ (${o.pay_type}) ${o.invoice_status ? '- '+o.invoice_status : ''}</span></div>
                <div class="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2"><span class="text-slate-500">Статус:</span><span class="text-slate-900 dark:text-white">${o.status}</span></div>
            `;
            const hRes = await fetch(`/api/orders/${id}/logs`); const hData = await hRes.json();
            document.getElementById('details-history').innerHTML = hData.map(l => `<div class="flex gap-2"><span class="text-indigo-500">●</span><div><span class="font-medium">${l.user}</span> <span class="text-slate-500">${l.action}</span><div class="text-[10px] text-slate-400">${l.time}</div></div></div>`).join('');
            
            let actionBtns = '';
            if(o.status !== 'Дайын' && o.status !== 'Бас тартылды') actionBtns += `<button onclick="changeStatus('${o.id}', 'Дайын'); closeModal('modal-details')" class="flex-1 bg-emerald-600 text-white py-2 rounded-lg text-xs">✓ Дайын ету</button>`;
            actionBtns += `<a href="https://wa.me/${cleanPhone}?text=${waText}" target="_blank" class="flex-1 bg-green-600 text-white py-2 rounded-lg text-xs text-center">💬 WhatsApp</a>`;
            if(currentRole === 'admin' || currentRole === 'subadmin') actionBtns += `<button onclick="openEditModal('${o.id}')" class="flex-1 bg-indigo-600 text-white py-2 rounded-lg text-xs">✏️ Өзгерту</button>`;
            document.getElementById('details-actions').innerHTML = actionBtns;
            document.getElementById('modal-details').classList.remove('hidden');
        }

        // --- ҚЫЗМЕТКЕРЛЕРДІ БАСҚАРУ ---
        async function loadUsers() {
            const res = await fetch('/api/users'); const data = await res.json();
            const roleColors = { 'admin': 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400', 'subadmin': 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400', 'master_cart': 'bg-sky-100 text-sky-600 dark:bg-sky-500/20 dark:text-sky-400', 'master_repair': 'bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400', 'accountant': 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400' };
            const roleNames = { 'admin': 'Админ', 'subadmin': 'Кіші админ', 'master_cart': 'Мастер (Картридж)', 'master_repair': 'Мастер (Ремонт)', 'accountant': 'Бухгалтер' };
            
            document.getElementById('users-tbody').innerHTML = data.map(u => `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td class="p-3 font-medium text-slate-900 dark:text-white">${u.name}</td>
                    <td class="p-3 text-slate-500 font-mono">${u.username}</td>
                    <td class="p-3">
                        <select onchange="updRole('${u.username}', this.value)" class="bg-transparent text-xs px-2 py-1 rounded ${roleColors[u.role]} border-0 focus:outline-none cursor-pointer">
                            <option value="admin" ${u.role==='admin'?'selected':''}>Админ</option>
                            <option value="subadmin" ${u.role==='subadmin'?'selected':''}>Кіші админ</option>
                            <option value="master_cart" ${u.role==='master_cart'?'selected':''}>Мастер (Картридж)</option>
                            <option value="master_repair" ${u.role==='master_repair'?'selected':''}>Мастер (Ремонт)</option>
                            <option value="accountant" ${u.role==='accountant'?'selected':''}>Бухгалтер</option>
                        </select>
                    </td>
                    <td class="p-3 text-right flex gap-2 justify-end">
                        <button onclick="resetPass('${u.username}')" class="text-amber-500 hover:text-amber-700 text-[10px] px-2 py-1 rounded-lg bg-amber-500/10">🔑 Құпиясөз</button>
                        ${u.username !== 'admin' ? `<button onclick="delUser('${u.username}')" class="text-red-500 hover:text-red-700 text-[10px] px-2 py-1 rounded-lg bg-red-500/10">Өшіру</button>` : ''}
                    </td>
                </tr>
            `).join('');
        }
        function openAddUserModal() { document.getElementById('modal-user').classList.remove('hidden'); }
        async function submitUser(e) {
            e.preventDefault();
            const res = await fetch('/api/users', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name: usrName.value, username: usrUsername.value, password: usrPassword.value, role: usrRole.value }) });
            const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error');
            if(data.success) { closeModal('modal-user'); document.getElementById('modal-user').querySelector('form').reset(); loadUsers(); }
        }
        async function updRole(username, role) { await fetch(`/api/users/${username}/role`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({role})}); showToast('Рөл өзгертілді!'); }
        async function resetPass(username) {
            const newPass = prompt(`"${username}" үшін жаңа құпиясөзді енгізіңіз:`);
            if(newPass) { const res = await fetch(`/api/users/${username}/password`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({password: newPass})}); const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error'); }
        }
        async function delUser(username) { if(confirm('Қызметкерді өшіргіңіз келе ме?')) { await fetch(`/api/users/${username}`, {method:'DELETE'}); showToast('Қызметкер өшірілді!'); loadUsers(); } }

        // --- БУХГАЛТЕРИЯ ---
        async function loadAccounting() {
            const res = await fetch('/api/accounting/pending'); const data = await res.json();
            const tbody = document.getElementById('accounting-tbody');
            if(data.length === 0) { tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-500">Күтудегі счеттар жоқ!</td></tr>'; return; }
            tbody.innerHTML = data.map(o => `<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40"><td class="p-3 font-bold text-indigo-500">${o.id}</td><td class="p-3 text-slate-900 dark:text-white">${o.client}</td><td class="p-3 text-slate-600 dark:text-slate-300">${o.device}</td><td class="p-3 font-bold text-amber-500">${o.price} ₸</td><td class="p-3 text-right"><button onclick="payInvoice('${o.id}')" class="bg-emerald-600 text-white text-[10px] px-3 py-1.5 rounded-lg font-bold">✓ Төленді</button></td></tr>`).join('');
        }
        async function payInvoice(id) { const res = await fetch(`/api/orders/${id}/pay-invoice`, {method:'POST'}); const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error'); if(data.success) { loadAccounting(); fetchAnalytics(); } }

        function openEditModal(id) {
            const o = allOrdersCache.find(x => x.id === id); if(!o) return;
            closeModal('modal-details');
            editId.value = o.id; editType.value = o.type; editClient.value = o.client; editPhone.value = o.phone; editDevice.value = o.device;
            editPrice.value = o.price; editPaytype.value = o.pay_type; editNotes.value = o.notes;
            document.getElementById('modal-edit').classList.remove('hidden');
        }
        async function submitEdit(e) {
            e.preventDefault();
            const res = await fetch(`/api/orders/${editId.value}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ type: editType.value, client: editClient.value, phone: editPhone.value, device: editDevice.value, price: editPrice.value, pay_type: editPaytype.value, notes: editNotes.value }) });
            const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error');
            if(data.success) { closeModal('modal-edit'); await loadOrders('active'); }
        }
        async function changeStatus(id, status) {
            const res = await fetch(`/api/orders/${id}/status`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status}) });
            if(res.ok) { showToast('Статус жаңартылды!'); await loadOrders('active'); await fetchAnalytics(); } else { showToast('Рұқсат жоқ!', 'error'); }
        }

        let inventoryCache = [];
        async function loadInventory() {
            const res = await fetch('/api/inventory'); inventoryCache = await res.json();
            const tbody = document.getElementById('inventory-tbody');
            tbody.innerHTML = inventoryCache.map(i => `<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40"><td class="p-3 font-medium text-slate-900 dark:text-white">${i.name}</td><td class="p-3"><span class="font-bold ${i.qty <= i.min_qty ? 'text-red-500' : 'text-emerald-500'}">${i.qty} шт</span></td><td class="p-3 text-right hidden" id="inv-action-${i.id}"><button onclick="openEditInv(${i.id})" class="bg-indigo-600 text-white text-[10px] px-2 py-1 rounded-lg">✏️ Өзгерту</button></td></tr>`).join('');
            if(currentRole === 'admin') document.querySelectorAll('[id^="inv-action-"]').forEach(el => el.classList.remove('hidden'));
        }
        async function openEditInv(id) {
            const i = inventoryCache.find(x=>x.id===id); if(!i) return;
            const newQty = prompt(`"${i.name}" жаңа қалдық мөлшерін енгізіңіз:`, i.qty);
            if(newQty !== null) { await fetch(`/api/inventory/${id}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({qty: newQty, min_qty: i.min_qty}) }); showToast('Склад жаңартылды!'); loadInventory(); }
        }
        function openAddInvModal() {
            document.getElementById('modal-inv-add').querySelector('form').reset();
            document.getElementById('modal-inv-add').classList.remove('hidden');
        }
        async function submitInvAdd(e) {
            e.preventDefault();
            const payload = { name: invName.value.trim(), qty: invQty.value, min_qty: invMinQty.value };
            const res = await fetch('/api/inventory', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
            const data = await res.json();
            showToast(data.message, data.success ? 'success' : 'error');
            if (data.success) { closeModal('modal-inv-add'); await loadInventory(); }
        }

        async function loadClients() {
            const res = await fetch('/api/clients'); const data = await res.json();
            document.getElementById('clients-tbody').innerHTML = data.map(c => `<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40"><td class="p-3 font-medium text-slate-900 dark:text-white">${c.client}</td><td class="p-3"><a href="https://wa.me/${c.phone.replace(/\\D/g, '').startsWith('8') ? '7' + c.phone.replace(/\\D/g, '').slice(1) : c.phone.replace(/\\D/g, '')}" target="_blank" class="text-emerald-500">💬 ${c.phone}</a></td><td class="p-3"><span class="bg-indigo-500/10 text-indigo-500 px-2 py-0.5 rounded text-xs font-bold">${c.visits} рет</span></td><td class="p-3 font-bold text-emerald-500">${c.total_spent || 0} ₸</td></tr>`).join('');
        }
        async function loadShiftStatus() {
            const res = await fetch('/api/cash/shift/status'); const data = await res.json(); const box = document.getElementById('shift-status-box');
            if(data.is_open) { box.innerHTML = `<div class="text-emerald-500 font-bold text-lg">● Ауысым Ашық</div><div class="text-slate-500">Касса: ${data.shift.start_cash} ₸</div><input id="shift-close-cash" type="number" placeholder="Нақты ақша" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white mt-2"><button onclick="closeShift()" class="w-full bg-rose-600 text-white py-2 rounded-xl font-bold mt-2">Ауысымды жабу</button>`; } 
            else { box.innerHTML = `<div class="text-amber-500 font-bold text-lg">○ Ауысым Жабық</div><input id="shift-open-cash" type="number" placeholder="Бастапқы ақша" class="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white mt-2"><button onclick="openShift()" class="w-full bg-emerald-600 text-white py-2 rounded-xl font-bold mt-2">Ауысымды ашу</button>`; }
        }
        async function openShift() { await fetch('/api/cash/shift/open', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({start_cash: document.getElementById('shift-open-cash').value})}); await loadShiftStatus(); }
        async function closeShift() { const res = await fetch('/api/cash/shift/close', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({end_cash_actual: document.getElementById('shift-close-cash').value})}); const data = await res.json(); showToast(`Ауысым жабылды! Айырмашылық: ${data.diff} ₸`); await loadShiftStatus(); }
        async function loadLogs() { const res = await fetch('/api/logs'); const data = await res.json(); document.getElementById('logs-container').innerHTML = data.map(l => `<div class="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-2 text-xs"><span><b class="text-slate-900 dark:text-white">${l.user}</b> <span class="text-slate-500">${l.action}</span></span><span class="text-slate-400">${l.time}</span></div>`).join(''); }

        function openNewOrderModal() { document.getElementById('modal-order').classList.remove('hidden'); }
        function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
        async function submitOrder(e) {
            e.preventDefault();
            const res = await fetch('/api/orders', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ type: ordType.value, client: ordClient.value, phone: ordPhone.value, device: ordDevice.value, serial_num: ordSn.value, price: ordPrice.value, pay_type: ordPaytype.value, notes: ordNotes.value }) });
            const data = await res.json(); showToast(data.message, data.success ? 'success' : 'error');
            if(data.success) { closeModal('modal-order'); document.getElementById('form-order').reset(); await loadOrders('active'); await fetchAnalytics(); }
        }
        function exportToExcel() { window.location.href = '/api/orders/export'; }

        // --- PWA: "БАСТЫ БЕТКЕ ҚОСУ" АВТОМАТТЫ СҰРАУЫ ---
        let deferredInstallPrompt = null;
        function isStandaloneMode() {
            return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
        }
        function isIosDevice() {
            return /iphone|ipad|ipod/i.test(window.navigator.userAgent) && !window.MSStream;
        }
        function wasInstallDismissedRecently() {
            const ts = localStorage.getItem('installDismissedAt');
            if (!ts) return false;
            return (Date.now() - parseInt(ts, 10)) < 7 * 24 * 60 * 60 * 1000;
        }
        function showInstallPrompt(iosMode) {
            const box = document.getElementById('install-prompt');
            if (!box) return;
            box.querySelector('p').textContent = iosMode
                ? 'Safari-де төмендегі Бөлісу 📤 батырмасынан "Басты бетке қосу" таңдаңыз.'
                : 'Программа ретінде жылдам ашыңыз.';
            document.getElementById('install-btn').classList.toggle('hidden', iosMode);
            document.getElementById('close-install').textContent = iosMode ? 'Түсінікті' : 'Жоқ';
            box.classList.remove('hidden');
        }
        function setupInstallPrompt() {
            if (isStandaloneMode() || wasInstallDismissedRecently()) return;
            if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});

            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                deferredInstallPrompt = e;
                showInstallPrompt(false);
            });
            window.addEventListener('appinstalled', () => document.getElementById('install-prompt').classList.add('hidden'));

            document.getElementById('install-btn').addEventListener('click', async () => {
                document.getElementById('install-prompt').classList.add('hidden');
                if (!deferredInstallPrompt) return;
                deferredInstallPrompt.prompt();
                try { await deferredInstallPrompt.userChoice; } catch (e) {}
                deferredInstallPrompt = null;
            });
            document.getElementById('close-install').addEventListener('click', () => {
                document.getElementById('install-prompt').classList.add('hidden');
                localStorage.setItem('installDismissedAt', Date.now().toString());
            });

            if (isIosDevice()) setTimeout(() => { if (!isStandaloneMode()) showInstallPrompt(true); }, 2500);
        }

        window.onload = () => { init(); setupInstallPrompt(); };
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)