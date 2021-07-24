import base64
from io import BytesIO
from PIL import Image, ImageFilter


# 图片转base64
def pic_2_base64(pic_path) -> str:
    with open(pic_path, 'rb') as f:
        b64 = base64.b64encode(f.read())
    b64 = str(b64, encoding='utf-8')
    b64 = 'base64://' + b64
    return b64


# 图片高斯模糊
def blur_illust(b64image: str) -> str:
    origin_image_f = BytesIO()
    # 解码b64图片
    b64image = b64image[9:]
    bytesimage = base64.b64decode(b64image)
    origin_image_f.write(bytesimage)

    # 处理图片
    mk_image = Image.open(origin_image_f)
    gaussianblur_radius = mk_image.width // 100
    blur_image = mk_image.filter(ImageFilter.GaussianBlur(radius=gaussianblur_radius))

    # 保存处理后的图片
    blur_image_f = BytesIO()
    blur_image.save(blur_image_f, format="PNG")
    origin_image_f.close()

    # 输出b64图片
    b64 = base64.b64encode(blur_image_f.getvalue())
    b64 = str(b64, encoding='utf-8')
    b64 = 'base64://' + b64
    origin_image_f.close()

    return b64
