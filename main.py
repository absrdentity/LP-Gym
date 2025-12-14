from flask import Flask, render_template, jsonify, request, url_for, session, flash, redirect
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key  = '!@#$'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'lpgym'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    selected_package = request.args.get('package', '')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        package = request.form['package']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # cek email
        cursor.execute('SELECT id FROM members WHERE email=%s', (email,))
        if cursor.fetchone():
            return render_template(
                'register.html',
                selected_package=selected_package,
                error='Email already registered'
            )

        # membership dates
        start_date = datetime.today().date()
        expiry_date = start_date + timedelta(days=30)

        cursor.execute("""
            INSERT INTO members
            (name, email, password, phone, package,
             membership_start, membership_expiry, attendance_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            name,
            email,
            password,
            phone,
            package,
            start_date,
            expiry_date,
            0
        ))

        mysql.connection.commit()

        # ambil user_id yang baru dibuat
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session.permanent = True

        return redirect(url_for('dashboard'))

    return render_template('register.html', selected_package=selected_package)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if  request.method == 'POST' and all(k in request.form for k in ['email', 'password']):
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('SELECT * FROM members WHERE email = %s', (email,))
        member = cursor.fetchone()

        if not member:
            error_message = 'Email not found'
            return render_template('login.html', error=error_message)
        
        if member['password'] != password:
            error_message = 'Incorrect password. Please try again'
            return render_template('login.html', error=error_message)
        
        session['user_id'] = member['id']
        session.permanent = True
        flash('Login Successful')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/membership', methods=['GET'])
def membership():
    return render_template('membership.html')

@app.route('/upgrade_membership', methods=['GET', 'POST'])
def upgrade_membership(): 
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT * FROM members WHERE id = %s',
        (session['member'],)
    )
    member = cursor.fetchone()

    if request.method == 'POST':
        new_package = request.form['package']
        cursor.execute(
            'UPDATE members SET package = %s WHERE id = %s',
            (new_package, session['member'])
        )
        mysql.connection.commit()

        flash('Membership upgraded successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('upgrade_membership.html', member=member)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT name, email, phone, package,
               membership_expiry,
               attendance_count
        FROM members
        WHERE id=%s
    """, (session['user_id'],))

    user = cursor.fetchone()
    if not user:
        session.pop('user_id')
        return redirect(url_for('login'))

    # Progress calculation
    target = 12
    progress = min(int((user['attendance_count'] / target) * 100), 100)

    return render_template(
        'dashboard.html',
        user=user,
        progress=progress
    )


@app.route('/checkin', methods=['POST'])
def checkin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    today = datetime.today().date()

    # prevent double check-in
    cursor.execute(
        "SELECT * FROM attendance WHERE member_id=%s AND checkin_date=%s",
        (session['user_id'], today)
    )

    if cursor.fetchone():
        flash('You already checked in today!')
        return redirect(url_for('dashboard'))

    cursor.execute(
        "INSERT INTO attendance (member_id, checkin_date) VALUES (%s,%s)",
        (session['user_id'], today)
    )

    cursor.execute(
        "UPDATE members SET attendance_count = attendance_count + 1 WHERE id=%s",
        (session['user_id'],)
    )

    mysql.connection.commit()
    flash('Check-in successful 💪')
    return redirect(url_for('dashboard'))

@app.route('/upgrade_membership', methods=['POST'])
def extend_membership():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT package, membership_expiry
        FROM members
        WHERE id=%s
    """, (session['user_id'],))
    user = cursor.fetchone()

    if not user:
        return redirect(url_for('login'))

    today = datetime.today().date()
    expiry = user['membership_expiry']
    duration_days = PACKAGE_DURATION.get(user['package'].lower(), 30)

    # logic inti
    if expiry and expiry >= today:
        new_expiry = expiry + timedelta(days=duration_days)
    else:
        new_expiry = today + timedelta(days=duration_days)

    cursor.execute("""
        UPDATE members
        SET membership_expiry=%s
        WHERE id=%s
    """, (new_expiry, session['user_id']))

    mysql.connection.commit()
    flash('Membership extended successfully 🎉')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)