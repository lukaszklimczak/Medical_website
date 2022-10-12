from flask import Flask, render_template, url_for, redirect, flash, abort, session, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv, find_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import date, datetime, timedelta
from forms import RegisterForm, RegisterBookUnregisteredUserForm, LoginForm, CreatePostForm, BookVisitForm, EditProfileForm
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import SignatureExpired
from flask_wtf.csrf import CSRFProtect
import re
from socket import gethostname

app = Flask(__name__)
Bootstrap(app)
mail = Mail(app)

load_dotenv(find_dotenv())

app.secret_key = os.getenv("SECRET_KEY")  # secret key is stored in .env file

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'e2021smtp.test@yahoo.com'
app.config['MAIL_PASSWORD'] = 'gstfufehsceusfas'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

csrf = CSRFProtect(app)

s = URLSafeTimedSerializer(app.secret_key)

now = date.today()
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), unique=False, nullable=False)
    last_name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    mobile = db.Column(db.Integer, unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
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
            flash("Aby to zrobić musisz być zalogowany", 'error')
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


@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = s.loads(token, salt='email-confirm', max_age=86400)
    try:
        user = User.query.filter_by(email=email).first()
        user.confirmed = True
        db.session.commit()
        flash('Twoje konto zostało potwierdzone. Teraz możesz się zalogować.')
    except SignatureExpired:
        flash('Link aktywacyjny wygasł. Wysłano ponowny email z linkiem')
    return redirect(url_for('login'))


def send_confirmation_link(token, sender, email):
    msg = Message('Confirm Email', sender=sender, recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = f'Twój link aktywacyjny to {link}'
    mail.send(msg)


@app.route('/resend_confirmation_link/<email>', methods=['GET', 'POST'])
def resend_confirmation_link(email):
    sender = app.config['MAIL_USERNAME']
    if request.method == 'POST':
        if request.form.get("resend"):
            token = s.dumps(email, salt='email-confirm')
            send_confirmation_link(token, sender, email)
            flash("Na podany adres e-mail wysłano link aktywacyjny. Ważność linka wygasa po 24 godzinach.")
            return redirect(url_for("login"))
    return render_template('unconfirmed.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Użytkownik o takim adresie e-mail został już zarejestrowany. Wybierz opcję 'Zaloguj się'", 'error')
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

        email = new_user.email
        token = s.dumps(email, salt='email-confirm')
        sender = app.config['MAIL_USERNAME']

        send_confirmation_link(token, sender, email)

        flash("Na podany adres e-mail wysłano link aktywacyjny. Ważność linka wygasa po 24 godzinach.")
        return redirect(url_for("login"))

    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Użytkownik o takim adresie e-mail nie istnieje. Spróbuj ponownie.", 'error')
            return redirect(url_for('login'))
        elif not user.confirmed:
            flash("Nie potwierdzono konta. Potwierdź link aktywacyjny wysłany na Twój adres email. Jeśli nie otrzymałeś"
                  "wiadomości z linkiem aktywacyjnym lub link wygasł, kliknij poniższy przycisk.", 'error')
            return redirect(url_for('resend_confirmation_link', email=email))
        elif not check_password_hash(user.password, password):
            flash("Podane hasło jest nieprawidłowe. Spróbuj ponownie.", 'error')
            return redirect(url_for('login'))
        else:
            login_user(user)
            # session['user'] = user
            return redirect(url_for('about'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('about'))


@app.context_processor
def utility_processor():
    def clean_html(a_string):
        cleantext = re.sub(CLEANR, ' ', a_string)
        return cleantext
    return dict(clean_html=clean_html)


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

    holidays = ['01-01', '01-06', '05-01', '05-03', '08-15', '11-01', '11-11',
                '12-25', '12-26']

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
                                              Visit.starts_at == datetime.strptime(form.starts_at.data.strftime('%H:00'),
                                                                                   '%H:00').time()).first():
                available_hours_to_string = ", ".join(available_hours)
                message = f"Dostępne godziny w tym dniu to {available_hours_to_string}"
                flash("Ten termin wizyty jest już zarezerwowany. Wybierz inny termin wizyty.", 'error')
                flash(message)
                return redirect(url_for('book_a_visit'))

            if selected_date <= date.today():
                flash("Wizytę można zarezerwować jedynie w dni nadchodzące.", 'error')
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
                flash("Poradnia jest czynna od poniedziałku do piątku.\n Proszę zarezerwować termin w dni pracy Poradni.",
                      'error')
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%m-%d') in holidays:
                flash("Poradnia w tym dniu jest nieczynna.\n Proszę zarezerwować termin w dni pracy Poradni.",
                      'error')
                return redirect(url_for('book_a_visit'))

            if form.starts_at.data < datetime.strptime(available_hours[0],
                                                       '%H:%M').time() or form.starts_at.data > datetime.strptime(
                available_hours[len(available_hours) - 1], '%H:%M').time():
                flash("Wizytę można zarezerwować od godziny 10:00 do godziny 18:00.", 'error')
                return redirect(url_for('book_a_visit'))

            new_visit = Visit(
                date=form.date.data,
                starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
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
                      " Można mieć tylko jedną zarezerwowaną wizytę!", 'error')
                return redirect(url_for('book_a_visit'))

            not_available_hours = db.session.query(func.strftime('%H:00', Visit.starts_at)).filter(
                Visit.date == selected_date).all()
            available_hours = all_hours
            for i in range(len(not_available_hours)):
                if not_available_hours[i][0] in available_hours:
                    available_hours.remove(not_available_hours[i][0])

            if db.session.query(Visit).filter(Visit.date == form.date.data,
                                              Visit.starts_at == datetime.strptime(form.starts_at.data.strftime('%H:00'),
                                                                                   '%H:00').time()).first():
                available_hours_to_string = ", ".join(available_hours)
                message = f"Dostępne godziny w tym dniu to {available_hours_to_string}"
                flash("Ten termin wizyty jest już zarezerwowany. Wybierz inny termin wizyty.", 'error')
                flash(message)
                return redirect(url_for('book_a_visit'))

            if selected_date <= date.today():
                flash("Wizytę można zarezerwować jedynie w dni nadchodzące.", 'error')
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
                flash("Poradnia jest czynna od poniedziałku do piątku. Proszę zarezerwować termin w dni pracy Poradni.",
                      'error')
                return redirect(url_for('book_a_visit'))

            if selected_date.strftime('%m-%d') in holidays:
                flash("Poradnia w tym dniu jest nieczynna.\n Proszę zarezerwować termin w dni pracy Poradni.",
                      'error')
                return redirect(url_for('book_a_visit'))

            if form.starts_at.data < datetime.strptime(available_hours[0],
                                                       '%H:%M').time() or form.starts_at.data > datetime.strptime(
                available_hours[len(available_hours) - 1], '%H:%M').time():
                flash("Wizytę można zarezerwować od godziny 10:00 do godziny 18:00.", 'error')
                return redirect(url_for('book_a_visit'))

            new_visit = Visit(
                date=form.date.data,
                starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
                patient_id=current_user.id
            )
            db.session.add(new_visit)
            db.session.commit()
            flash("Zarezerwowano wizytę.")
            return redirect(url_for('show_visits'))
    return render_template('book.html', form=form, current_user=current_user)


@app.route('/register_book/', methods=['GET', 'POST'])
@admin_only
def register_book_a_visit():
    all_hours = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00',
                 '17:00', '18:00']

    holidays = ['01-01', '01-06', '05-01', '05-03', '08-15', '11-01', '11-11',
                '12-25', '12-26']

    form = RegisterBookUnregisteredUserForm()
    if form.validate_on_submit():
        selected_date = form.date.data
        not_available_hours = db.session.query(func.strftime('%H:00', Visit.starts_at)).filter(
            Visit.date == selected_date).all()
        available_hours = all_hours
        for i in range(len(not_available_hours)):
            if not_available_hours[i][0] in available_hours:
                available_hours.remove(not_available_hours[i][0])

        if db.session.query(Visit).filter(Visit.date == form.date.data,
                                          Visit.starts_at == datetime.strptime(form.starts_at.data.strftime('%H:00'),
                                                                               '%H:00').time()).first():
            available_hours_to_string = ", ".join(available_hours)
            message = f"Dostępne godziny w tym dniu to {available_hours_to_string}"
            flash("Ten termin wizyty jest już zarezerwowany. Wybierz inny termin wizyty.", 'error')
            flash(message)
            return redirect(url_for('book_a_visit'))

        if selected_date <= date.today():
            flash("Wizytę można zarezerwować jedynie w dni nadchodzące.", 'error')
            return redirect(url_for('book_a_visit'))

        if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
            flash("Poradnia jest czynna od poniedziałku do piątku.\n Proszę zarezerwować termin w dni pracy Poradni.",
                  'error')
            return redirect(url_for('book_a_visit'))

        if selected_date.strftime('%m-%d') in holidays:
            flash("Poradnia w tym dniu jest nieczynna.\n Proszę zarezerwować termin w dni pracy Poradni.",
                  'error')
            return redirect(url_for('book_a_visit'))

        if form.starts_at.data < datetime.strptime(available_hours[0],
                                                   '%H:%M').time() or form.starts_at.data > datetime.strptime(
            available_hours[len(available_hours) - 1], '%H:%M').time():
            flash("Wizytę można zarezerwować od godziny 10:00 do godziny 18:00.", 'error')
            return redirect(url_for('book_a_visit'))

        if User.query.filter_by(email=form.email.data).first():
            flash("Użytkownik o takim adresie e-mail został już zarejestrowany. Wybierz opcję 'Zaloguj się'", 'error')
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
        new_user.confirmed = True
        db.session.commit()

        new_visit = Visit(
            date=form.date.data,
            starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
            patient_id=new_user.id
        )

        db.session.add(new_visit)
        db.session.commit()
        flash("Zarezerwowano wizytę.")
        return redirect(url_for('show_visits'))

    return render_template('register-book.html', form=form)


@app.context_processor
def utility_processor():
    def make_list_visits(hour, list_of_days):
        list_of_visits_at_specific_time = []
        for elem in list_of_days:
            if elem:
                list_of_visits_at_specific_time.append(Visit.query.filter(Visit.date == elem, Visit.starts_at == datetime.strptime(hour, '%H').time()).first())
            else:
                list_of_visits_at_specific_time.append(0)
        return list_of_visits_at_specific_time
    return dict(make_list_visits=make_list_visits)


@app.route('/visits/', methods=['GET', 'POST'])
@login_required
def show_visits():
    global now
    holidays = ['01-01', '01-06', '05-01', '05-03', '08-15', '11-01', '11-11',
                '12-25', '12-26']

    hours = ['10', '11', '12', '13', '14', '15', '16', '17', '18']

    following_dates_list = [now + timedelta(days=x) for x in range(7)]
    dates_list = following_dates_list
    free_days = []
    days_of_week = []
    for elem in dates_list:
        if elem.strftime('%A') == "Saturday" or elem.strftime('%A') == "Sunday" or elem.strftime('%m-%d') in holidays:
            free_days.append(None)
            days_of_week.append(elem.strftime('%A'))
        else:
            free_days.append(elem)
            days_of_week.append(elem.strftime('%A'))

    mapping = {
        'Monday': 'Poniedziałek',
        'Tuesday': 'Wtorek',
        'Wednesday': 'Środa',
        'Thursday': 'Czwartek',
        'Friday': 'Piątek',
        'Saturday': 'Sobota',
        'Sunday': 'Niedziela',
    }
    days_of_week = [mapping.get(word, word) for word in days_of_week]

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

    return render_template('visits.html', days=dates_list, free_days=free_days, visits=user_visits, hours=hours,
                           days_of_week=days_of_week, booked=is_booked)


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
                flash("Nie ma takiej wizyty.", 'error')
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

        if delete_form.validate_on_submit():

            date_of_visit_to_delete = delete_form.date.data
            starts_at_of_visit_to_delete = datetime.strptime(delete_form.starts_at.data.strftime('%H:00'), '%H:00').time()
            visit_to_delete = db.session.query(Visit).filter(Visit.date == date_of_visit_to_delete,
                                                             Visit.starts_at == starts_at_of_visit_to_delete).first()

            if not visit_to_delete:
                flash("Nie ma takiej wizyty.", 'error')
                return redirect(url_for('show_visits'))

            if visit_to_delete.patient.email != current_user.email:
                flash("Możesz usunąć tylko wizytę zarejestrowaną na Twój adres e-mail.", 'error')
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

    holidays = ['01-01', '01-06', '05-01', '05-03', '08-15', '11-01', '11-11',
                '12-25', '12-26']

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
            flash("Ten termin wizyty jest już zarezerwowany. Aby zablokować termin najpierw usuń wizytę.", 'error')
            flash(message)
            return redirect(url_for('block_term'))

        if selected_date <= date.today():
            flash("Termin można zablokować jedynie w dni nadchodzące.", 'error')
            return redirect(url_for('block_term'))

        if selected_date.strftime('%A') == "Saturday" or selected_date.strftime('%A') == "Sunday":
            flash("Poradnia jest czynna od poniedziałku do piątku. Zablokować termin można jedynie w dni pracy Poradni.",
                  'error')
            return redirect(url_for('block_term'))

        if selected_date.strftime('%m-%d') in holidays:
            flash("Poradnia w tym dniu i tak jest nieczynna.", 'error')
            return redirect(url_for('book_a_visit'))

        if form.starts_at.data < datetime.strptime(available_hours[0],
                                                   '%H:%M').time() or form.starts_at.data > datetime.strptime(
            available_hours[len(available_hours) - 1], '%H:%M').time():
            flash("Termin można zablokować w godziny pracy Poradni, od godziny 10:00 do godziny 18:00.", 'error')
            return redirect(url_for('block_term'))

        blocked_term = Visit(
            date=form.date.data,
            starts_at=datetime.strptime(form.starts_at.data.strftime('%H:00'), '%H:00').time(),
            patient_id=current_user.id
        )

        db.session.add(blocked_term)
        db.session.commit()
        flash("Zablokowano termin.")
        return redirect(url_for('show_visits'))

    return render_template('block-term.html', form=form, current_user=current_user)


@app.context_processor
def utility_processor():
    def display_patient_visits(patient):
        return Visit.query.filter(Visit.date >= date.today(), Visit.patient_id == patient.id).all()
    return dict(display_patient_visits=display_patient_visits)


@app.route('/show_patients', methods=['GET'])
@admin_only
def show_patients():
    patients = User.query.all()
    return render_template('show-patients.html', patients=patients)


@app.route('/delete_patient', methods=['GET', 'POST'])
@admin_only
def delete_patient():
    user_id = request.form.get('id')
    patient_to_delete = User.query.get(user_id)

    user_visits = Visit.query.filter(Visit.date >= date.today(), Visit.patient_id == user_id).all()
    if user_visits:
        for visit in user_visits:
            db.session.delete(visit)
            db.session.commit()

    db.session.delete(patient_to_delete)
    db.session.commit()
    patients = User.query.all()
    return render_template('show-patients.html', patients=patients)


@app.route('/show_profile', methods=['GET'])
@login_required
def show_profile():
    is_booked = None
    user_visits = Visit.query.filter(Visit.date >= date.today(), Visit.patient_id == current_user.id).all()
    if user_visits:
        is_booked = True
    return render_template("show-profile.html", current_user=current_user, visits=user_visits, booked=is_booked)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = current_user.id
    profile_to_edit = User.query.get(user_id)
    edit_form = EditProfileForm(
        password=profile_to_edit.password,
        first_name=profile_to_edit.first_name,
        last_name=profile_to_edit.last_name,
        mobile=profile_to_edit.mobile,
    )
    if edit_form.validate_on_submit():

        if edit_form.password.data:
            hash_and_salted_password = generate_password_hash(
                edit_form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            profile_to_edit.password = hash_and_salted_password
        else:
            pass
        profile_to_edit.first_name = edit_form.first_name.data
        profile_to_edit.last_name = edit_form.last_name.data
        profile_to_edit.mobile = edit_form.mobile.data
        db.session.commit()
        return redirect(url_for('about'))

    return render_template('edit-profile.html', form=edit_form, current_user=current_user)


@app.route('/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_profile():
    user_id = current_user.id
    patient_to_delete = User.query.get(user_id)

    user_visits = Visit.query.filter(Visit.date >= date.today(), Visit.patient_id == user_id).all()
    if user_visits:
        for visit in user_visits:
            db.session.delete(visit)
            db.session.commit()

    db.session.delete(patient_to_delete)
    db.session.commit()
    logout_user()
    return redirect(url_for('about'))


@app.route('/statute')
def show_statute():
    return render_template('statute.html')


if __name__ == "__main__":
    db.create_all()
    if 'liveconsole'not in gethostname():
        app.run()
