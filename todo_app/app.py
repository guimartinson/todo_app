from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt
from authlib.integrations.flask_client import OAuth
from authlib.jose import jwt
import os
import secrets
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Establish a connection to the MySQL database
db = mysql.connector.connect(
    host=os.getenv('DB_ID'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database="todo_app"
)

# Initialize OAuth for handling social login (Google login in this case)
oauth = OAuth(app)

# Configure Google OAuth provider details
google = oauth.register(
    name='google',
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_params=None,
    client_kwargs={'scope': 'openid profile email'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

# Home route with login and register options
@app.route('/')
def home():
    # Check if the user is already logged in
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect(url_for('todo'))
    return render_template('login.html')

# Register route for creating a new user account
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the user is already logged in
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect(url_for('todo'))
    
    if request.method == 'POST':
        # Get email and password from the registration form
        email = request.form['email']
        password = request.form['password']
        # Hash the password using Bcrypt for security
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Create a database cursor and execute a query to check if the email is already registered
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()

# If the email is already registered, show an error message and redirect to the registration page
        if user:
            flash("Email already registered!", "error")
            return redirect(url_for('register'))
        
# Insert new user into the Users table
        cursor.execute("INSERT INTO Users (email, password_hash, is_guest) VALUES (%s, %s, %s)", 
                       (email, hashed_password, 0)) # is_guest is set to 0, indicating a registered user
        db.commit() # Commit the transaction to the database
        
        # Show a success message and redirect the user to the login page
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('home'))

# Render the registration page if the request method is GET
    return render_template('register.html')

# Login route for user authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect(url_for('todo'))
    
    if request.method == 'POST':
        # Get the email and password from the login form
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # user[2] is password_hash
            session['user_id'] = user[0]
            session['email'] = user[1]
            flash(f"Welcome, {user[1]}!", "success")
            return redirect(url_for('todo'))
        else:
            flash("Invalid login credentials!", "error")
            return redirect(url_for('home'))

    return render_template('login.html')

# Google Login Route
@app.route('/google/login')
def google_login():
    # Generate a nonce and store it in the session
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce

# Redirect the user to Google's OAuth consent screen
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri, nonce=nonce)

# Google Callback Route
@app.route('/google/callback')
def google_callback():
# Store the nonce in the session for validation later    
    token = google.authorize_access_token()
    nonce = session.get('nonce')

    # Parse the ID token and validate it against the nonce
    user_info = google.parse_id_token(token, nonce=nonce)

    cursor = db.cursor()

    # First, check if the user already exists by email
    cursor.execute("SELECT * FROM Users WHERE email = %s", (user_info['email'],))
    user = cursor.fetchone()

    if user:
        # If the user exists, update their Google ID
        cursor.execute("UPDATE Users SET google_id = %s WHERE email = %s", 
                       (user_info['sub'], user_info['email']))
        db.commit()
        session['user_id'] = user[0]
    else:
        # If the user does not exist, create a new record
        cursor.execute("INSERT INTO Users (email, google_id, is_guest) VALUES (%s, %s, %s)", 
                       (user_info['email'], user_info['sub'], 0))
        db.commit()

         # Retrieve the newly created user record and store the user ID in the session
        cursor.execute("SELECT * FROM Users WHERE google_id = %s", (user_info['sub'],))
        user = cursor.fetchone()
        session['user_id'] = user[0]

# Store the user's email in the session and show a welcome message
    session['email'] = user_info['email']
    flash(f"Welcome, {user_info['name']}!", "success")
    return redirect(url_for('todo'))

# To-Do List Route (for adding and viewing tasks)
@app.route('/todo', methods=['GET', 'POST'])
def todo():
    # Check if the user is logged in
    user_id = session.get('user_id')
    if not user_id:
        # If not logged in, redirect to the home (login) page
        flash("Please log in first!", "error")
        return redirect(url_for('home'))

    # Create a database cursor
    cursor = db.cursor()

    # If the request is POST, add a new task
    if request.method == 'POST':
        task_name = request.form['task_name']
        due_date = request.form['due_date']
        priority = request.form['priority']
        
        # Insert new task into the Tasks table
        cursor.execute("INSERT INTO Tasks (user_id, task_name, due_date, priority, completed) VALUES (%s, %s, %s, %s, %s)",
                       (user_id, task_name, due_date, priority, False))
        db.commit() # Commit the transaction to the database
        flash("Task added successfully!", "success")

# Fetch active tasks (not completed) for the logged-in user
    cursor.execute("SELECT * FROM Tasks WHERE user_id = %s AND completed = %s", (user_id, False))
    tasks = cursor.fetchall()

# Fetch completed tasks for the logged-in user
    cursor.execute("SELECT * FROM Tasks WHERE user_id = %s AND completed = %s", (user_id, True))
    completed_tasks = cursor.fetchall()

    # Render the to-do list page, showing both active and completed tasks
    return render_template('todo.html', tasks=tasks, completed_tasks=completed_tasks)

# Mark task as completed
@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    cursor = db.cursor()

# Mark the task as completed and record the timestamp    
    cursor.execute("UPDATE Tasks SET completed = %s, completed_on = %s WHERE id = %s", (True, datetime.now(), task_id))
    db.commit()
    flash("Task marked as completed!", "success")
    return redirect(url_for('todo'))

# Delete a task
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM Tasks WHERE id = %s", (task_id,))
    db.commit()
    flash("Task deleted successfully!", "success")
    return redirect(url_for('todo'))


# Logout Route (clears the session and logs out the user)
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
