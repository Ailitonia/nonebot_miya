import datetime
import random
import zhdate


async def get_divination_of_thing(divination: str, divination_user: str) -> str:
    # 导入日期和农历
    date_geo = datetime.date.today().strftime('%Y年%m月%d日')
    date_luna = zhdate.ZhDate.today()
    # 用昵称、日期、所求事项生成随机种子
    random.seed(str(divination) + str(divination_user) + str(date_geo) + str(date_luna))
    # 生成求签种子，习惯性按百分比转化
    div_seed = random.random()
    divination_result = div_seed * 100
    # 大吉・中吉・小吉・吉・半吉・末吉・末小吉・凶・小凶・半凶・末凶・大凶
    if divination_result < 5:
        result_text = '大凶'
    elif divination_result < 18:
        result_text = '凶'
    elif divination_result < 33:
        result_text = '小凶'
    elif divination_result < 45:
        result_text = '末吉'
    elif divination_result < 60:
        result_text = '小吉'
    elif divination_result < 75:
        result_text = '中吉'
    elif divination_result < 90:
        result_text = '吉'
    else:
        result_text = '大吉'
    return f'今天是{date_geo}\n{date_luna}\n{divination_user}所求事项：【{divination}】\n\n结果：【{result_text}】'
