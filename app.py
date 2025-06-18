import exceptions as excp
import json
import time

from exceptions import (
    MiniBookApiException, INVALID_BODY
)
from flask import (
    Flask, request, jsonify, request,
    send_file, Response, render_template
)
from functools import wraps
from model import (
    init_model, Book, Sale
)
from res import (
    init_img_res, CONFIGFILE,
    get_image_path
)

def create_app() -> Flask:
    _app = Flask(__name__)
    with _app.app_context():
        with open(CONFIGFILE, 'r') as cfg:
            cfg_d = json.load(cfg)
            _app.config.update(cfg_d)
        init_model(_app)
        init_img_res()
    return _app
app = create_app()

def auth_required(admin_only:bool=False):
    def decorator(f):
        @wraps(f)
        def inject(*args, **kwargs):
            Sale.refresh()
            try:
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    raise excp.MiniBookApiException(excp.TOKEN_REQUIRED)
                token = auth_header.split('Bearer ')[1]
                token_type = 'TOKEN_ADMIN' if admin_only else 'TOKEN'
                if token != app.config[token_type]:
                    raise excp.MiniBookApiException(excp.TOKEN_INVALID)
                return f(*args, **kwargs)
            except excp.MiniBookApiException as e:
                return e.jsonify()
        return inject
    return decorator

# --- PAGE PROVIDING

@app.route('/', methods=['GET'])
def index():
    books = Book.query.all()
    book_list = []
    for b in books:
        book_list.append(b.toDict())
    return render_template('index.html', 
                           timenow=int(time.time()), 
                           book_list=sorted(book_list, key=lambda b: b['title']),
                           str=str)

# --- GET ROUTES

@app.route('/img/<string:img_res>', methods=['GET'])
def get_img(img_res:str):
    try:
        return send_file(get_image_path(img_res))
    except MiniBookApiException as e:
        return e.jsonify()

@app.route('/book/ls', methods=['GET'])
def list_books():
    books = Book.query.all()
    ret = []
    for b in books:
        ret.append(b.toDict())
    return jsonify(ret)

@app.route('/sale/ls', methods=['GET'])
@auth_required()
def list_sales():
    sales = Sale.query.all()
    ret = []
    for s in sales:
        ret.append(s.toDict())
    return jsonify(ret)

# --- POST ROUTES

@app.route('/book/new', methods=['POST'])
@auth_required(admin_only=True)
def new_book():
    try:
        body = request.get_json()
        if(len({'title', 'author', 'price', 
            'year', 'unities', 'publisher'} - set(body)) > 0):
            raise MiniBookApiException(INVALID_BODY)
        book = Book.new(
            body['title'],
            body['author'],
            body['publisher'],
            body['price'],
            body['unities'],
            body['year'],
            body['description'] 
                if 'description' in body else None,
            body['img'] 
                if 'img' in body else None
        )
        return jsonify(book.toDict())
    except MiniBookApiException as e:
        return e.jsonify()

@app.route('/sale/new', methods=['POST'])
@auth_required()
def new_sale():
    try:
        body = request.get_json()
        if not 'books_sale_data' in body:
            raise MiniBookApiException(INVALID_BODY)
        sale = Sale.new(body['books_sale_data'])
        pix = sale.getPix(
            app.config['PIX_NAME'],
            app.config['PIX_KEY']
        )
        ret = sale.toDict()
        ret.update({
            'pix_b64': pix.toBase64(),
            'pix_str': str(pix)
        })
        return jsonify(ret)
    except MiniBookApiException as e:
        return e.jsonify()

# --- DELETE ROUTES

@app.route('/sale/cancel', methods=['DELETE'])
@auth_required()
def cancel_sale():
    try:
        body = request.get_json()
        if not 'sale_uuid' in body:
            raise MiniBookApiException(INVALID_BODY)
        Sale.cancel(body['sale_uuid'])
        return Response(status=200)
    except MiniBookApiException as e:
        return e.jsonify()

# --- PUT ROUTES

@app.route('/sale/confirm', methods=['PUT'])
@auth_required()
def confirm_sale():
    try:
        body = request.get_json()
        if not 'sale_uuid' in body:
            raise MiniBookApiException(INVALID_BODY)
        Sale.confirm(body['sale_uuid'])
        return Response(status=200)
    except MiniBookApiException as e:
        return e.jsonify()