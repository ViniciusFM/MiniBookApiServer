import base64
import binascii
import exceptions
import os
import PIL
import uuid

from exceptions import MiniBookApiException
from io import BytesIO
from paths import *
from PIL import Image

_MAX_H, _MAX_W  = 1080, 1080 # max image pixel

def init_img_res():
    if not os.path.exists(IMG_RES):
        os.makedirs(IMG_RES)

def store_pic_from_base64(pic_b64:str|None) -> str|None:
    '''
        Returns the picture uuid resource or None if pic_b64 = None.
        Raises MiniBookApiException
    '''
    if not pic_b64:
        return None
    try:
        resuuid = uuid.uuid4().hex
        fpath = os.path.join(IMG_RES, f'{resuuid}.jpg')
        with Image.open(BytesIO(base64.b64decode(pic_b64))) as img:
            if(img.height <= _MAX_H and img.width <= _MAX_W):
                rgb_img = img.convert('RGB')
                rgb_img.save(fpath, 'JPEG')
            else:
                raise MiniBookApiException(
                    exceptions.INVALID_IMG_RESOLUTION,
                    extra=f'max: {_MAX_W}x{_MAX_H} pixels'
                )
    except binascii.Error as e:
        raise MiniBookApiException(
            exceptions.INVALID_B64_FORMAT,
            extra=str(e)
        )
    except (FileNotFoundError, PIL.UnidentifiedImageError) as e:
        raise MiniBookApiException(
            exceptions.UNKNOW_IMG_CRETION_PROBLEM,
            extra=str(e)
        )
    return resuuid

def get_image_path(resuuid:str) -> str|None:
    '''
        Returns path.
        raises MiniBookApiException
    '''
    path = os.path.join(IMG_RES, f'{resuuid}.jpg')
    if os.path.exists(path):
        return path
    else:
        raise MiniBookApiException(exceptions.IMG_NOT_FOUND)
