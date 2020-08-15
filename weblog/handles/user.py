'''
完成注册和验证后，用户相关的视图函数
'''

from datetime import datetime
from flask import Blueprint, abort, redirect, url_for, flash, render_template
from flask import request, current_app
from flask_login import login_required, login_user, current_user

from ..models import db, User, Role, Blog, Permission
from ..forms import ProfileForm, ChangePasswordForm, BlogForm

user = Blueprint('user', __name__, url_prefix='/user')

@user.route('/<name>/index')
def index(name):
    '''用户的个人主页'''
    user = User.query.filter_by(name=name).first()
    if not user:
        abort(404)
    blogs = user.blogs.order_by(Blog.time_stamp.desc())

    return render_template('user/index.html', user=user, blogs=blogs)

@user.route('/edit-profile', methods=["GET", 'POST'])
@login_required
def edit_profile():
    '''用户编辑自己的个人信息'''
    form = ProfileForm(current_user, obj=current_user)
    if form.validate_on_submit():
        form .populate_obj(current_user)
        db.session.add(current_user)
        db.session.commit()
        flash('个人信息更新成功', 'success')
        return redirect(url_for('.index', name=current_user.name))
    return render_template('user/edit_profile.html', form=form)

@user.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    '''登录后修改密码'''
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.add(current_user)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('.index', name=current_user.name))
    return render_template('user/change_password.html', form=form)

@user.route('/edit-blog/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_blog(id):
    '''用户编写博客'''
    blog = Blog.query.get_or_404(id)
    # 如果当前登录用户既不是作者又不是管理员，则没有编辑权限，返回 403
    if current_user != blog.author and not current_user.is_administrator:
        abort(403)
    form = BlogForm(obj=blog)
    if form.validate_on_submit():
        form.populate_obj(blog)
        db.session.add(blog)
        db.session.commit()
        flash('博客已经更新', 'success')
        return redirect(url_for('front.blog', id=blog.id))
    return render_template('user/edit_blog.html', form=form)

@user.route('/follow/<name>')
@login_required
def follow(name):
    '''关注用户'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('该用户不存在。', 'warning')
        return redirect(url_for('front.index'))
    if current_user.is_following(user):
        flash('在此操作之前，你已经关注了该用户。', 'info')
    else:
        current_user.follow(user)
        flash('成功关注此用户。', 'success')
    return redirect(url_for('.index', name=name))


@user.route('/unfollow/<name>')
@login_required
def unfollow(name):
    '''取关用户'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('该用户不存在。', 'warning')
        return redirect(url_for('front.index'))
    if not current_user.is_following(user):
        flash('你并未关注此用户。', 'info')
    else:
        current_user.unfollow(user)
        flash('成功取关此用户。', 'success')
    return redirect(url_for('.index', name=name))

@user.route('/<name>/followed')
def followed(name):
    '''【user 关注了哪些用户】的页面'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('用户不存在。', 'warning')
        return redirect(url_for('front.index'))
    page = request.args.get('page', default=1, type=int)
    pagination = user.followed.paginate(
            page,
            per_page = current_app.config['USERS_PER_PAGE'],
            error_out = False
    )
    follows = [{'user': f.followed, 'time_stamp': f.time_stamp}
            for f in pagination.items]
    # 这个模板是「关注了哪些用户」和「被哪些用户关注了」共用的模板
    return render_template('user/follow.html', user=user, title='我关注的人',
            endpoint='user.followed', pagination=pagination, follows=follows)


@user.route('/<name>/followers')
def followers(name):
    '''【user 被哪些用户关注了】的页面'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('用户不存在。', 'warning')
        return redirect(url_for('front.index'))
    page = request.args.get('page', default=1, type=int)
    pagination = user.followers.paginate(
            page,
            per_page = current_app.config['USERS_PER_PAGE'],
            error_out = False
    )
    follows = [{'user': f.follower, 'time_stamp': f.time_stamp}
            for f in pagination.items]
    return render_template('user/follow.html', user=user, title='关注我的人',
            endpoint='user.followers', pagination=pagination, follows=follows)