from flask import Blueprint, redirect, url_for, flash, abort, request, session
from flask import render_template, current_app, make_response
from  flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
from ..forms import RegisterForm, LoginForm, BlogForm, CommentForm
from ..models import db, User, Blog, Comment, Permission


# 创建蓝图
front = Blueprint('front', __name__)

@front.app_errorhandler(404)
def page_not_found(e):
    """路由错误，页面不存在"""
    return render_template('404.html'), 404

@front.app_errorhandler(500)
def inter_server_error(e):
    """服务器内部错误"""
    return render_template('500.html'), 500

@front.route('/', methods=["GET", 'POST'])
def index():
    '''网站首页'''
    form = BlogForm()
    if current_user.is_authenticated:
        if form.validate_on_submit():
            blog = Blog()
            form.populate_obj(blog)
            blog.author = current_user
            db.session.add(blog)
            db.session.commit()
            flash('成功发布博客', 'success')
            return redirect(url_for('.index'))
    blogs = Blog.query.order_by(Blog.time_stamp.desc())
    return render_template('index.html', form=form, blogs=blogs)
    # date_time = datetime.utcnow()
    # print("1111111111111111111: %s"%date_time)
    # return render_template('index.html', date_time=date_time)
@front.route('/register', methods=['POST', 'GET'])
def register():
    """用户注册"""
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('你已经注册成功，请登录', 'success')
        return redirect(url_for('.login'))
    return render_template('register.html', form=form)

@front.route('/login', methods=['POST', 'GET'])
def login():
    '''用户登录'''
    if current_user.is_authenticated:
        flash('你已经处于登录状态', 'success')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('你已经登录成功， {}'.format(user.name), 'success')
            return redirect(url_for('.index'))
        flash('邮箱或密码错误', 'warning')
    return render_template('login.html', form=form)

@front.route('/logout')
def logout():
    '''退出登录'''
    logout_user()
    flash('你已经退出登录', 'info')
    return redirect(url_for('.index'))
@front.before_app_first_request
def before_request():
    '''页面请求预处理'''
    if current_user.is_authenticated:
        current_user.pring()


@front.route('/blog/<int:id>', methods=['GET', 'POST'])
def blog(id):
    '''每篇博客的单独页面，便于分享'''
    blog = Blog.query.get_or_404(id)
    # 页面提供评论输入框
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, blog=blog, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('评论成功。', 'success')
        return redirect(url_for('.blog', id=id))
    page = request.args.get('page', default=1, type=int)
    pagination = blog.comments.order_by(Comment.time_stamp.desc()).paginate(
            page,
            per_page = current_app.config['COMMENTS_PER_PAGE'],
            error_out = False
    )
    comments = pagination.items
    # hidebloglink 在博客页面中隐藏博客单独页面的链接
    # noblank 在博客页面中点击编辑按钮不在新标签页中打开
    return render_template('blog.html', blogs=[blog], hidebloglink=True,
            noblank=True, form=form, pagination=pagination,
            comments=comments, Permission=Permission)