from nonebot import log
from omega_miya.database import *
from omega_miya.plugins.members_skill.skil_query import is_skill_exist
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


async def add_skill_to_db(skill_name, skill_description) -> bool:
    if is_skill_exist(skill_name):
        return False
    else:
        try:
            __new_skill = Skill(name=skill_name, description=skill_description, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_skill)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: DBSESSION ERROR, error info: {e}.')
            return False


async def clean_user_skill_in_db(user_qq) -> bool:
    user_qq = int(user_qq)

    for res in NONEBOT_DBSESSION.query(UserSkill.id).join(User). \
            filter(UserSkill.user_id == User.id). \
            filter(User.qq == user_qq). \
            all():
        try:
            __user_skill = NONEBOT_DBSESSION.query(UserSkill).filter(UserSkill.id == res).one()
            NONEBOT_DBSESSION.delete(__user_skill)
            NONEBOT_DBSESSION.commit()
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: clean_user_skill_in_db, DBSESSION ERROR, error info: {e}.')
            continue
    return True


async def add_user_skill_in_db(user_qq, skill_name, skill_level) -> bool:
    if skill_level == '普通':
        skill_level = 1
    elif skill_level == '熟练':
        skill_level = 2
    elif skill_level == '专业':
        skill_level = 3

    # 检查用户是否在表中，查这个用户在用户表中的id(不是qq号)
    try:
        __user_table_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_user_skill_in_db ERROR: User NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_user_skill_in_db ERROR: {e}, in checking user.')
        return False

    # 检查技能是否在表中，查这个技能在技能表中的id
    try:
        __skill_id = NONEBOT_DBSESSION.query(Skill.id).filter(Skill.name == skill_name).one()[0]
    except NoResultFound:
        log.logger.warning(f'{__name__}: add_user_skill_in_db ERROR: Skill NoResultFound.')
        return False
    except Exception as e:
        log.logger.warning(f'{__name__}: add_user_skill_in_db ERROR: {e}, in checking skill')
        return False

    # 查询成员是否具备该技能
    try:
        # 成员已具备该技能, 更新技能等级
        __exist_user_skill = NONEBOT_DBSESSION.query(UserSkill). \
            filter(UserSkill.user_id == __user_table_id). \
            filter(UserSkill.skill_id == __skill_id).one()
        __exist_user_skill.skill_level = skill_level
        __exist_user_skill.updated_at = datetime.now()
        NONEBOT_DBSESSION.commit()
        return True
    except NoResultFound:
        # 不存在关系则添加新技能
        try:
            __new_skill = UserSkill(user_id=__user_table_id, skill_id=__skill_id,
                                    skill_level=skill_level, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_skill)
            NONEBOT_DBSESSION.commit()
            return True
        except Exception as e:
            NONEBOT_DBSESSION.rollback()
            log.logger.error(f'{__name__}: add_user_skill_in_db, DBSESSION ERROR, error info: {e}, '
                             f'failed to add new skill')
            return False
    except MultipleResultsFound:
        log.logger.error(f'{__name__}: add_user_skill_in_db ERROR: MultipleResultsFound, user_qq: {user_qq}.')
        return False
    except Exception as e:
        NONEBOT_DBSESSION.rollback()
        log.logger.error(f'{__name__}: add_user_skill_in_db, DBSESSION ERROR, error info: {e}.')
        return False
