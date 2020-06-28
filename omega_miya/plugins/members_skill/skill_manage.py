from omega_miya.database import *
from omega_miya.plugins.members_skill.skil_query import is_skill_exist
from datetime import datetime


async def add_skill_to_db(skill_name, skill_description) -> bool:
    if is_skill_exist(skill_name):
        return False
    else:
        __new_skill = Skill(name=skill_name, description=skill_description, created_at=datetime.now())
        NONEBOT_DBSESSION.add(__new_skill)
        NONEBOT_DBSESSION.commit()
        return True


async def clean_user_skill_in_db(user_qq) -> bool:
    for res in NONEBOT_DBSESSION.query(UserSkill.id).join(User). \
            filter(UserSkill.user_id == User.id). \
            filter(User.qq == user_qq). \
            all():
        __user_skill = NONEBOT_DBSESSION.query(UserSkill).filter(UserSkill.id == res).first()
        NONEBOT_DBSESSION.delete(__user_skill)
        NONEBOT_DBSESSION.commit()
    return True


async def add_user_skill_in_db(user_qq, skill_name, skill_level) -> bool:
    if skill_level == '普通':
        skill_level = 1
    elif skill_level == '熟练':
        skill_level = 2
    elif skill_level == '专业':
        skill_level = 3
    __user_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).first()[0]
    __skill_id = NONEBOT_DBSESSION.query(Skill.id).filter(Skill.name == skill_name).first()[0]
    try:
        if __user_id and __skill_id:
            __new_skill = UserSkill(user_id=__user_id, skill_id=__skill_id,
                                    skill_level=skill_level, created_at=datetime.now())
            NONEBOT_DBSESSION.add(__new_skill)
            NONEBOT_DBSESSION.commit()
            return True
        else:
            return False
    except:
        return False
