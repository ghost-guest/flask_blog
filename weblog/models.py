from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from datetime import datetime
import enum
import bleach
from markdown import markdown

import pymysql
pymysql.install_as_MySQLdb()

db = SQLAlchemy()

class Gender(enum.Enum):
    """性别类，roel类中的gender属性要用到此类"""
    MALE = '男性'
    FEMALE = '女性'

class Follow(db.Model):
    '''存储用户关注信息的双主键映射类'''

    __tablename__ = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
            primary_key=True)   # 关注者 ID
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
            primary_key=True)   # 被关注者 ID
    time_stamp = db.Column(db.DateTime, default=datetime.now)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    @staticmethod
    def insert_roles():
        roles = {
            'User': Permission.FOLLOW | Permission.COMMENT | Permission.WRITE,
            'Moderator': Permission.FOLLOW | Permission.COMMENT | Permission.WRITE | Permission.MODERATE,
            'Administrator': Permission.FOLLOW | Permission.COMMENT | Permission.WRITE | Permission.MODERATE | Permission.ADMINISTER,

        }
        default_role_name = 'User'
        for r, v in roles.items():
            role = Role.query.filter_by(name=r).first() or Role(name=r)
            role.permissions = v
            role.default = True if role.name == default_role_name else False
            db.session.add(role)
        db.session.commit()
        print('角色已经创建')

    def __repr__(self):
        return '<Role : {}>'.format(self.name)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    _password = db.Column('password', db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum(Gender))
    phone_number = db.Column(db.String(32), unique=True)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    avatar_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # 此属性为「我关注了谁」，属性值为查询对象，里面是 Follow 类的实例
    # 参数 foreign_keys 意为查询 User.id 值等于 Follow.follower_id 的数据
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
            # 反向查询接口 follower 定义的是 Follow 实例的属性，创建实例用得上
            # 该属性指向关注关系中的「关注者」，对应 Follow().follower_id 属性
            # User 实例使用 followers 属性获得 Follow 实例的时候
            # 这些 Follow 实例顺便使用 follower 属性获得对应的 User 实例
            # 也就是「关注者」
            # 因为 lazy='joined' 模式可以实现立即从联结查询中加载相关对象
            # 例如，如果某个用户关注了 100 个用户
            # 调用 user.followed.all() 后会返回一个列表
            # 其中包含 100 个 Follow 实例
            # 每一个实例的 follower 和 followed 回引属性都指向相应的用户
            # 设定为 lazy='joined' 模式，即可在一次数据库查询中完成这些操作
            # 如果把 lazy 设为默认值 select
            # 那么首次访问 follower 和 followed 属性时才会加载对应的用户
            # 而且每个属性都需要一个单独的查询
            # 这就意味着获取全部被关注用户时需要增加 100 次额外的数据库查询操作
            backref=db.backref('follower', lazy='joined'),
            # cascade 表示如果该 User 对象被删除，顺便删除全部相关的 Follow 对象
            # cascade 参数的值是一组由逗号分隔的层叠选项
            # all 表示启用所有默认层叠选项，delete-orphan 表示删除所有孤儿记录
            # lazy='dynamic' 表示仅获得查询结果，不把数据从数据库加载到内存
            cascade='all, delete-orphan', lazy='dynamic')
    # 此属性可获得数据库中「谁关注了我」的查询结果，它是 Follow 实例的列表
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
            backref=db.backref('followed', lazy='joined'),
            cascade='all, delete-orphan', lazy='dynamic')
    @property
    def password(self):
        return self._password
    @password.setter
    def password(self, pwd):
        self._password = generate_password_hash(pwd)
    def verify_password(self, pwd):
        return check_password_hash(self._password, pwd)
    def __init__(self, **kw):
        """初始化实例， 给用户增加默认的角色"""
        super().__init__(**kw)
        self.role_id = Role.query.filter_by(default=True).first().id

    @property
    def is_administrator(self):
        '''判断用户是不是管理员'''
        return self.role.permissions & Permission.ADMINISTER

    @property
    def is_moderator(self):
        '''判断用户是不是协管员'''
        return self.role.permissions & Permission.MODERATE

    @property
    def has_permission(self, permission):
        '''判断用户是否有某种权限'''
        return self.role.permissions & Permission
    def __repr__(self):
        return '<User:{}>'.format(self.name)
    def pring(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    def is_following(self, user):
        '''判断 self 用户是否关注了 user 用户'''
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        '''判断 self 用户是否被 user 用户关注'''
        return self.followers.filter_by(follower_id=user.id).first() is not None
    def follow(self, user):
        '''关注 user 用户，即向 follows 数据表中添加一条数据'''
        if not self.is_following(user):
            f = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        '''取关 user 用户，即移除 follows 数据表中的一条数据'''
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()
    @property
    def followed_posts(self):
        '''我关注的所有用户的全部博客'''
        # query.join 为联表查询或者联结查询
        # 查询 Follow 实例中被关注者 ID 等于 Post.author_id 的 Post 实例
        # Follow 实例指的是哪些呢？关注者 ID 等于 self.id 的
        return Blog.query.join(Follow, Follow.followed_id==Blog.author_id
                ).filter(Follow.follower_id==self.id)



class Permission:
    '''权限类'''
    FOLLOW = 1  # 关注他人
    WRITE = 2  # 写博客
    COMMENT = 4 # 评论博客
    MODERATE = 8 # 审核评论
    ADMINISTER = 2**7 # 管理网站

class Blog(db.Model):
    '''博客'''
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    author = db.relationship('User', backref=db.backref('blogs', lazy='dynamic', cascade='all, delete-orphan'))
    @staticmethod
    def on_change_body(target, value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1',
                        'h2', 'h3', 'h4', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'), tags = allowed_tags,
            strip = True
        ))
        db.event.listen(Blog.body, 'set', Blog.on_change_body)

class Comment(db.Model):
    '''评论映射类'''

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, index=True, default=datetime.now)
    disable = db.Column(db.Boolean)
    author_id = db.Column(db.Integer,
            db.ForeignKey('user.id', ondelete='CASCADE'))
    author = db.relationship('User', backref=db.backref('comments',
            lazy='dynamic', cascade='all, delete-orphan'))
    blog_id = db.Column(db.Integer,
            db.ForeignKey('blog.id', ondelete='CASCADE'))
    blog = db.relationship('Blog', backref=db.backref('comments',
            lazy='dynamic', cascade='all, delete-orphan'))