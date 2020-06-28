from omega_miya.database import *
from datetime import datetime
import re


# 查询所有已存在用户的qq号
def query_member_list() -> list:
    __result = []
    for res in NONEBOT_DBSESSION.query(User.qq).order_by(User.id).all():
        __result.append(res[0])
    return __result


# 查询所有已存在qq群的群号
def query_group_list() -> list:
    __result = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).order_by(Group.id).all():
        __result.append(res[0])
    return __result


# 添加非重复用户信息到数据库
async def add_member_to_db(user_qq, user_nickname) -> bool:
    user_nickname = re.sub(r'\W+', '', user_nickname)
    exist_user_qq = query_member_list()
    if user_qq in exist_user_qq:
        # 昵称有变动则更新成员表昵称
        if not user_nickname == NONEBOT_DBSESSION.query(User.nickname).filter(User.qq == user_qq).first()[0]:
            __exist_user = NONEBOT_DBSESSION.query(User).filter(User.qq == user_qq).first()
            __exist_user.nickname = user_nickname
            __exist_user.updated_at = datetime.now()
            NONEBOT_DBSESSION.commit()
            return True
    else:
        # 成员表中添加新成员
        __new_user = User(qq=user_qq, nickname=user_nickname, created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_user)
        NONEBOT_DBSESSION.commit()
        return True


# 添加非重复qq群信息到数据库
async def add_group_to_db(group_id, group_name) -> bool:
    group_name = re.sub(r'\W+', '', group_name)
    exist_group_id = query_group_list()
    if group_id in exist_group_id:
        # 群名称有变动则更新群名称
        if not group_name == NONEBOT_DBSESSION.query(Group.name).filter(Group.group_id == group_id).first()[0]:
            __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).first()
            __exist_group.nickname = group_name
            __exist_group.updated_at = datetime.now()
            NONEBOT_DBSESSION.commit()
            return True
    else:
        # 成员表中添加新群组
        __new_group = Group(group_id=group_id, name=group_name, noitce_permissions=0,
                            command_permissions=0, admin_permissions=0, created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_group)
        NONEBOT_DBSESSION.commit()
        return True


# 添加非重复用户_所属群组信息到数据库
async def add_member_group_to_db(user_qq, group_id, user_group_nickmane) -> bool:
    user_group_nickmane = re.sub(r'\W+', '', user_group_nickmane)
    exist_user_qq = query_member_list()
    exist_group_id = query_group_list()
    # 不在成员表中的qq跳过
    if user_qq not in exist_user_qq:
        return False
    # 不在群组表中的qq群跳过
    if group_id not in exist_group_id:
        return False
    # 查这个用户在用户表中的id（不是qq号）
    __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).first()[0]
    # 查这个群组在群组表中的id（不是群号）
    __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).first()[0]
    # 查询成员-群组表中所有成员的qq，这个人用户-群关系已存在
    __result = []
    for __res in NONEBOT_DBSESSION.query(User.qq). \
            join(UserGroup).join(Group). \
            filter(User.id == UserGroup.user_id). \
            filter(UserGroup.group_id == Group.id). \
            filter(Group.group_id == group_id). \
            order_by(User.id).all():
        __result.append(__res[0])
    # 群组-成员表里面这个人用户-群关系已存在，更新用户昵称
    if user_qq in __result:
        __exist_user = NONEBOT_DBSESSION.query(UserGroup).filter(UserGroup.user_id == __user_table_id).first()
        __exist_user.user_group_nickname = user_group_nickmane
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    # 群组-成员表里面这个人用户-群关系不存在，更新用户-群组关联
    else:
        # 添加新成员
        __new_user = UserGroup(user_id=__user_table_id, group_id=__group_table_id,
                               user_group_nickname=user_group_nickmane)
        NONEBOT_DBSESSION.add(__new_user)
        NONEBOT_DBSESSION.commit()
        return True


# 重置非重复用户状态信息到数据库
async def reset_member_status_to_db(user_qq) -> bool:
    exist_user_qq = query_member_list()
    # 不在成员表中的qq跳过
    if user_qq not in exist_user_qq:
        return False
    # 查询状态表中所有成员
    __result = []
    for __res in NONEBOT_DBSESSION.query(User.qq, Vocation.status). \
            join(Vocation). \
            filter(User.id == Vocation.user_id). \
            order_by(User.id).all():
        __result.append(__res[0])
    if user_qq in __result:
        __exist_user = NONEBOT_DBSESSION.query(Vocation).join(User). \
            filter(User.id == Vocation.user_id). \
            filter(User.qq == user_qq). \
            first()
        __exist_user.status = 0
        __exist_user.stop_at = None
        __exist_user.reason = None
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    else:
        # 假期表中添加新成员
        __user_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).first()[0]
        __new_user = Vocation(user_id=__user_id, status=0)
        NONEBOT_DBSESSION.add(__new_user)
        NONEBOT_DBSESSION.commit()
        return True


# 重置非重复群组权限到数据库
async def reset_group_permissions_to_db(group_id) -> bool:
    exist_group_id = query_group_list()
    # 不在群组表中的qq群跳过
    if group_id not in exist_group_id:
        return False
    __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).first()
    __exist_group.noitce_permissions = 0
    __exist_group.command_permissions = 0
    __exist_group.admin_permissions = 0
    __exist_group.updated_at = datetime.now()
    NONEBOT_DBSESSION.commit()
    return True


# 设置已有群组权限到数据库
async def set_group_permissions_to_db(group_id,
                                      noitce_permissions=0, command_permissions=0, admin_permissions=0) -> bool:
    exist_group_id = query_group_list()
    # 不在群组表中的qq群跳过
    if group_id not in exist_group_id:
        return False
    __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).first()
    __exist_group.noitce_permissions = noitce_permissions
    __exist_group.command_permissions = command_permissions
    __exist_group.admin_permissions = admin_permissions
    __exist_group.updated_at = datetime.now()
    NONEBOT_DBSESSION.commit()
    return True


# 查询群组权限
async def query_group_permissions_in_db(group_id) -> dict:
    __result = {}
    exist_group_id = query_group_list()
    # 不在群组表中的qq群跳过
    if group_id not in exist_group_id:
        return {}
    __res = NONEBOT_DBSESSION.query(Group.noitce_permissions, Group.command_permissions, Group.admin_permissions).\
        filter(Group.group_id == group_id).first()
    __result['通知'] = __res[0]
    __result['命令'] = __res[1]
    __result['管理命令'] = __res[2]
    return __result
