from flask.app import Flask
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed,FileField
from wtforms import StringField,PasswordField,SubmitField,BooleanField,TextAreaField
from wtforms import validators
from wtforms.validators import DataRequired,EqualTo,Length,Email,ValidationError
from flaskblog.models import User
from flask_login import current_user

class RegistrationForm(FlaskForm):
    username=StringField('Username',validators=[DataRequired(),Length(min=3, max=20)])
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Sign Up')

    def validate_username(self,username):
        user=User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken!')

    def validate_email(self,email):
        email=User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('An account already exists with this email id!')

class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    remember=BooleanField("Remember Me")
    submit=SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username=StringField('Username',validators=[DataRequired(),Length(min=3, max=20)])
    email=StringField('Email',validators=[DataRequired(),Email()])
    picture=FileField('Update profile picture',validators=[FileAllowed(['jpg','png','jpeg'])])
    submit=SubmitField('Update')

    def validate_username(self,username):
        if username.data!=current_user.username:
            user=User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken!')

    def validate_email(self,email):
        if email.data!=current_user.email:
            email=User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('An account already exists with this email id!')

class PostForm(FlaskForm):
    title=StringField('Title',validators=[DataRequired()])
    content=TextAreaField('Content',validators=[DataRequired()])
    submit=SubmitField('Post')

class RequestResetForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Email()])
    submit=SubmitField('Request password reset')

    def validate_email(self,email):
        email=User.query.filter_by(email=email.data).first()
        if email is None:
            raise ValidationError('No account exists with this email. Please register first.')

class PasswordResetForm(FlaskForm):
    password=PasswordField('Password',validators=[DataRequired()])
    confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Reset password')