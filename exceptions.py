from flask import jsonify, Response

MINI_BOOK_API_EXCP          = ('Mini Book API Exception', 0, 400)
INVALID_BODY                = ('Invalid request body.', 1, 400)
TOKEN_REQUIRED              = ('A token is required to proceed this operation', 2, 403)
TOKEN_INVALID               = ('The token is invalid or expired', 3, 403)
BOOK_NOT_FOUND              = ('Book not found.', 4, 404)
INVALID_B64_FORMAT          = ('Invalid base64 encoding.', 5, 406)
UNKNOW_IMG_CRETION_PROBLEM  = ('Problem during image creation.', 6, 400)
IMG_NOT_FOUND               = ('Image resource not found.', 7, 404)
INVALID_IMG_RESOLUTION      = ('Invalid image resolution.', 8, 406)
SALE_NOT_FOUND              = ('Sale not found.', 9, 404)
SALE_UNITIES_NOT_ENOUGH     = ('Not enough unities for sale.', 10, 422)
SALE_IS_EMPTY               = ('Sale does not have any books.', 11, 422)
SALE_CAN_NOT_BE_CANCELED    = ('This sale can not be canceled, because it is already concluded.', 12, 422)
SALE_ALREADY_CONCLUDED      = ('This sale is already concluded.', 13, 422)
PIX_EXCEPTION               = ('Something went wrong on generating pix qrcode. Contact admin.', 14, 500)

def jsonifyFailure(excp:tuple, extra:str=None) -> Response:
    ret = {
        'errmsg'    : excp[0],
        'errcode'   : excp[1],
        'extra'     : extra
    }
    return jsonify(ret), excp[2]

class MiniBookApiException(Exception):
    def __init__(self, excp:tuple=MINI_BOOK_API_EXCP, extra:str = None):
        super().__init__(excp[0])
        self.excp = excp
        self.extra = extra
    def jsonify(self) -> Response:
        return jsonifyFailure(self.excp, self.extra)
