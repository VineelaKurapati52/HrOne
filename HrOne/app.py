import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash




app = Flask(__name__)
app.secret_key = 'super_secret_session_key_change_this_in_production'
DB_FILE = 'database.db'




def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User'
        )
    ''')
    conn.commit()
   
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        admin_pass = generate_password_hash('admin123')
        user_pass = generate_password_hash('user123')
        conn.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                     ('admin', admin_pass, 'admin@example.com', 'Admin'))
        conn.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                     ('user', user_pass, 'user@example.com', 'User'))
        conn.commit()
    conn.close()


init_db()


# --- ROUTES & AUTHENTICATION ---


@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
       
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
       
        from werkzeug.security import check_password_hash
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
           
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- ADMIN ACTIONS ---


@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
       
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users)


@app.route('/admin/add', methods=['POST'])
def admin_add_user():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))
       
    username = request.form['username']
    email = request.form['email']
    from werkzeug.security import generate_password_hash
    password = generate_password_hash(request.form['password'])
    role = request.form['role']
   
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                     (username, password, email, role))
        conn.commit()
        flash('User added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Username already exists!', 'danger')
    finally:
        conn.close()
       
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit/<int:id>', methods=['POST'])
def admin_edit_user(id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))
       
    username = request.form['username']
    email = request.form['email']
    role = request.form['role']
   
    conn = get_db_connection()
    conn.execute('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?', (username, email, role, id))
    conn.commit()
    conn.close()
    flash('User updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:id>')
def admin_delete_user(id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('index'))
       
    if id == session['user_id']:
        flash('You cannot delete your own session!', 'danger')
        return redirect(url_for('admin_dashboard'))
       
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# --- USER ACTIONS ---


@app.route('/user')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
       
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('user_dashboard.html', user=user)


@app.route('/user/update', methods=['POST'])
def user_update():
    if 'user_id' not in session:
        return redirect(url_for('login'))
       
    email = request.form['email']
    conn = get_db_connection()
    conn.execute('UPDATE users SET email = ? WHERE id = ?', (email, session['user_id']))
    conn.commit()
    conn.close()
    flash('Profile updated!', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/user/reset-password', methods=['POST'])
def user_reset_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
       
    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(request.form['password'])
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, session['user_id']))
    conn.commit()
    conn.close()
    flash('Password updated successfully!', 'success')
    return redirect(url_for('user_dashboard'))






if __name__ == '__main__':
    print("\n" + "═"*60)
    print(" 🚀 FIXED RUNTIME MULTI-USER ENGINE STARTING...")
    print(" 👉 ADDRESS LOCATION: http://127.0.0.1:5000")
    print("═"*60 + "\n")
   
    app.run(debug=True, port=4000)
