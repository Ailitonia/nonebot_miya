from nonebot import log
from omega_miya.database import *
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


async def check_member_vocation(user_qq) -> bool:
    user_qq = int(user_qq)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: {e}, in checking user.')
        return False

    # 检查用户请假状态
    try:
        __result = NONEBOT_DBSESSION.query(Vocation).filter(Vocation.user_id == __user_table_id).one()
        if __result.status == 1 and datetime.now() >= __result.stop_at:
            return True
        else:
            return False
    except NoResultFound:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: NoResultFound, user_qq: {user_qq}.')
        return False
    except MultipleResultsFound:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.warning(f'{__name__}: check_member_vocation, DBSESSION ERROR, error info: {e}.')
        return False


async def clear_member_vocation(user_qq) -> bool:
    user_qq = int(user_qq)

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: check_member_vocation ERROR: {e}, in checking user.')
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
            log.logger.error(f'{__name__}: check_member_vocation, DBSESSION ERROR, error info: {e}.')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: check_member_vocation ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: check_member_vocation, DBSESSION ERROR, error info: {e}.')
        return False
