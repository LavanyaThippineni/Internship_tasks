#Import the required libraries
from flask import Flask, render_template, request, redirect, url_for,session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import random
import string
import os
############# SQL Alchemy Configuration #############
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mykey'

db = SQLAlchemy(app)
Migrate(app, db)
#######################################################

login_manager = LoginManager()
login_manager.init_app(app)
current_user=""
modify_note=None
add_id=None

# Tell users what view to go to when they need to login.
login_manager.login_view = "login"

@app.before_first_request
def create_tables():
    db.create_all()
############# Create a Model ##################################
class Urls(db.Model):
    __tablename__ = 'urls'
    id_ = db.Column("id_", db.Integer, primary_key=True)
    long = db.Column("long", db.String())
    short = db.Column("short", db.String(10))
#create a constructor 

    def __init__(self, long, short):
        self.long = long
        self.short = short

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)  

class User(db.Model, UserMixin):

    # Create a table in the db
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username=db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    def __init__(self,username,email, password):
        self.username=username
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

##################################################################

#Home page
@app.route('/')
def index():
    return render_template("index.html")


#Register code
@app.route('/register', methods=['GET', 'POST'])
def register():
    wrong_pssd=None
    if request.method == "POST":
        if request.form.get('password')==request.form.get('confirm_password'):
            user = User(username=request.form.get('username'),email=request.form.get('email'),
                    password=request.form.get('password'))
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        wrong_pssd="password do not match"
    return render_template('register.html',wrong_pssd=wrong_pssd)

#Login code
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # Grab the user from our User Models table
        user = User.query.filter_by(email=request.form.get('email')).first()
        if session.get('add_id') is None:
            session['add_id']=None
            session['current_user']=""
        session['add_id']=int(user.id)
        session['current_user']=user.username

        # Check that the user was supplied and the password is right
        # The check_password method comes from the User object
        if user is not None and user.check_password(request.form.get('password')):

            #Log in the user
            login_user(user)

            # If a user was trying to visit a page that requires a login
            # flask saves that URL as 'next'.
            next = request.args.get('next')

            # So let's now check if that next exists, otherwise we'll go to
            # the welcome page.
            if next == None or not next[0]=='/':
                next = url_for('index')

            return redirect(next)
    return render_template('login.html')


#Logout code
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


#To generate shortern code
def shorten_url():
    letters = string.ascii_lowercase + string.ascii_uppercase+ string.digits
    while True:
        rand_letters = random.choices(letters, k=5)
        rand_letters = "".join(rand_letters)
        short_url = Urls.query.filter_by(short=rand_letters).first()
        if not short_url:
            return rand_letters

#Home page
@app.route('/url_shortener', methods=['POST', 'GET'])
@login_required
def Home():
    if request.method == "POST":
        url_received = request.form["nm"]
        found_url = Urls.query.filter_by(long=url_received).first()

        if found_url:
            return redirect(url_for("display_short_url", url=found_url.short))
        else:
            short_url = shorten_url()
            print(short_url)
            new_url = Urls(url_received, short_url)
            db.session.add(new_url)
            db.session.commit()
            return redirect(url_for("display_short_url", url=short_url))
    else:
        return render_template('url_page.html')

@app.route('/<short_url>')
@login_required
def redirection(short_url):
    long_url = Urls.query.filter_by(short=short_url).first()
    if long_url:
        return redirect(long_url.long)
    else:
        return f'<h1>Url doesnt exist</h1>'

@app.route('/display/<url>')
@login_required
def display_short_url(url):
    return render_template('shorturl.html', short_url_display=url)

@app.route('/all_urls')
@login_required
def display_all():
    Hist = db.session.execute("Select * from urls")
    return render_template("all_urls.html", data =Hist)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
