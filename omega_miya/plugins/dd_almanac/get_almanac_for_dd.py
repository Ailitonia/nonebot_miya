import datetime
import random
import zhdate
from .almanac_text import do, do_not, saying, vtb


async def get_almanac_for_dd(dd_almanac: str) -> str:
    # 日期与农历
    almanac_geo = datetime.date.today().strftime('%Y年%m月%d日')
    almanac_luna = zhdate.ZhDate.today()
    # 用日期和昵称生成随机种子
    random.seed(str(dd_almanac) + str(almanac_geo) + str(almanac_luna))
    almanac_seed = random.random()
    do_seed = almanac_seed
    do_not_seed = 1 - almanac_seed
    # 宜做
    dd_do1 = str(do[int(do_seed * len(do))])
    dd_do2 = str(do[int(do_seed * len(do) / 2)])
    # 不宜做
    dd_do_not1 = str(do_not[int(do_not_seed * len(do_not))])
    dd_do_not2 = str(do_not[int(do_not_seed * len(do_not) / 2)])
    # 名句与DD
    dd_saying = str(saying[int(do_seed * len(saying))])
    dd_vtb = str(vtb[int(do_not_seed * len(vtb))])

    return f'今天是{almanac_geo}\n{almanac_luna}\n\n“{dd_saying}”\n\n{dd_almanac}今天:\n' \
           f'【宜】\n{dd_do1}\n{dd_do2}\n\n【不宜】\n{dd_do_not1}\n{dd_do_not2}\n\n今日宜D：{dd_vtb}'
