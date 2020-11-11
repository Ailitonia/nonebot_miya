from omega_miya.database import *
from nonebot import log
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


# 查询所有已存在用户的qq号
def query_member_list() -> list:
    __result = []
    for res in NONEBOT_DBSESSION.query(User.qq).order_by(User.id).all():
        __result.append(res[0])
    return __result


# 查询数据库中群组成员qq号
def query_group_member_list(group_id) -> list:
    # 检查群组是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: query_group_member_list ERROR: Group NoResultFound.')
        return []
    except Exception as e:
        log.logger.warning(f'{__name__}: query_group_member_list ERROR: {e}, in checking group.')
        return []

    __result = []
    for res in NONEBOT_DBSESSION.query(User.qq).join(UserGroup).\
            filter(User.id == UserGroup.user_id).\
            filter(UserGroup.group_id == __group_table_id).all():
        __result.append(int(res[0]))
    return __result


# 查询所有已存在qq群的群号
def query_group_list() -> list:
    __result = []
    for res in NONEBOT_DBSESSION.query(Group.group_id).order_by(Group.id).all():
        __result.append(res[0])
    return __result


# 添加非重复用户信息到数据库
async def add_member_to_db(user_qq, user_nickname) -> bool:
    user_qq = int(user_qq)
    user_nickname = str(user_nickname)
    try:
        # 用户已存在则更新成员表昵称
        __exist_user = NONEBOT_DBSESSION.query(User).filter(User.qq == user_qq).one()
        __exist_user.nickname = user_nickname
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则成员表中添加新成员
        try:
            __new_user = User(qq=user_qq, nickname=user_nickname, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_user)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_member_to_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: add_member_to_db ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_member_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 添加非重复qq群信息到数据库
async def add_group_to_db(group_id, group_name) -> bool:
    group_id = int(group_id)
    group_name = str(group_name)
    try:
        # qq群已存在则更新群名称
        __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).one()
        __exist_group.name = group_name
        __exist_group.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则添加新群组
        try:
            __new_group = Group(group_id=group_id, name=group_name, noitce_permissions=0,
                                command_permissions=0, admin_permissions=0, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_group)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_group_to_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: add_group_to_db ERROR: MultipleResultsFound, group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_group_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 添加非重复用户_所属群组信息到数据库
async def add_member_group_to_db(user_qq, group_id, user_group_nickmane) -> bool:
    user_qq = int(user_qq)
    group_id = int(group_id)
    user_group_nickmane = str(user_group_nickmane)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_member_group_to_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_member_group_to_db ERROR: {e}, in checking user.')
        return False

    # 检查群组是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_member_group_to_db ERROR: Group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_member_group_to_db ERROR: {e}, in checking group.')
        return False

    # 查询成员-群组表中用户-群关系
    try:
        # 用户-群关系已存在, 更新用户群昵称
        __exist_user = NONEBOT_DBSESSION.query(UserGroup). \
            filter(UserGroup.user_id == __user_table_id). \
            filter(UserGroup.group_id == __group_table_id).one()
        __exist_user.user_group_nickname = user_group_nickmane
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在关系则添加新成员
        try:
            __new_user = UserGroup(user_id=__user_table_id, group_id=__group_table_id,
                                   user_group_nickname=user_group_nickmane, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_user)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_member_group_to_db, DBSESSION ERROR, error info: {e}, '
                             f'failed to add new usergroup')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: add_member_group_to_db ERROR: MultipleResultsFound, '
                         f'user_qq: {user_qq}, group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_member_group_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 删除数据库中用户_所属群组信息
async def del_member_group_to_db(user_qq, group_id) -> bool:
    user_qq = int(user_qq)
    group_id = int(group_id)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: del_member_group_to_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: del_member_group_to_db ERROR: {e}, in checking user.')
        return False

    # 检查群组是否在表中，查这个群组在群组表中的id(不是群号)
    try:
        __group_table_id = NONEBOT_DBSESSION.query(Group.id).filter(Group.group_id == group_id).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: del_member_group_to_db ERROR: Group NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: del_member_group_to_db ERROR: {e}, in checking group.')
        return False

    # 查询成员-群组表中用户-群关系
    try:
        # 用户-群关系已存在, 删除
        __exist_user = NONEBOT_DBSESSION.query(UserGroup). \
            filter(UserGroup.user_id == __user_table_id). \
            filter(UserGroup.group_id == __group_table_id).one()
        NONEBOT_DBSESSION.delete(__exist_user)
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在
        return True
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: del_member_group_to_db ERROR: MultipleResultsFound, '
                         f'user_qq: {user_qq}, group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: del_member_group_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 重置数据库用户状态信息
async def reset_member_status_to_db(user_qq) -> bool:
    user_qq = int(user_qq)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: reset_member_status_to_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: reset_member_status_to_db ERROR: {e}, in checking user.')
        return False

    # 检查用户在假期表中是否存在
    try:
        # 存在则重置假期状态信息
        __exist_user = NONEBOT_DBSESSION.query(Vocation).filter(Vocation.user_id == __user_table_id).one()
        __exist_user.status = 0
        __exist_user.stop_at = None
        __exist_user.reason = None
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则假期表中添加新成员
        try:
            __new_user = Vocation(user_id=__user_table_id, status=0, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_user)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: reset_member_status_to_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: reset_member_status_to_db ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: reset_member_status_to_db, DBSESSION ERROR, error info: {e}.')
        return False


# 重置数据库群组权限
async def reset_group_permissions_to_db(group_id) -> bool:
    group_id = int(group_id)

    # 检查群组是否在表中, 存在则直接更新状态
    try:
        __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).one()
        __exist_group.noitce_permissions = 0
        __exist_group.command_permissions = 0
        __exist_group.admin_permissions = 0
        __exist_group.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        log.logger.warning(f'{__name__}: reset_group_permissions_to_db ERROR: Group NoResultFound.')
        return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: reset_group_permissions_to_db ERROR: MultipleResultsFound, '
                           f'group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: reset_group_permissions_to_db ERROR: {e}, in checking group.')
        return False


# 设置数据库已有群组权限
async def set_group_permissions_to_db(group_id,
                                      noitce_permissions=0, command_permissions=0, admin_permissions=0) -> bool:
    group_id = int(group_id)

    # 检查群组是否在表中, 存在则直接更新状态
    try:
        __exist_group = NONEBOT_DBSESSION.query(Group).filter(Group.group_id == group_id).one()
        __exist_group.noitce_permissions = noitce_permissions
        __exist_group.command_permissions = command_permissions
        __exist_group.admin_permissions = admin_permissions
        __exist_group.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        log.logger.warning(f'{__name__}: set_group_permissions_to_db ERROR: Group NoResultFound.')
        return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: set_group_permissions_to_db ERROR: MultipleResultsFound, '
                           f'group_id: {group_id}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: set_group_permissions_to_db ERROR: {e}, in checking group.')
        return False


# 查询群组权限
async def query_group_permissions_in_db(group_id) -> dict:
    __result = {}
    group_id = int(group_id)

    # 检查群组是否在表中, 存在则直接更新状态
    try:
        __res = NONEBOT_DBSESSION.query(Group.noitce_permissions, Group.command_permissions, Group.admin_permissions). \
            filter(Group.group_id == group_id).one()
        __result['通知'] = __res[0]
        __result['命令'] = __res[1]
        __result['管理命令'] = __res[2]
        return __result
    except NoResultFound:
        log.logger.warning(f'{__name__}: set_group_permissions_to_db ERROR: Group NoResultFound.')
        return __result
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: set_group_permissions_to_db ERROR: MultipleResultsFound, '
                           f'group_id: {group_id}.')
        return __result
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.warning(f'{__name__}: set_group_permissions_to_db ERROR: {e}, in checking group.')
        return __result
