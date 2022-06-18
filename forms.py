from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from datetime import datetime, date
from wtforms.fields.html5 import DateTimeField, DateField, TimeField


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    first_name = StringField("Imię", validators=[DataRequired()])
    last_name = StringField("Nazwisko", validators=[DataRequired()])
    mobile = StringField("Telefon", validators=[DataRequired()])
    submit = SubmitField("Zarejestruj")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Zaloguj")


class CreatePostForm(FlaskForm):
    title = StringField("Tytuł Posta", validators=[DataRequired()])
    body = CKEditorField("Treść posta", validators=[DataRequired()])
    image_url = StringField("Link do zdjęcia", validators=[DataRequired(), URL()])
    submit = SubmitField("Opublikuj")


class BookVisitForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    date = DateField("Data wizyty", format='%Y-%m-%d', validators=[DataRequired()])
    starts_at = TimeField("Godzina rozpoczęcia wizyty", format='%H:%M', validators=[DataRequired()])
    # ends_at = DateTimeField("Godzina zakończenia wizyty", format='%H:%M:%S')
    submit = SubmitField("Dodaj wizytę")