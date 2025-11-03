from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from collections import defaultdict
import requests
from datetime import datetime
import os
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret")


# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    url = f"{SUPABASE_URL}/rest/v1/staff?id=eq.{user_id}&select=id,username,password_hash"
    res = requests.get(url, headers=headers).json()
    if res:
        user = res[0]
        return User(user['id'], user['username'], user['password_hash'])
    return None

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        url = f"{SUPABASE_URL}/rest/v1/staff?username=eq.{username}&select=id,username,password_hash"
        res = requests.get(url, headers=headers).json()
        if res and check_password_hash(res[0]['password_hash'], password):
            login_user(User(res[0]['id'], res[0]['username'], res[0]['password_hash']))
            return redirect('/')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/add-cow', methods=['GET', 'POST'])
@login_required
def add_cow():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "breed": request.form['breed'],
            "age": int(request.form['age']),
            "health_status": request.form['health']
        }
        url = f"{SUPABASE_URL}/rest/v1/cows"
        requests.post(url, headers=headers, json=data)
        return redirect('/cows')
    return render_template('add_cow.html')

@app.route('/cows')
@login_required
def cows():
    query = request.args.get('query')
    url = f"{SUPABASE_URL}/rest/v1/cows"
    if query:
        url += f"?or=(name.ilike.*{query}*,breed.ilike.*{query}*)"
    res = requests.get(url, headers=headers).json()
    return render_template('cows.html', cows=res)

@app.route('/add-milk-log', methods=['GET', 'POST'])
@login_required
def add_milk_log():
    cows = requests.get(f"{SUPABASE_URL}/rest/v1/cows?select=id,name", headers=headers).json()
    if request.method == 'POST':
        data = {
            "cow_id": int(request.form['cow_id']),
            "date": request.form['date'],
            "quantity_liters": float(request.form['quantity_liters'])
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/milk_logs", headers=headers, json=data)
        return redirect('/milk-logs')
    return render_template('add_milk_log.html', cows=cows)

@app.route('/milk-logs')
@login_required
def milk_logs():
    url = f"{SUPABASE_URL}/rest/v1/milk_logs?select=id,date,quantity_liters,cows(name)&order=date.desc"
    logs = requests.get(url, headers=headers).json()
    return render_template('milk_logs.html', logs=logs)

@app.route('/add-vendor', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        data = {
            "name": request.form['name'],
            "contact": request.form['contact'],
            "village": request.form['village']
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/vendors", headers=headers, json=data)
        return redirect('/vendors')
    return render_template('add_vendor.html')

@app.route('/vendors')
@login_required
def vendors():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/vendors?select=id,name,contact,village", headers=headers).json()
    return render_template('vendors.html', vendors=res)

@app.route('/milk-sheet', methods=['GET', 'POST'])
@login_required
def milk_sheet():
    vendors = requests.get(f"{SUPABASE_URL}/rest/v1/vendors?select=id,name", headers=headers).json()
    if request.method == 'POST':
        date = request.form['date']
        session_time = request.form['session']
        rate = float(request.form['rate'])
        vendor_ids = request.form.getlist('vendor_id')
        milk_litres_list = request.form.getlist('milk_litres')
        percentage_list = request.form.getlist('percentage')

        for vendor_id, litres, perc in zip(vendor_ids, milk_litres_list, percentage_list):
            if not litres.strip() or not perc.strip():
                continue
            litres = float(litres)
            perc = float(perc)
            price = litres * rate * (perc / 10)
            data = {
                "vendor_id": int(vendor_id),
                "date": date,
                "session": session_time,
                "milk_litres": litres,
                "percentage": perc,
                "price": price
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/vendor_milk_sheet", headers=headers, json=data)
        return redirect(url_for('milk_sheet_summary', date=date, session=session_time))
    return render_template('milk_sheet.html', vendors=vendors)

@app.route('/milk-sheet-summary')
@login_required
def milk_sheet_summary():
    date = request.args.get('date')
    session_time = request.args.get('session')
    url = f"{SUPABASE_URL}/rest/v1/vendor_milk_sheet?date=eq.{date}&session=eq.{session_time}&select=id,milk_litres,percentage,price,vendors(name)&order=id.asc"
    logs = requests.get(url, headers=headers).json()
    return render_template('milk_sheet_summary.html', logs=logs, date=date, session=session_time)

@app.route('/vendor-milk-logs', methods=['GET', 'POST'])
@login_required
def vendor_milk_logs():
    vendors = requests.get(f"{SUPABASE_URL}/rest/v1/vendors?select=id,name", headers=headers).json()
    logs_by_date = {}
    summary_by_range = defaultdict(lambda: {'litres': 0, 'price': 0})
    monthly_total = {'litres': 0, 'price': 0}
    selected_vendor_id = None
    selected_month = None

    if request.method == 'POST':
        selected_vendor_id = request.form['vendor_id']
        selected_month = request.form['month']
        year, month = map(int, selected_month.split('-'))

        url = f"{SUPABASE_URL}/rest/v1/vendor_milk_sheet?vendor_id=eq.{selected_vendor_id}&select=date,session,milk_litres,percentage,price&order=date.asc"
        entries = requests.get(url, headers=headers).json()

        for entry in entries:
            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            if entry_date.year != year or entry_date.month != month:
                continue
            date = entry_date.date()
            session = entry['session']
            litres = entry['milk_litres']
            perc = entry['percentage']
            price = entry['price']

            if date not in logs_by_date:
                logs_by_date[date] = {'morning': None, 'evening': None}
            logs_by_date[date][session] = {'litres': litres, 'percentage': perc, 'price': price}

            day = date.day
            bucket = '1–10' if day <= 10 else '11–20' if day <= 20 else '21–end'
            summary_by_range[bucket]['litres'] += litres
            summary_by_range[bucket]['price'] += price
            monthly_total['litres'] += litres
            monthly_total['price'] += price

    return render_template('vendor_milk_logs.html',
                           vendors=vendors,
                           logs_by_date=logs_by_date,
                           summary_by_range=summary_by_range,
                           monthly_total=monthly_total,
                           selected_vendor_id=selected_vendor_id,
                           selected_month=selected_month)

if __name__ == '__main__':

    app.run(debug=True)
