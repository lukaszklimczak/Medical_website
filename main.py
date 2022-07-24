from flask import Flask, render_template, url_for, redirect, flash, abort, session, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from dotenv import load_dotenv, find_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import date, datetime, timedelta
from forms import RegisterForm, LoginForm, CreatePostForm, BookVisitForm
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app = Flask(__name__)
Bootstrap(app)

load_dotenv(find_dotenv())

app.secret_key = os.getenv("SECRET_KEY")  # secret key is stored in .env file

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)

now = date.today()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), unique=False, nullable=False)
    last_name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    mobile = db.Column(db.Integer, unique=True, nullable=False)
    posts = db.relationship("BlogPost", backref="poster")
    visit = db.relationship("Visit", backref="patient", uselist=False)  # one to one relationship


# db.create_all()


class BlogPost(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(80), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))


# db.create_all()


class Visit(db.Model):
    __tablename__ = "visits"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    starts_at = db.Column(db.Time, nullable=False)
    # ends_at = db.Column(db.Time, nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            flash("Aby zarezerwować termin musisz być zalogowany")
            return redirect(url_for('login'))

    return decorated_function


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
            # session['user'] = user
            return redirect(url_for('about'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('about'))


@app.route('/blog', methods=['GET'])
def show_blog():
    all_posts = BlogPost.query.all()
    return render_template('blog.html', posts=all_posts, current_user=current_user)


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    return render_template('post.html', current_user=current_user, post=requested_post)


@app.route('/add_post', methods=['GET', 'POST'])
@admin_only
def add_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            content=form.body.data,
            image_url=form.image_url.data,
            date=date.today().strftime("%B %d, %Y"),
            poster=current_user
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('show_blog'))
    return render_template('add_post.html', form=form, current_user=current_user)


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        poster_id=current_user.id
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.content = edit_form.body.data
        post.image_url = edit_form.image_url.data
        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('add_post.html', form=edit_form, is_edit=True, current_user=current_user)


@app.route('/delete/<int:post_id>')
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('show_blog'))


@app.route('/book/', methods=['GET', 'POST'])
@login_required
def book_a_visit():
    all_hours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00',
                 '17:00', '18:00']

    if current_user.id == 1:
        form = BookVisitForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            selected_date = form.date.data
            not_available_hours = db.session.query(func.strftime('%H:00', Visit.starts_at)).filter(
                Visit.date == selected_date).all()
            available_hours = all_hours
            for i in range(len(not_available_hours)):
                if not_available_hours[i][0] in available_hours:
                    available_hours.remove(not_available_hours[i][0])

            if db.session.query(Visit).filter(Visit.date == form.date.data,
                                              Visit.starts_at == datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time()).first():
                available_hours_to_string = ", ".join(available_hours)
                message = f"Dostępne godziny w tym dniu to {available_hours_to_string}"
                flash("Ten termin wizyty jest już zarezerwowany. Wybierz inny termin wizyty.")
                flash(message)
                return redirect(url_for('book_a_visit'))

            if selected_date <= date.today():
                flash("Wizytę można zarezerwować jedynie w dni nadchodzące.")
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
                flash("Poradnia jest czynna od poniedziałku do piątku. Proszę zarezerwować termin w dni pracy Poradni.")
                return redirect(url_for('book_a_visit'))

            if form.starts_at.data < datetime.strptime(available_hours[0],
                                                       '%H:%M').time() or form.starts_at.data > datetime.strptime(
                available_hours[len(available_hours) - 1], '%H:%M').time():
                flash("Wizytę można zarezerwować od godziny 10:00 do godziny 18:00.")
                return redirect(url_for('book_a_visit'))

            new_visit = Visit(
                date=form.date.data,
                starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
                # ends_at=form.ends_at.data,
                confirmed=True,
                patient_id=user.id
            )

            db.session.add(new_visit)
            db.session.commit()
            flash("Zarezerwowano wizytę.")
            return redirect(url_for('show_visits'))
    else:
        form = BookVisitForm(
            email=current_user.email,
        )
        if form.validate_on_submit():

            selected_date = form.date.data
            if Visit.query.filter_by(patient_id=current_user.id).first() and \
                    db.session.query(Visit).filter(Visit.date >= date.today(),
                                                   Visit.patient_id == current_user.id).first():
                flash("Użytkownik o takim adresie e-mail już zarezerwował wizytę."
                      " Można mieć tylko jedną zarezerwowaną wizytę!")
                return redirect(url_for('book_a_visit'))

            not_available_hours = db.session.query(func.strftime('%H:00', Visit.starts_at)).filter(
                Visit.date == selected_date).all()
            available_hours = all_hours
            for i in range(len(not_available_hours)):
                if not_available_hours[i][0] in available_hours:
                    available_hours.remove(not_available_hours[i][0])

            if db.session.query(Visit).filter(Visit.date == form.date.data,
                                              Visit.starts_at == datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time()).first():
                available_hours_to_string = ", ".join(available_hours)
                message = f"Dostępne godziny w tym dniu to {available_hours_to_string}"
                flash("Ten termin wizyty jest już zarezerwowany. Wybierz inny termin wizyty.")
                flash(message)
                return redirect(url_for('book_a_visit'))

            if selected_date <= date.today():
                flash("Wizytę można zarezerwować jedynie w dni nadchodzące.")
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
                flash("Poradnia jest czynna od poniedziałku do piątku. Proszę zarezerwować termin w dni pracy Poradni.")
                return redirect(url_for('book_a_visit'))

            if form.starts_at.data < datetime.strptime(available_hours[0],
                                                       '%H:%M').time() or form.starts_at.data > datetime.strptime(
                available_hours[len(available_hours) - 1], '%H:%M').time():
                flash("Wizytę można zarezerwować od godziny 10:00 do godziny 18:00.")
                return redirect(url_for('book_a_visit'))

            new_visit = Visit(
                date=form.date.data,
                starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
                # ends_at=form.ends_at.data,
                patient_id=current_user.id
            )
            db.session.add(new_visit)
            db.session.commit()
            flash("Zarezerwowano wizytę.")
            return redirect(url_for('show_visits'))
    return render_template('book.html', form=form, current_user=current_user)


@app.route('/visits/', methods=['GET', 'POST'])
@login_required
def show_visits():
    global now
    holidays = ['01-01', '01-06', '05-01', '05-03', '08-15', '11-01', '11-11',
                '12-25', '12-26']
    following_dates_list = [now + timedelta(days=x) for x in range(7)]
    dates_list = following_dates_list
    days_of_week = []
    for elem in dates_list:
        if elem.strftime('%A') == "Saturday" or elem.strftime('%A') == "Sunday" or elem.strftime('%m-%d') in holidays:
            days_of_week.append(None)
        else:
            days_of_week.append(elem)

    visits_at_10 = []
    visits_at_11 = []
    visits_at_12 = []
    visits_at_13 = []
    visits_at_14 = []
    visits_at_15 = []
    visits_at_16 = []
    visits_at_17 = []
    visits_at_18 = []
    for elem in days_of_week:
        if elem:
            visits_at_10.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '10:00:00.000000').first())
            visits_at_11.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '11:00:00.000000').first())
            visits_at_12.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '12:00:00.000000').first())
            visits_at_13.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '13:00:00.000000').first())
            visits_at_14.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '14:00:00.000000').first())
            visits_at_15.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '15:00:00.000000').first())
            visits_at_16.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '16:00:00.000000').first())
            visits_at_17.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '17:00:00.000000').first())
            visits_at_18.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == '18:00:00.000000').first())
        else:
            visits_at_10.append(0)
            visits_at_11.append(0)
            visits_at_12.append(0)
            visits_at_13.append(0)
            visits_at_14.append(0)
            visits_at_15.append(0)
            visits_at_16.append(0)
            visits_at_17.append(0)
            visits_at_18.append(0)

    is_booked = None
    user_visits = Visit.query.filter(Visit.date >= date.today(), Visit.patient_id == current_user.id).all()
    if user_visits:
        is_booked = True

    if request.method == "POST":
        if request.form.get("previous"):
            previous_dates_list = [dates_list[0] - timedelta(days=x) for x in range(7)]
            dates_list = previous_dates_list
            now = dates_list[6]
            return redirect(url_for('show_visits'))
        elif request.form.get("forward"):
            forward_dates_list = [dates_list[0] + timedelta(days=x) for x in range(7)]
            dates_list = forward_dates_list
            now = dates_list[6]
            return redirect(url_for('show_visits'))

    return render_template('visits.html', days=dates_list, days_of_week=days_of_week, visits=user_visits, visits_10=visits_at_10,
                           visits_11=visits_at_11,
                           visits_12=visits_at_12, visits_13=visits_at_13, visits_14=visits_at_14,
                           visits_15=visits_at_15, visits_16=visits_at_16, visits_17=visits_at_17,
                           visits_18=visits_at_18, booked=is_booked)


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_a_visit():
    if current_user.id == 1:
        delete_form = BookVisitForm()
        if delete_form.validate_on_submit():
            date_of_visit_to_delete = delete_form.date.data
            starts_at_of_visit_to_delete = delete_form.starts_at.data
            visit_to_delete = db.session.query(Visit).filter(Visit.date == date_of_visit_to_delete,
                                                             Visit.starts_at == starts_at_of_visit_to_delete).first()

            if not visit_to_delete:
                flash("Nie ma takiej wizyty.")
                return redirect(url_for('show_visits'))

            db.session.delete(visit_to_delete)
            db.session.commit()
            flash("Usunięto wizytę.")
            return redirect(url_for('show_visits'))

    if current_user.id != 1:
        delete_form = BookVisitForm()
        user_visits = db.session.query(Visit).filter(Visit.date >= date.today(),
                                                     Visit.patient_id == current_user.id).all()
        if len(user_visits) == 1:
            visit_to_delete = db.session.query(Visit).filter(Visit.date >= date.today(),
                                                             Visit.patient_id == current_user.id).first()
            delete_form = BookVisitForm(
                email=current_user.email,
                date=visit_to_delete.date,
                starts_at=visit_to_delete.starts_at,
            )
        else:
            delete_form = BookVisitForm(
                email=current_user.email,
                date=delete_form.date.data,
                starts_at=delete_form.starts_at.data,
            )
            date_of_visit_to_delete = delete_form.date.data
            starts_at_of_visit_to_delete = delete_form.starts_at.data
            visit_to_delete = db.session.query(Visit).filter(Visit.date == date_of_visit_to_delete,
                                                             Visit.starts_at == starts_at_of_visit_to_delete).first()

        if delete_form.validate_on_submit():

            if not visit_to_delete:
                flash("Nie ma takiej wizyty.")
                return redirect(url_for('show_visits'))

            db.session.delete(visit_to_delete)
            db.session.commit()
            flash("Usunięto wizytę.")
            return redirect(url_for('show_visits'))

    return render_template('delete-visit.html', form=delete_form, current_user=current_user)


@app.route('/block', methods=['GET', 'POST'])
@admin_only
def block_term():
    all_hours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00',
                 '17:00', '18:00']
    form = BookVisitForm(
        email=current_user.email,
    )
    if form.validate_on_submit():
        selected_date = form.date.data
        not_available_hours = db.session.query(func.strftime('%H:00', Visit.starts_at)).filter(
            Visit.date == selected_date).all()
        available_hours = all_hours
        for i in range(len(not_available_hours)):
            if not_available_hours[i][0] in available_hours:
                available_hours.remove(not_available_hours[i][0])

        if db.session.query(Visit).filter(Visit.date == form.date.data,
                                          Visit.starts_at == form.starts_at.data).first():
            available_hours_to_string = ", ".join(available_hours)
            message = f"Wolne godziny do zablokowania w tym dniu to {available_hours_to_string}"
            flash("Ten termin wizyty jest już zarezerwowany. Aby zablokować termin najpierw usuń wizytę.")
            flash(message)
            return redirect(url_for('block_term'))

        if selected_date <= date.today():
            flash("Termin można zablokować jedynie w dni nadchodzące.")
            return redirect(url_for('block_term'))

        if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
            flash(
                "Poradnia jest czynna od poniedziałku do piątku. Zablokować termin można jedynie w dni pracy Poradni.")
            return redirect(url_for('block_term'))

        if form.starts_at.data < datetime.strptime(available_hours[0],
                                                   '%H:%M').time() or form.starts_at.data > datetime.strptime(
            available_hours[len(available_hours) - 1], '%H:%M').time():
            flash("Termin można zablokować w godziny pracy Poradni, od godziny 10:00 do godziny 18:00.")
            return redirect(url_for('block_term'))

        blocked_term = Visit(
            date=form.date.data,
            starts_at=form.starts_at.data,
            # ends_at=form.ends_at.data,
            confirmed=True,
            patient_id=current_user.id
        )

        db.session.add(blocked_term)
        db.session.commit()
        flash("Zablokowano termin.")
        return redirect(url_for('show_visits'))

    return render_template('block-term.html', form=form, current_user=current_user)


def show_patients():
    pass


def delete_patient():
    pass


if __name__ == "__main__":
    app.run(debug=True)
