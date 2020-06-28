from omega_miya.database import *


# 返回该名称的技能是否在技能表中存在
def is_skill_exist(skill_name) -> bool:
    __result = NONEBOT_DBSESSION.query(Skill.name).filter(Skill.name == skill_name).first()
    if __result:
        return True
    else:
        return False


# 以列表形式返回技能表中所有技能的名字
def query_skill_list() -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(Skill.name).order_by(Skill.id).all():
        __result.append(__res[0])
    return __result


# 以列表形式返回查询者的所有技能
def query_my_skill_list(user_qq) -> list:
    __result = []
    for __res in NONEBOT_DBSESSION.query(UserSkill.skill_level, Skill.name). \
            join(User).join(Skill). \
            filter(UserSkill.user_id == User.id). \
            filter(UserSkill.skill_id == Skill.id). \
            filter(User.qq == user_qq). \
            all():
        __result.append(__res)
    if __result:
        return __result
    else:
        return []
