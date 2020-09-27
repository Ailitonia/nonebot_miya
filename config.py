from nonebot.default_config import *

# nonebot配置
SUPERUSERS = {}
COMMAND_START = {'/'}
HOST = '0.0.0.0'
PORT = 3322
DEBUG = True
ACCESS_TOKEN = ''

SESSION_RUNNING_EXPRESSION = '你有其他命令正在执行呢QAQ，请稍后再试吧~'
DEFAULT_VALIDATION_FAILURE_EXPRESSION = '你发送的内容格式不太对呢QAQ，请检查一下再发送哦～'
MAX_VALIDATION_FAILURES = 3
TOO_MANY_VALIDATION_FAILURES_EXPRESSION = '你输错太多次啦QAQ，建议先看看使用帮助哦～'
SESSION_CANCEL_EXPRESSION = '已中止操作，下次有需要再叫我哦~'

# 下面都是自定义的配置

# 数据库相关
# 配置使用DBAPI规范
DATABASE = 'mysql'
DB_DRIVER = 'mysqldb'
DB_USER = 'test'
DB_PASSWORD = 'test'
DB_HOST = '127.0.0.1'
DB_PORT = '3306'
DB_NAME = 'test'
