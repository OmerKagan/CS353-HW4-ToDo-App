import re  
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cs353hw4db'
  
mysql = MySQL(app)  

@app.route('/')

@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s AND password = % s', (username, password))
        user = cursor.fetchone()
        if user:              
            session['loggedin'] = True
            session['userid'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return redirect(url_for('tasks'))
        else:
            message = 'Please enter correct username / password !'
    return render_template('login.html', message = message)


@app.route('/register', methods =['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            message = 'Choose a different username!'
  
        elif not username or not password or not email:
            message = 'Please fill out the form!'

        else:
            cursor.execute('INSERT INTO User (password, username, email) VALUES (% s, % s, % s)', (password, username, email))
            mysql.connection.commit()
            message = 'User successfully created!'

    elif request.method == 'POST':

        message = 'Please fill all the fields!'
    return render_template('register.html', message = message)

@app.route('/tasks', methods =['GET', 'POST'])
def tasks():
    user_id = session.get('userid')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'title' in request.form and 'description' in request.form and 'deadline' in request.form and 'task_type' in request.form :
        # get form data
        title = request.form['title']
        description = request.form['description']
        deadline_str = request.form['deadline']
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        deadline = deadline.strftime('%Y-%m-%d %H:%M:%S')
        task_type = request.form['task_type']
        status = 'Todo'
        creation_time = datetime.now()
        creation_time = creation_time.strftime('%Y-%m-%d %H:%M:%S')
        done_time = None        
        cursor.execute('INSERT INTO Task (title, description, status, deadline, creation_time, done_time, user_id, task_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (title, description, status, deadline, creation_time, done_time, user_id, task_type))
        mysql.connection.commit()

    cursor.execute("SELECT * FROM Task WHERE user_id=%s AND status='Todo' ORDER BY deadline ASC", (user_id,))
    taskList = cursor.fetchall()
    cursor.execute("SELECT * FROM Task WHERE user_id=%s AND status='Done' ORDER BY done_time DESC", (user_id,))
    doneList = cursor.fetchall()

    return render_template('tasks.html', taskList = taskList, doneList = doneList)

@app.route('/delete_task', methods=['POST'])
def delete_task():
    task_id = request.form['task_id']    
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM Task WHERE id = %s", (task_id,))
    mysql.connection.commit()

    return redirect(url_for('tasks'))

@app.route('/edit_task', methods=['POST'])
def edit_task():
    task_id = request.form['task_id']

    # Edit algorithm here   

    return redirect(url_for('tasks'))    

@app.route('/done_task', methods=['POST'])
def done_task():
    task_id = request.form['task_id']
    status = "Done"
    done_time = datetime.now()
    done_time = done_time.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE Task SET status=%s, done_time=%s WHERE id = %s", (status, done_time, task_id,))
    mysql.connection.commit()

    return redirect(url_for('tasks'))    

@app.route('/analysis', methods =['GET', 'POST'])
def analysis():
    user_id = session.get('userid')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        return redirect(url_for('analysis'))
    cursor.execute("SELECT title, done_time - deadline AS latency FROM Task WHERE user_id=%s AND status='Done' AND done_time > deadline", (user_id,))
    firstQuery = cursor.fetchall()
    cursor.execute("SELECT AVG(done_time - creation_time) AS avg_completion_time FROM Task WHERE user_id=%s AND status='Done'", (user_id,))
    secondQuery = cursor.fetchall()
    cursor.execute("SELECT TaskType.type, COUNT(*) AS num_of_completed_tasks FROM Task JOIN TaskType ON Task.task_type = TaskType.type WHERE Task.user_id=%s AND Task.status='Done' GROUP BY TaskType.type ORDER BY num_of_completed_tasks DESC", (user_id,))
    thirdQuery = cursor.fetchall()
    cursor.execute("SELECT title, deadline FROM Task WHERE user_id=%s AND status='Todo' ORDER BY deadline ASC", (user_id,))
    fourthQuery = cursor.fetchall()
    cursor.execute("SELECT title, done_time - creation_time AS completion_time FROM Task WHERE user_id=%s AND status='Done' ORDER BY completion_time DESC LIMIT 2", (user_id,))
    fifthQuery = cursor.fetchall()   
    return render_template('analysis.html', firstQuery = firstQuery, secondQuery = secondQuery, thirdQuery = thirdQuery, fourthQuery = fourthQuery, fifthQuery = fifthQuery)


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('userid', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
