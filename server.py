from flask import Flask, render_template, session, request, redirect, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt 
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]*$')
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret"
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=['POST'])
def create_account():
	if len(request.form['first_name']) < 2:
		flash("*Name must be at least 2 characters long", "first_name")
	elif not NAME_REGEX.match(request.form['first_name']):
		flash("*Name cannot have special characters or numbers","first_name")

	if len(request.form['last_name']) <2:
		flash("*Name must be at least 2 characters long", "last_name")
	elif not NAME_REGEX.match(request.form['last_name']):
		flash("*Name cannot have special characters or numbers", "last_name")

	mysql = connectToMySQL('advancedlogindb')
	emails = mysql.query_db("SELECT email FROM users")
	if not EMAIL_REGEX.match (request.form['email']): 
		flash("*email doesn't follow email format","email")
	
	for email in emails: #check if email input is already in the database

		if request.form['email'] == email['email']:
			flash("*email is already in the database","email")
			return redirect('/')
	if request.form['password'] == '':
		flash("*password field is required", "password")
	elif len(request.form['password']) < 8:
		flash("*password must be greater than 8 characters long", "password")

	if request.form["password_confirmation"] != request.form["password"]:
		flash("*password confirmation doesn't match password", "password_confirmation") 

	if '_flashes' in session.keys():
		return redirect('/')
	else:
		session['first_name'] = request.form['first_name']
		session['email'] = request.form['email']
		pw_hash =bcrypt.generate_password_hash(request.form['password'])
		mysql = connectToMySQL("advancedlogindb")
		query = "INSERT INTO users (first_name, last_name, email, password, user_level, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s,1, NOW(),NOW())"
		data = { "first_name" : request.form['first_name'],
				"last_name" : request.form['last_name'],
				"email" : request.form['email'],
				"password_hash" : pw_hash
				}
		mysql.query_db(query, data)

	return redirect("/success")

@app.route("/login", methods=['POST'])
def login():
	mysql = connectToMySQL('advancedlogindb')
	query = "SELECT * FROM users WHERE email = %(email)s"
	data = { "email" : request.form["email_log"]}
	result = mysql.query_db(query, data)
	if result:
		if bcrypt.check_password_hash(result[0]['password'], request.form['password_log']):
			session['email'] = result[0]["email"]
			session['id'] = result[0]["id"]
			session['user_level'] = result[0]['user_level']
			session['first_name'] = result[0]["first_name"]
			session['last_name'] = result[0]['last_name']

			if session['user_level'] == 1:
				return redirect('/success')
			elif session['user_level'] == 9:
				return redirect('/admin')


	flash("*Email or password is incorrect", "email_log")
	return redirect ('/')

@app.route("/success")
def success():

	return render_template("success.html")

@app.route('/admin')
def admin():
	if session['user_level'] != 9:
		return render_template('danger.html')
	print(session['id'])
	mysql = connectToMySQL('advancedlogindb')
	users = mysql.query_db("SELECT id, first_name, last_name, email, user_level FROM users")
	return render_template("admin.html", users = users)

@app.route("/logout")
def logout():
	session.clear()
	return redirect('/')

@app.route('/delete_user', methods=['POST'])
def deleteUser():
	mysql = connectToMySQL('advancedlogindb')
	query= "DELETE FROM users WHERE id = %(id)s"
	data = { "id": (request.form['user_id']) }
	mysql.query_db(query, data)

	return redirect('/admin')

@app.route('/promote_user', methods=['POST'])
def promoteUser():
	mysql = connectToMySQL('advancedlogindb')
	query = "UPDATE users SET user_level = 9 WHERE id = %(id)s"
	data = { "id": (request.form['user_id']) }
	mysql.query_db(query, data)


	return redirect('/admin')

@app.route('/demote_user', methods=['POST'])
def demoteUser():
	mysql = connectToMySQL('advancedlogindb')
	query = "UPDATE users SET user_level = 1 WHERE id = %(id)s"
	data = { "id": (request.form['user_id'])}
	mysql.query_db(query, data)

	return redirect('/admin')

def debugHelp(message = ""):
    print("\n\n-----------------------", message, "--------------------")
    print('REQUEST.FORM:', request.form)
    print('SESSION:', session)
if __name__ == "__main__":
    app.run(debug=True)