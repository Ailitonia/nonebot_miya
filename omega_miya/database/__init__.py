from config import DATABASE, DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from omega_miya.database.tables import *

# 格式化数据库引擎链接
DB_ENGINE = f'{DATABASE}+{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# 初始化数据库连接
engine = create_engine(DB_ENGINE, encoding='utf8', connect_args={"use_unicode": True, "charset": "utf8mb4"},
                       pool_recycle=3600, pool_pre_ping=True)
# 初始化数据库结构
Base.metadata.create_all(engine)
# 创建DBSession对象
DBSession = sessionmaker()
DBSession.configure(bind=engine)
# 创建session对象
NONEBOT_DBSESSION = DBSession()
