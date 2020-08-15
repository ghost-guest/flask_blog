from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from .models import db, User
from wtforms import IntegerField, TextAreaField, SelectField, RadioField
from  flask_login import current_user
from flask_pagedown.fields import PageDownField


class RegisterForm(FlaskForm):
    """注冊表单类"""
    name = StringField('Name', validators=[DataRequired(), Length(3, 22),
                                           Regexp('^\w+', 0, 'user name must have only letters.')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired(), Length(3, 32)])
    repeat_password = PasswordField('RepeatPassword', validators=[DataRequired(),
                                                                  EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('email already registered')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('name already registered')

class LoginForm(FlaskForm):
    """登录表单类
    """
    email = StringField('Email', validators=[DataRequired(), Length(6, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 32)])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):
    """用户编辑个人信息所用的表单类"""

    name = StringField('用户名', validators=[DataRequired(), Length(2, 22),
                                          Regexp('^\w+$', 0, '用户只能使用单词字符')])
    age = IntegerField('年龄')
    gender = RadioField('性别', choices=[('Male', '男'), ('Female', '女')])
    phone_number = StringField('电话', validators=[Length(6, 16)])
    location = StringField('地址', validators=[Length(2, 16)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField("提交")

    def validate_name(self, field):
        if (field.data != self.user.name and User.query.filter_by(name=field.data).first()):
            raise ValidationError('该用户已经存在')

    def validate_phone_number(self, field):
        if (field.data != self.phone_number.data and
        User.query.filter_by(phone_number=field.data).first()):
            raise ValidationError('该电话号码已经存在')
    def __init__(self, user, *args, **kwargs):
        """创建该类实例时，需要提供一个用户对象作为参数"""
        super().__init__(*args, **kwargs)
        self.user = user

class ChangePasswordForm(FlaskForm):
    """用户登录后修改密码"""
    old_password = PasswordField('原密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[DataRequired(), Length(3, 22)])
    repeat_password = PasswordField('重复新密码', validators=[DataRequired()])
    submit = SubmitField('提交')

    def validate_old_password(self, field):
        if not current_user.verify_password(field.data):
            raise  ValidationError('原密码错误')

class BlogForm(FlaskForm):
    '''博客表单类'''

    body = PageDownField('记录你的想法', validators=[DataRequired()])
    submit = SubmitField('发布')


class CommentForm(FlaskForm):
    '''评论表单类'''

    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('提交')
