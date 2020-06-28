from omega_miya.database import *
from datetime import datetime


async def check_member_vocation(user_qq) -> bool:
    __res_user_id = NONEBOT_DBSESSION.query(User.id).filter(User.qq == user_qq).first()
    if not __res_user_id:
        return False
    __user_id = __res_user_id[0]
    __result = NONEBOT_DBSESSION.query(Vocation).filter(Vocation.user_id == __user_id).first()
    if not __result:
        return False
    if __result.status == 1 and datetime.now() >= __result.stop_at:
        try:
            __result.status = 0
            __result.stop_at = None
            __result.reason = None
            __result.updated_at = datetime.now()
            NONEBOT_DBSESSION.commit()
            return True
        except:
            return False
    else:
        return False
