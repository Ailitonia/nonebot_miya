import os
import base64
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from nonebot import log


# 图片转base64
async def pic_2_base64(pic_path) -> str:
    with open(pic_path, 'rb') as f:
        b64 = base64.b64encode(f.read())
    b64 = str(b64, encoding='utf-8')
    b64 = 'base64://' + b64
    return b64


async def get_image(url: str):
    timeout_count = 0
    while timeout_count < 3:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/83.0.4103.116 Safari/537.36'}
                async with session.get(url=url, headers=headers, timeout=timeout) as resp:
                    __res = await resp.read()
            return __res
        except Exception as err:
            log.logger.warning(f'Stick_maker: get_image ERROR: {err}. '
                               f'Occurred in try {timeout_count + 1} using paras: {url}')
        finally:
            timeout_count += 1
    else:
        log.logger.warning(f'Stick_maker: get_image ERROR: Timeout {timeout_count}, using paras: {url}')
        return None


async def sticker_maker_main(url: str, temp: str, text: str):
    origin_image_f = BytesIO()
    try:
        origin_image_f.write(await get_image(url=url))
    except Exception as e:
        log.logger.error(f'Stick_maker: sticker_maker ERROR: {e}')
        return None
    # 字体路径
    plugin_src_path = os.path.dirname(__file__)
    font_path = os.path.join(plugin_src_path, 'msyhbd.ttc')
    sticker_path = os.path.join(plugin_src_path, 'sticker',
                                f"{temp}_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.jpg")
    # 调整图片大小（宽度512像素）
    make_image = Image.open(origin_image_f)
    image_resize_width = 512
    image_resize_height = 512 * make_image.height // make_image.width
    make_image = make_image.resize((image_resize_width, image_resize_height))
    # 调用模板处理图片
    if temp == 'default':
        make_image = stick_maker_temp_default(text=text, image_file=make_image, font_path=font_path,
                                              image_wight=image_resize_width, image_height=image_resize_height)
    elif temp == 'littleangel':
        make_image = stick_maker_temp_littleangel(text=text, image_file=make_image, font_path=font_path,
                                                  image_wight=image_resize_width, image_height=image_resize_height)
    # 输出图片
    make_image.save(sticker_path, 'JPEG')
    origin_image_f.close()
    return sticker_path


def stick_maker_temp_default(text: str, image_file: bytes, font_path: str, image_wight: int, image_height: int):
    # 处理图片
    draw = ImageDraw.Draw(image_file)
    font_size = 72
    font = ImageFont.truetype(font_path, font_size)
    text_w, text_h = font.getsize_multiline(text)
    while text_w >= image_wight:
        font_size = font_size * 3 // 4
        font = ImageFont.truetype(font_path, font_size)
        text_w, text_h = font.getsize_multiline(text)
    # 计算居中文字位置
    text_coordinate = (((image_wight - text_w) // 2), 9 * (image_height - text_h) // 10)
    # 为文字设置黑边
    text_b_resize = 4
    if font_size >= 72:
        text_b_resize = 4
    elif font_size >= 36:
        text_b_resize = 3
    elif font_size >= 24:
        text_b_resize = 2
    elif font_size < 12:
        text_b_resize = 1
    text_coordinate_b1 = (text_coordinate[0] + text_b_resize, text_coordinate[1])
    text_coordinate_b2 = (text_coordinate[0] - text_b_resize, text_coordinate[1])
    text_coordinate_b3 = (text_coordinate[0], text_coordinate[1] + text_b_resize)
    text_coordinate_b4 = (text_coordinate[0], text_coordinate[1] - text_b_resize)
    draw.multiline_text(text_coordinate_b1, text, font=font, fill=(0, 0, 0))
    draw.multiline_text(text_coordinate_b2, text, font=font, fill=(0, 0, 0))
    draw.multiline_text(text_coordinate_b3, text, font=font, fill=(0, 0, 0))
    draw.multiline_text(text_coordinate_b4, text, font=font, fill=(0, 0, 0))
    # 白字要后画，后画的在上层，不然就是黑滋在上面挡住了
    draw.multiline_text(text_coordinate, text, font=font, fill=(255, 255, 255))
    return image_file


def stick_maker_temp_littleangel(text: str, image_file: bytes, font_path: str, image_wight: int, image_height: int):
    # 处理图片
    background_w = image_wight + 100
    background_h = image_height + 230
    background = Image.new(mode="RGB", size=(background_w, background_h), color=(255, 255, 255))
    # 处理粘贴位置 上留100像素，下留130像素
    text_coordinate = (((background_w - image_wight) // 2), 100)
    background.paste(image_file, text_coordinate)
    draw = ImageDraw.Draw(background)

    font_down_1 = ImageFont.truetype(font_path, 48)
    text_down_1 = r'非常可爱！简直就是小天使'
    text_down_1_w, text_down_1_h = font_down_1.getsize(text_down_1)
    text_down_1_coordinate = (((background_w - text_down_1_w) // 2), background_h - 120)
    draw.text(text_down_1_coordinate, text_down_1, font=font_down_1, fill=(0, 0, 0))

    font_down_2 = ImageFont.truetype(font_path, 26)
    text_down_2 = r'她没失踪也没怎么样  我只是觉得你们都该看一下'
    text_down_2_w, text_down_2_h = font_down_2.getsize(text_down_2)
    text_down_2_coordinate = (((background_w - text_down_2_w) // 2), background_h - 60)
    draw.text(text_down_2_coordinate, text_down_2, font=font_down_2, fill=(0, 0, 0))

    font_size_up = 72
    font_up = ImageFont.truetype(font_path, font_size_up)
    text_up = f'请问你们看到{text}了吗？'
    text_up_w, text_up_h = font_up.getsize(text_up)
    while text_up_w >= background_w:
        font_size_up = font_size_up * 5 // 6
        font_up = ImageFont.truetype(font_path, font_size_up)
        text_up_w, text_up_h = font_up.getsize(text_up)
    # 计算居中文字位置
    text_up_coordinate = (((background_w - text_up_w) // 2), 25)
    draw.text(text_up_coordinate, text_up, font=font_up, fill=(0, 0, 0))
    return background
