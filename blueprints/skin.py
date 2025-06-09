from flask import Blueprint, request, jsonify, render_template, session, redirect
import sqlite3

skin_bp = Blueprint('skin', __name__)
DB_PATH = 'user.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
# 取得目前使用者的skin
@skin_bp.route('/get_skin', methods=['GET'])
def get_skin():
    user_id = session.get('user_id', 1)
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        user_id = 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT skin_id FROM bus_skins WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({'skin_id': row['skin_id']})
    else:
        return jsonify({'skin_id': 1})

# 儲存skin
@skin_bp.route('/save_skin', methods=['POST'])
def save_skin():
    user_id = session.get('user_id', 1)
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        user_id = 1
    try:
        skin_id = int(request.json.get('skin_id'))
    except (TypeError, ValueError):
        skin_id = None
    if not user_id or skin_id is None or skin_id <= 0:
        return jsonify({'success': False, 'error': '未登入或資料錯誤'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bus_skins WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE bus_skins SET skin_id = ? WHERE user_id = ?", (skin_id, user_id))
    else:
        cursor.execute("INSERT INTO bus_skins (user_id, skin_id) VALUES (?, ?)", (user_id, skin_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'skin_id': skin_id})