from flask import Flask, render_template, url_for, redirect, flash, abort, session
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from dotenv import load_dotenv, find_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import date
from forms import RegisterForm, LoginForm, CreatePostForm
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
Bootstrap(app)

# load_dotenv(find_dotenv())

app.secret_key = os.getenv("SECRET_KEY") #secret key is stored in .env file

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), unique=False, nullable=False)
    last_name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    mobile = db.Column(db.Integer, unique=True, nullable=False)
    posts = db.relationship("BlogPost", backref="poster")
    # visit = db.relationship("Visit", backref='patient', uselist=False) #one to one relationship
# db.create_all()


class BlogPost(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(80), nullable=False)
    # author = db.relationship("User", back_populates='posts')
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))
# db.create_all()


# class Visit(db.Model):
#     __tablename__ = "visits"
#     id = db.Column(db.Integer, primary_key=True)
#     date = db.Column(db.DateTime, nullable=False)
#     patient = db.Column(db.Integer, db.ForeignKey('users.id'))
#     db.create_all()


@app.route("/")
def about():
    return render_template("about.html")


@app.route('/online-therapy')
def online_therapy():
    return render_template("online-therapy.html")


@app.route('/mobile-advice')
def mobile_advice():
    return render_template("mobile-advice.html")


@app.route('/couple-therapy')
def couple_therapy():
    return render_template("couple-therapy.html")


@app.route('/phobies')
def phobies():
    return render_template("phobies.html")


@app.route('/stress')
def stress():
    return render_template("stress.html")


@app.route('/depression')
def depression():
    return render_template("depression.html")


@app.route('/our_team')
def team():
    return render_template('team.html')


@app.route('/contact')
def contact():
    return render_template("contact.html")


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Użytkownik o takim adresie e-mail został już zarejestrowany. Wybierz opcję 'Zaloguj się'")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            mobile=form.mobile.data,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("about"))
    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Użytkownik o takim adresie e-mail nie istnieje. Spróbuj ponownie.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Podane hasło jest nieprawidłowe. Spróbuj ponownie.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('about'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('about'))


if __name__ == "__main__":
    app.run(debug=True)
