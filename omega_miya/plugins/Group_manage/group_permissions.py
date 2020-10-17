from omega_miya.database import *
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


'''
这里封装一些用来确认群组权限的函数
供其他插件调用
'''


# 查询群组是否具有通知权限
def has_notice_permissions(group_id) -> bool:
    try:
        __res = NONEBOT_DBSESSION.query(Group.noitce_permissions).filter(Group.group_id == group_id).one()
        if __res and __res[0] == 1:
            return True
        else:
            return False
    except NoResultFound:
        return False
    except MultipleResultsFound:
        return False


# 查询群组是否具有命令权限
def has_command_permissions(group_id) -> bool:
    try:
        __res = NONEBOT_DBSESSION.query(Group.command_permissions).filter(Group.group_id == group_id).one()
        if __res and __res[0] == 1:
            return True
        else:
            return False
    except NoResultFound:
        return False
    except MultipleResultsFound:
        return False


# 查询群组是否具有管理命令权限
def has_admin_permissions(group_id) -> bool:
    try:
        __res = NONEBOT_DBSESSION.query(Group.admin_permissions).filter(Group.group_id == group_id).one()
        if __res and __res[0] == 1:
            return True
        else:
            return False
    except NoResultFound:
        return False
    except MultipleResultsFound:
        return False


# 查询所有有通知权限的群组
def query_all_notice_groups() -> list:
    __res = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).\
            filter(Group.noitce_permissions == 1).order_by(Group.id).all():
        __res.append(res[0])
    return __res


# 查询所有有命令权限的群组
def query_all_command_groups() -> list:
    __res = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).\
            filter(Group.command_permissions == 1).order_by(Group.id).all():
        __res.append(res[0])
    return __res


# 查询所有有通知权限的群组
def query_all_admin_groups() -> list:
    __res = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).\
            filter(Group.admin_permissions == 1).order_by(Group.id).all():
        __res.append(res[0])
    return __res
