import base64


# 图片转base64
def pic_2_base64(pic_path) -> str:
    with open(pic_path, 'rb') as f:
        b64 = base64.b64encode(f.read())
    b64 = str(b64, encoding='utf-8')
    b64 = 'base64://' + b64
    return b64
