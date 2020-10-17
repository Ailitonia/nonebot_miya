import datetime
import random
import zhdate
from .almanac_text import do, saying, vtb


async def get_almanac_for_dd(user) -> str:
    # 日期与农历
    almanac_geo = datetime.date.today().strftime('%Y年%m月%d日')
    almanac_luna = zhdate.ZhDate.chinese(zhdate.ZhDate.today())
    # 初始化随机种子
    random_seed = hash(str([user, almanac_geo, almanac_luna]))
    random.seed(random_seed)
    # 宜做和不宜做
    dd_do_and_not = random.sample(do, k=4)
    # 名句与DD
    dd_saying = random.sample(saying, k=1)
    dd_vtb = random.sample(vtb, k=1)

    msg = f'今天是{almanac_geo}\n农历{almanac_luna}\n\n{user}今天:\n' \
          f"【宜】\n{dd_do_and_not[0]['name']} —— {dd_do_and_not[0]['good']}\n" \
          f"{dd_do_and_not[2]['name']} —— {dd_do_and_not[2]['good']}\n\n" \
          f"【不宜】\n{dd_do_and_not[1]['name']} —— {dd_do_and_not[1]['bad']}\n" \
          f"{dd_do_and_not[3]['name']} —— {dd_do_and_not[3]['bad']}\n\n" \
          f"今日宜D：{dd_vtb[0]}\n\n“{dd_saying[0]}”"

    return msg
