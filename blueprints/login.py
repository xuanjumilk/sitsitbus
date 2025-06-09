from flask import Flask, Blueprint, request, jsonify, render_template, session, redirect
import sqlite3
import bcrypt

login_bp = Blueprint('login', __name__)
DB_PATH = 'user.db'

@login_bp.route('/', methods=['GET'])
def show_login_page():
    return render_template("login.html")

@login_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# 連線工具函式
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🔓 使用者登入（若無帳號則自動註冊）
@login_bp.route('/', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user:
        # 有帳號，檢查密碼
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user'] = username
            session['user_id'] = user['id']
            conn.close()
            return jsonify({'message': '✅ 登入成功', 'username': username})
        else:
            conn.close()
            return jsonify({'error': '❌ 帳號或密碼錯誤'}), 401
    else:
        # 沒有帳號，自動註冊
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            # 取得新用戶的 user_id
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id']
                # 新增 bus_skins 預設 skin
                cursor.execute("INSERT INTO bus_skins (user_id, skin_id) VALUES (?, ?)", (user_id, 1))
                conn.commit()
                session['user'] = username
                session['user_id'] = user_id
            conn.close()
            return jsonify({'message': '✅ 註冊成功並自動登入', 'username': username})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': '❌ 註冊失敗，請重試'}), 409

if __name__ == '__main__':
    login_bp.run(debug=True)