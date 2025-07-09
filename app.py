from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['AVATAR_FOLDER'] = os.path.join('static', 'avatars')

socketio = SocketIO(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['AVATAR_FOLDER']):
    os.makedirs(app.config['AVATAR_FOLDER'])

DB_PATH = 'messenger.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            text TEXT,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            filename TEXT
        )''')
        conn.commit()

init_db()

def add_message(user, text, time, type_, filename=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO messages (user, text, time, type, filename) VALUES (?, ?, ?, ?, ?)',
                  (user, text, time, type_, filename))
        conn.commit()

def get_all_messages():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT user, text, time, type, filename FROM messages ORDER BY id ASC')
        return [
            {'user': row[0], 'text': row[1], 'time': row[2], 'type': row[3], 'filename': row[4]}
            for row in c.fetchall()
        ]

def get_avatar_filename(username):
    for ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        fname = secure_filename(username) + '.' + ext
        fpath = os.path.join(app.config['AVATAR_FOLDER'], fname)
        if os.path.exists(fpath):
            return fname
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html', username=session['username'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'username' not in session:
        return jsonify({'success': False}), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    avatar = get_avatar_filename(session['username'])
    msg = {
        'user': session['username'],
        'text': filename,
        'time': datetime.now().strftime('%H:%M'),
        'type': 'file',
        'filename': filename,
        'avatar': avatar
    }
    add_message(msg['user'], msg['text'], msg['time'], msg['type'], msg['filename'])
    socketio.emit('message', msg)
    return jsonify({'success': True, 'filename': filename})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/avatar_upload', methods=['POST'])
def avatar_upload():
    if 'avatar' not in request.files or 'username' not in session:
        return jsonify({'success': False}), 400
    file = request.files['avatar']
    if not file or not file.filename:
        return jsonify({'success': False}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        return jsonify({'success': False, 'error': 'Неверный формат'}), 400
    filename = secure_filename(session['username']) + '.' + ext
    filepath = os.path.join(app.config['AVATAR_FOLDER'], filename)
    file.save(filepath)
    session['avatar'] = filename
    return jsonify({'success': True, 'filename': filename})

@app.route('/avatars/<filename>')
def avatar_file(filename):
    return send_from_directory(app.config['AVATAR_FOLDER'], filename)

@socketio.on('send_message')
def handle_message(data):
    username = session.get('username', 'anon')
    avatar = get_avatar_filename(username)
    msg = {
        'user': username,
        'text': data['text'],
        'time': datetime.now().strftime('%H:%M'),
        'type': 'text',
        'filename': None,
        'avatar': avatar
    }
    add_message(msg['user'], msg['text'], msg['time'], msg['type'], msg['filename'])
    emit('message', msg, broadcast=True)

@socketio.on('join')
def on_join():
    msgs = get_all_messages()
    for m in msgs:
        m['avatar'] = get_avatar_filename(m['user'])
    emit('init_messages', msgs)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 