import os
import requests
from flask import Flask, request, render_template, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 数据库连接参数
db_host = "XX.XX.XX.XX"
db_port = "5432"
db_name = "testdb"
db_user = "joe"
db_password = "NewPassword123!"

def get_db_connection():
    conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_password)
    return conn

def ensure_schema_exists():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("CREATE SCHEMA IF NOT EXISTS chatgpt")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chatgpt.users (
                u_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                api_url VARCHAR(255),
                api_key VARCHAR(255)
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error ensuring schema exists: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def send_to_gpt(api_url, api_key, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 3000
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code != 200:
        return f"Error: API request failed with status code {response.status_code}\nResponse: {response.text}"
    response_json = response.json()
    if 'choices' not in response_json:
        return f"Error: 'choices' not found in response JSON\nResponse JSON: {response_json}"
    return response_json['choices'][0]['message']['content']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO chatgpt.users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username already exists. Please choose a different one.', 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM chatgpt.users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['u_id']
            session['username'] = user['username']
            if user['api_url'] and user['api_key']:
                flash('Login successful!', 'success')
                return redirect(url_for('chat'))
            else:
                flash('Login successful! Please set your API URL and Key.', 'success')
                return redirect(url_for('set_api'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/set_api', methods=['GET', 'POST'])
def set_api():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        api_url = request.form['api_url']
        api_key = request.form['api_key']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE chatgpt.users SET api_url = %s, api_key = %s WHERE u_id = %s", (api_url, api_key, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        flash('API settings saved!', 'success')
        return redirect(url_for('chat'))

    return render_template('set_api.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT api_url, api_key FROM chatgpt.users WHERE u_id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if request.method == 'POST':
        user_input = request.form['user_input']
        messages = [{"role": "system", "content": "你是一个经验丰富的助手。"}, {"role": "user", "content": user_input}]
        response = send_to_gpt(user['api_url'], user['api_key'], messages)
        return render_template('chat.html', response=response)

    return render_template('chat.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    ensure_schema_exists()
    app.run(host='0.0.0.0', port=5000, debug=True)