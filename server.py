from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
import re, md5

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'[0-9]')
PASS_REGEX = re.compile(r'.*[A-Z].*[0-9]')

app = Flask(__name__)
app.secret_key = "ThisIsSecretadfasdfasdf!"

mysql = MySQLConnector(app,'wall')

@app.route('/')
def index():
    print session
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    input_email = request.form['email']
    input_password = request.form['password']
    email_query = "SELECT * FROM users WHERE email = :email_id"
    query_data = {'email_id': input_email}
    stored_email = mysql.query_db(email_query, query_data)

    if not EMAIL_REGEX.match(request.form['email']):
        flash("Email must be a valid email", 'error')
    if not stored_email:
        flash("User does not exist!")
        return redirect('/')
    else:
        if md5.new(request.form['password']).hexdigest() == stored_email[0]['password']:
            session['user_id'] = stored_email[0]['id']
            return redirect('/wall')
        else:
            flash("Wrong password, try again!")
            return redirect('/')

@app.route('/logoff')
def logoff():
    print session
    if 'user_id' in session:
        session.pop('user_id')
    print session
    return redirect('/')

@app.route('/register', methods=['POST'])
def register_user():
    input_email = request.form['email']
    email_query = "SELECT * FROM users WHERE email = :email_id"
    query_data = {'email_id': input_email}
    stored_email = mysql.query_db(email_query, query_data)

    print request.form
    print request.form['email']
    print session

    for x in request.form:
        if len(request.form[x]) < 1:
            flash(x + " cannot be blank!", 'blank')
    
    if NAME_REGEX.search(request.form['first_name']):
        flash("First name cannot contain any numbers", 'error')

    if NAME_REGEX.search(request.form['last_name']):
        flash("Last name cannot contain any numbers", 'error')

    if len(request.form['password']) < 8:
        flash("Password must be more than 8 characters", 'password')

    if not EMAIL_REGEX.match(request.form['email']):
        flash("Email must be a valid email", 'error')
    
    if not PASS_REGEX.search(request.form['password']):
        flash("Password must have a number and an uppercase letter", 'password')
    
    if request.form['password'] != request.form['confirm_password']:
        flash("Password and Password Confirmation should match", 'password')

    if stored_email:
        flash("This email is not available, it has been TAKEN!")


    if '_flashes' in session:
        return redirect('/')
    else:
        flash("All Good!!!!", 'good')
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email_id, :pass, NOW(), NOW())"
        data = {
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'email_id': request.form['email'],
                'pass': md5.new(request.form['password']).hexdigest()
            }
        #since INSERT returns last row id we set this equal to session to log in
        session['user_id'] = mysql.query_db(query, data)

        flash("This email address you entered " + input_email + " is a valid email address. Thank you!")
        return redirect('/wall')

@app.route('/wall')
def thewall():
    # This displays all the users you have created
    query = "SELECT email, DATE_FORMAT(created_at,'%M %d %Y') as date FROM users"       
    emails = mysql.query_db(query)
    
    id_query = "SELECT * FROM users WHERE id = :user_id"
    query_data = {'user_id': session['user_id']}
    name_query = mysql.query_db(id_query, query_data)

    #displays messages
    query = "SELECT messages.message, DATE_FORMAT(messages.created_at,'%M %d %Y') as date, concat_ws(' ',users.first_name, users.last_name) as fullname, messages.id FROM users join messages on messages.user_id = users.id ORDER BY messages.created_at desc"
    all_messages = mysql.query_db(query)

    #displays comments
    query = "SELECT comments.comment, DATE_FORMAT(comments.created_at,'%M %d %Y') as date, concat_ws(' ',users.first_name, users.last_name) as fullname, comments.message_id FROM users join comments on comments.user_id = users.id ORDER BY comments.created_at"
    all_comments = mysql.query_db(query)

    return render_template('wall.html', email_list = emails, firname = name_query[0]['first_name'], all_messages = all_messages, all_comments = all_comments)

@app.route('/message', methods=['POST'])
def postmessage():
    #posts messages
    query = "INSERT INTO messages (message, created_at, updated_at, user_id) VALUES (:message, NOW(), NOW(), :id)" 
    data = {
            'message': request.form['message_content'],
            'id': session['user_id']
            }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/comment', methods=['POST'])
def postcomment():
    #posts comments
    query = "INSERT INTO comments (comment, created_at, updated_at, user_id, message_id) VALUES (:comment, NOW(), NOW(), :id, :messageid)" 
    data = {
            'comment': request.form['comment_content'],
            'id': session['user_id'],
            'messageid': int(request.form['messageidnumb']),
            }
    mysql.query_db(query, data)
    return redirect('/wall')

app.run(debug=True)