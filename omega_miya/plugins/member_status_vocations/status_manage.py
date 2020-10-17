from omega_miya.database import *
from nonebot import log
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


# 设置数据库用户状态信息
async def set_my_status_in_db(user_qq, user_status) -> bool:
    user_qq = int(user_qq)
    user_status = int(user_status)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: set_my_status_in_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: set_my_status_in_db ERROR: {e}, in checking user.')
        return False

    # 检查用户在假期表中是否存在
    try:
        # 存在则重置假期状态信息
        __exist_user = NONEBOT_DBSESSION.query(Vocation).filter(Vocation.user_id == __user_table_id).one()
        __exist_user.status = user_status
        __exist_user.stop_at = None
        __exist_user.reason = None
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则假期表中添加新成员
        try:
            __new_status = Vocation(user_id=__user_table_id, status=user_status, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_status)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: set_my_status_in_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: set_my_status_in_db ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: set_my_status_in_db, DBSESSION ERROR, error info: {e}.')
        return False


async def set_my_vocation_in_db(user_qq, vocation_times, reason=None) -> bool:
    user_qq = int(user_qq)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: set_my_vocation_in_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: set_my_vocation_in_db ERROR: {e}, in checking user.')
        return False

    # 检查用户在假期表中是否存在
    try:
        # 如果状态表中已存在, 则修改状态,包括清空请假时间等字段
        __exist_user = NONEBOT_DBSESSION.query(Vocation).filter(Vocation.user_id == __user_table_id).one()
        __exist_user.status = 1
        __exist_user.stop_at = vocation_times
        __exist_user.reason = reason
        __exist_user.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在则假期表中添加新成员
        try:
            __new_status = Vocation(user_id=__user_table_id, status=1,
                                    stop_at=vocation_times, reason=reason, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_status)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: set_my_vocation_in_db, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: set_my_vocation_in_db ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: set_my_vocation_in_db, DBSESSION ERROR, error info: {e}.')
        return False


async def query_my_status(user_qq) -> str:
    user_qq = int(user_qq)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: query_my_status ERROR: User NoResultFound.')
        return 'error'
    except Exception as e:
        log.logger.warning(f'{__name__}: query_my_status ERROR: {e}, in checking user.')
        return 'error'

    try:
        __result = NONEBOT_DBSESSION.query(Vocation.status).filter(Vocation.user_id == __user_table_id).one()[0]
        if __result == 0:
            return '空闲中'
        elif __result == 1:
            return '请假中'
        elif __result == 2:
            return '工作中'
    except NoResultFound:
        log.logger.warning(f'{__name__}: query_my_status ERROR: User NoResultFound.')
        return 'error'
    except Exception as e:
        log.logger.error(f'{__name__}: query_my_status, DBSESSION ERROR, error info: {e}.')
        return 'error'


async def query_my_vocation(user_qq) -> str:
    user_qq = int(user_qq)

    if await query_my_status(user_qq) == '请假中':
        # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
        try:
            __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
        except NoResultFound:
            log.logger.warning(f'{__name__}: query_my_vocation ERROR: User NoResultFound.')
            return 'error'
        except Exception as e:
            log.logger.warning(f'{__name__}: query_my_vocation ERROR: {e}, in checking user.')
            return 'error'

        # 查询假期结束时间
        try:
            __result = NONEBOT_DBSESSION.query(Vocation.stop_at).filter(Vocation.user_id == __user_table_id).one()[0]
            return __result
        except NoResultFound:
            log.logger.warning(f'{__name__}: query_my_vocation ERROR: User NoResultFound.')
            return 'error'
        except Exception as e:
            log.logger.error(f'{__name__}: query_my_vocation, DBSESSION ERROR, error info: {e}.')
            return 'error'
    else:
        return 'not_in_vocation'


async def query_who_not_busy(group_id) -> dict:
    __result = {}
    # 查询该群组中所有没有假的人
    try:
        for __res_vocation in NONEBOT_DBSESSION.query(User.id, UserGroup.user_group_nickname). \
                join(Vocation).join(UserGroup).join(Group). \
                filter(User.id == Vocation.user_id). \
                filter(User.id == UserGroup.user_id). \
                filter(UserGroup.group_id == Group.id). \
                filter(Vocation.status == 0). \
                filter(Group.group_id == group_id). \
                all():
            # 这个人的id和昵称
            __user_id = __res_vocation[0]
            __user_aliasname = __res_vocation[1]
            # 查询这个人的技能
            __user_skill_list = ''
            __res_skill = NONEBOT_DBSESSION.query(Skill.name). \
                join(UserSkill).join(User). \
                filter(Skill.id == UserSkill.skill_id). \
                filter(UserSkill.user_id == User.id). \
                filter(User.id == __user_id). \
                all()
            if __res_skill:
                for __skill in __res_skill:
                    __user_skill_list += '/' + __skill[0]
            else:
                __user_skill_list = '/暂无技能'
            __result[__user_aliasname] = __user_skill_list
        return __result
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
        return {'error': e}


async def query_which_skill_not_busy(skill_name, group_id) -> list:
    __result = []
    # 查询这这个技能有那些人会
    try:
        for __res_member in NONEBOT_DBSESSION.query(User.id, UserGroup.user_group_nickname). \
                join(UserSkill).join(Skill).join(UserGroup).join(Group). \
                filter(User.id == UserSkill.user_id). \
                filter(UserSkill.skill_id == Skill.id). \
                filter(User.id == UserGroup.user_id). \
                filter(UserGroup.group_id == Group.id). \
                filter(Skill.name == skill_name). \
                filter(Group.group_id == group_id). \
                all():
            # 查这个人是不是空闲
            __user_id = __res_member[0]
            __user_status = NONEBOT_DBSESSION.query(Vocation.status).filter(Vocation.user_id == __user_id).one()[0]
            __user_aliasname = __res_member[1]
            # 如果空闲则把这个人昵称放进结果列表里面
            if __user_status == 0:
                __result.append(__user_aliasname)
        return __result
    except NoResultFound:
        log.logger.error(f'{__name__}: query_which_skill_not_busy ERROR: User NoResultFound.')
        return ['error']
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: query_which_skill_not_busy ERROR: User MultipleResultsFound.')
        return ['error']
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
        return ['error']


# 查所有在休假的人
async def query_who_in_vocation(group_id) -> dict:
    __result = {}
    # 查询所有没有假的人
    try:
        for __res_vocation in NONEBOT_DBSESSION.query(User.id, UserGroup.user_group_nickname, Vocation.stop_at). \
                join(Vocation). \
                filter(User.id == Vocation.user_id). \
                filter(User.id == UserGroup.user_id). \
                filter(UserGroup.group_id == Group.id). \
                filter(Vocation.status == 1). \
                filter(Group.group_id == group_id). \
                all():
            # 这个人的id和昵称
            __user_id = __res_vocation[0]
            __user_aliasname = __res_vocation[1]
            # 查询这个人放假截止时间
            __user_vocation_stop_at = __res_vocation[2]
            __result[__user_aliasname] = __user_vocation_stop_at
        return __result
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
        return {'error': e}
