import base64
import aiohttp
from io import BytesIO
from nonebot import log


# 图片转base64
async def pic_2_base64(url: str) -> str:
    async def get_image(pic_url: str):
        timeout_count = 0
        while timeout_count < 3:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                                             'Chrome/83.0.4103.116 Safari/537.36'}
                    async with session.get(url=pic_url, headers=headers, timeout=timeout) as resp:
                        __res = await resp.read()
                return __res
            except Exception as err:
                log.logger.warning(f'{__name__}: error info: {err}. '
                                   f'Occurred in try {timeout_count + 1} using paras: {pic_url}')
            finally:
                timeout_count += 1
        else:
            log.logger.warning(f'{__name__}: error info: Exceeds the set timeout time. '
                               f'Timeout in {timeout_count} times, using paras: {pic_url}')
            return None

    origin_image_f = BytesIO()
    try:
        origin_image_f.write(await get_image(pic_url=url))
    except Exception as e:
        log.logger.error(f'{__name__}: error info: {e}.')
        return ''
    b64 = base64.b64encode(origin_image_f.getvalue())
    b64 = str(b64, encoding='utf-8')
    b64 = 'base64://' + b64
    origin_image_f.close()
    return b64
