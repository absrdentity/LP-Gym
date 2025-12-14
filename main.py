from flask import Flask, render_template, jsonify, request, url_for, session, flash, redirect
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key  = '!@#$'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'lp-gym'

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
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('SELECT * FROM members WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            error_message = 'Email already registered. Please use another email or log in.'
            return render_template('register.html', selected_package=selected_package, error=error_message)

        cursor.execute(
            'INSERT INTO members (name, email, password, phone, package, date) VALUES (%s, %s, %s, %s, %s, %s)',
            (name, email, password, phone, package)
        )
        mysql.connection.commit()

        return redirect(url_for('dashboard.html', name=name, email=email, package=package, phone=phone))
    
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
        
        session['member'] = member['ID']
        session.permanent = True
        flash('Login Successful')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('member', None)
    return redirect(url_for('home'))

@app.route('/membership', methods=['GET'])
def membership():
    return render_template('membership.html')

@app.route('/upgrade_membership', methods=['GET', 'POST'])
def upgrade_membership(): 
    if 'member' not in session:
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

if __name__ == '__main__':
    app.run(debug=True)