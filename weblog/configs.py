import os


class BaseConfig:
    '''
    基础配置类，存储公共配置项
    '''

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hahha'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BLOGS_PER_PAGE = 10
    USERS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10

class DevConfig(BaseConfig):
    '''
    开发阶段使用的配置类
    '''

    # 这是设置连接数据库的配置项
    url = 'mysql://root:123456@127.0.0.1/weblog?charset=utf8'
    pwd = os.environ.get('MYSQL_PWD')
    pwd = ':{}'.format(pwd) if pwd else ''
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@127.0.0.1/weblog?charset=utf8'


class TestConfig(BaseConfig):
    '''
    测试阶段使用的配置类
    '''

    pass


# 配置类字典，便于 app.py 文件中的应用调用
configs = {
    'dev': DevConfig,
    'test': TestConfig
}