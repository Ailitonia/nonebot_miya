from sqlalchemy import Sequence, ForeignKey
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# 创建数据表基类
Base = declarative_base()


# 成员表
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    id = Column(Integer, Sequence('users_id_seq'), primary_key=True, nullable=False)
    qq = Column(BigInteger, nullable=False, comment='QQ号')
    nickname = Column(String(64), nullable=False, comment='昵称')
    aliasname = Column(String(64), nullable=True, comment='自定义名称')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # 声明外键联系
    has_skills = relationship('UserSkill', back_populates='user_skill')
    in_which_groups = relationship('UserGroup', back_populates='user_groups')
    vocation = relationship('Vocation', back_populates='vocation_for_user', uselist=False)
    can_persecuted = relationship('Persecution', back_populates='user_persecutions_status', uselist=False)

    def __init__(self, qq, nickname, aliasname=None, created_at=None, updated_at=None):
        self.qq = qq
        self.nickname = nickname
        self.aliasname = aliasname
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<User(qq='%s', nickname='%s', aliasname='%s', created_at='%s', created_at='%s')>" % (
            self.qq, self.nickname, self.aliasname, self.created_at, self.updated_at)


# 技能表
class Skill(Base):
    __tablename__ = 'skills'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('skills_id_seq'), primary_key=True, nullable=False)
    name = Column(String(64), nullable=False, comment='技能名称')
    description = Column(String(64), nullable=True, comment='技能介绍')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    avaiable_skills = relationship('UserSkill', back_populates='skill_used')

    def __init__(self, name, description=None, created_at=None, updated_at=None):
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Skill(name='%s', description='%s', created_at='%s', created_at='%s')>" % (
            self.name, self.description, self.created_at, self.updated_at)


# 成员与技能表
class UserSkill(Base):
    __tablename__ = 'users_skills'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('users_skills_id_seq'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    skill_level = Column(Integer, nullable=False, comment='技能等级')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    user_skill = relationship('User', back_populates='has_skills')
    skill_used = relationship('Skill', back_populates='avaiable_skills')

    def __init__(self, user_id, skill_id, skill_level, created_at=None, updated_at=None):
        self.user_id = user_id
        self.skill_id = skill_id
        self.skill_level = skill_level
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<UserSkill(user_id='%s', skill_id='%s', skill_level='%s', created_at='%s', created_at='%s')>" % (
            self.user_id, self.skill_id, self.skill_level, self.created_at, self.updated_at)


# qq群表
class Group(Base):
    __tablename__ = 'groups'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('groups_id_seq'), primary_key=True, nullable=False)
    name = Column(String(64), nullable=False, comment='qq群名称')
    group_id = Column(Integer, nullable=False, comment='qq群号')
    noitce_permissions = Column(Integer, nullable=False, comment='通知权限')
    command_permissions = Column(Integer, nullable=False, comment='命令权限')
    admin_permissions = Column(Integer, nullable=False, comment='可使用管理员命令权限')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    avaiable_groups = relationship('UserGroup', back_populates='groups_have_users')

    def __init__(self, name, group_id, noitce_permissions, command_permissions,
                 admin_permissions, created_at=None, updated_at=None):
        self.name = name
        self.group_id = group_id
        self.noitce_permissions = noitce_permissions
        self.command_permissions = command_permissions
        self.admin_permissions = admin_permissions
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Group(name='%s', group_id='%s', noitce_permissions='%s', " \
               "command_permissions='%s', admin_permissions='%s', created_at='%s', created_at='%s')>" % (
                   self.name, self.group_id, self.noitce_permissions, self.command_permissions,
                   self.admin_permissions, self.created_at, self.updated_at)


# 成员与qq群表
class UserGroup(Base):
    __tablename__ = 'users_groups'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('users_groups_id_seq'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    user_group_nickname = Column(String(64), nullable=True, comment='用户群昵称')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    user_groups = relationship('User', back_populates='in_which_groups')
    groups_have_users = relationship('Group', back_populates='avaiable_groups')

    def __init__(self, user_id, group_id, user_group_nickname=None, created_at=None, updated_at=None):
        self.user_id = user_id
        self.group_id = group_id
        self.user_group_nickname = user_group_nickname
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<UserGroup(user_id='%s', group_id='%s', " \
               "user_group_nickname='%s', created_at='%s', created_at='%s')>" % (
                   self.user_id, self.group_id, self.user_group_nickname, self.created_at, self.updated_at)


# 假期表
class Vocation(Base):
    __tablename__ = 'vocations'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('vocations_id_seq'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Integer, nullable=False, comment='请假状态 0-空闲 1-请假 2-工作中')
    stop_at = Column(DateTime, nullable=True, comment='假期结束时间')
    reason = Column(String(64), nullable=True, comment='请假理由')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    vocation_for_user = relationship('User', back_populates='vocation')

    def __init__(self, user_id, status, stop_at=None, reason=None, created_at=None, updated_at=None):
        self.user_id = user_id
        self.status = status
        self.stop_at = stop_at
        self.reason = reason
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Vocation(user_id='%s',status='%s',stop_at='%s',reason='%s', created_at='%s', created_at='%s')>" % (
            self.user_id, self.status, self.stop_at, self.reason, self.created_at, self.updated_at)


# 迫害表
class Persecution(Base):
    __tablename__ = 'persecutions'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    id = Column(Integer, Sequence('persecutions_id_seq'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    gender = Column(String(64), nullable=False, comment='他/她/TA')
    status = Column(Integer, nullable=False, comment='0=不准迫害 1=允许迫害')
    boring = Column(Integer, nullable=False, comment='0=正常迫害 1=防止此人调戏bot')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    user_persecutions_status = relationship('User', back_populates='can_persecuted')

    def __init__(self, user_id, gender, status, boring, created_at=None, updated_at=None):
        self.user_id = user_id
        self.gender = gender
        self.status = status
        self.boring = boring
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Persecution(user_id='%s', gender='%s',status='%s',boring='%s', created_at='%s', created_at='%s')>" % (
            self.user_id, self.gender, self.status, self.boring, self.created_at, self.updated_at)


# Pixiv作品表
class Pixiv(Base):
    __tablename__ = 'pixiv_illusts'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    id = Column(Integer, Sequence('upixiv_illusts_id_seq'), primary_key=True, nullable=False)
    pid = Column(Integer, nullable=False, comment='pid')
    uid = Column(Integer, nullable=False, comment='uid')
    title = Column(String(256), nullable=False, comment='title')
    author = Column(String(256), nullable=False, comment='author')
    tags = Column(String(1024), nullable=False, comment='tags')
    url = Column(String(1024), nullable=False, comment='url')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    def __init__(self, pid, uid, title, author, tags, url, created_at=None, updated_at=None):
        self.pid = pid
        self.uid = uid
        self.title = title
        self.author = author
        self.tags = tags
        self.url = url
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Pixiv(pid='%s',uid='%s',title='%s',author='%s'," \
               "tags='%s', url='%s', created_at='%s', created_at='%s')>" % (
                   self.pid, self.uid, self.title, self.author,
                   self.tags, self.url, self.created_at, self.updated_at)
