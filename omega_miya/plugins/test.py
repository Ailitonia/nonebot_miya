import nonebot
from nonebot import log

bot = nonebot.get_bot()


@nonebot.scheduler.scheduled_job(
    'cron',
    # year=None,
    # month=None,
    # day=None,
    # week=None,
    # day_of_week=None,
    hour='*/1',
    # minute='*/1',
    # second=None,
    # start_date=None,
    # end_date=None,
    # timezone=None,
    coalesce=True,
    misfire_grace_time=5
)
async def import_setu():
    log.logger.info(f"{__name__}: start import setu - 9 db")
    group_id = 1121459110
    try:
        await bot.send_group_msg(group_id=group_id, message=r'/来点涩图 import')
    except Exception as e:
        log.logger.info(f"{__name__}: task failed, {e}")
