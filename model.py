import datetime
import pybrcode
import uuid

import pybrcode.pix

from exceptions import (
    MiniBookApiException, BOOK_NOT_FOUND,
    SALE_NOT_FOUND, PIX_EXCEPTION,
    SALE_UNITIES_NOT_ENOUGH, SALE_IS_EMPTY,
    SALE_CAN_NOT_BE_CANCELED,
    SALE_ALREADY_CONCLUDED
)
from flask_sqlalchemy import SQLAlchemy
from pybrcode.exceptions import (
    PixInvalidKeyException, PixInvalidPayloadException
)
from res import store_pic_from_base64
from sqlalchemy import event, and_

db = SQLAlchemy()

def init_model(app):
    db.init_app(app)
    if db.engine.url.drivername == 'sqlite':
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(conn, _):
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    db.create_all()

def get_uuid() -> str:
    return uuid.uuid4().hex

def get_timestamp() -> datetime:
    return datetime.datetime.now(datetime.UTC)

class BookSale(db.Model):
    __tablename__ = 'books_sales'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='RESTRICT'), 
                        primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), 
                        primary_key=True)
    unities = db.Column(db.Integer, nullable=False, default=1)
    
    book = db.relationship('Book', back_populates='books_sales')
    sale = db.relationship('Sale', back_populates='books_sales')
    
    def toDict(self) -> dict:
        return {
            'book_id': self.book_id,
            'book_title': self.book.title,
            'book_price': self.book.price,
            'unities': self.unities
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    id          = db.Column(db.Integer, primary_key=True)
    total       = db.Column(db.Integer, nullable=False)
    sale_ts     = db.Column(db.DateTime, default=get_timestamp)
    uuid        = db.Column(db.String(32), default=get_uuid)
    concluded   = db.Column(db.Boolean, default=False)
    books_sales  = db.relationship('BookSale', cascade='all, delete-orphan')
    
    @staticmethod
    def fetch(uuid:str) -> 'Sale':
        sale = Sale.query.filter_by(uuid=uuid).first()
        if not sale:
            raise MiniBookApiException(SALE_NOT_FOUND)
        return sale
    @staticmethod
    def confirm(uuid:str):
        sale = Sale.fetch(uuid)
        if sale.concluded:
            raise MiniBookApiException(SALE_ALREADY_CONCLUDED)
        for bs in sale.books_sales:
            bs.book.unities -= bs.unities
            if bs.book.unities < 0:
                raise MiniBookApiException(
                    SALE_UNITIES_NOT_ENOUGH,
                    f'Book: {bs.book.title}'
                )
        sale.concluded = True
        db.session.commit()
    @staticmethod
    def cancel(uuid:str):
        sale = Sale.fetch(uuid)
        if not sale.concluded:
            db.session.delete(sale)
            db.session.commit()
        else:
            raise MiniBookApiException(SALE_CAN_NOT_BE_CANCELED)
    @staticmethod
    def refresh():
        time_limit = \
            datetime.datetime.now(datetime.UTC) - \
            datetime.timedelta(minutes=30)
        sales = Sale.query.filter(
            and_(
                Sale.sale_ts < time_limit,
                Sale.concluded == False
            )
        ).all()
        if sales:
            for s in sales:
                db.session.delete(s)
            db.session.commit()
    @staticmethod
    def _fill_books_sale_data(books_sale_data:dict[str]) -> dict:
        book_ids = set(books_sale_data)
        books = Book.query.filter(Book.id.in_(book_ids)).all() \
                if len(book_ids) > 0 else []
        if len(books) != len(book_ids):
            missing_ids = book_ids - {b.id for b in books}
            raise MiniBookApiException(
                BOOK_NOT_FOUND, f'ids: {str(missing_ids)}'
            )
        ret = {}
        for b in books:
            ret[b.id] = {
                'book': b, 'unities': books_sale_data[str(b.id)]
            }
        return ret
    @staticmethod
    def new(books_sale_data:dict[int]) -> 'Sale':
        '''
            example:
            -------
            books_sale_data = {"1": 2, "0": 3, "1":1}
        '''
        if len(books_sale_data) < 1:
            raise MiniBookApiException(SALE_IS_EMPTY)
        new_bsd = Sale._fill_books_sale_data(books_sale_data)
        sale = Sale()
        sale.total = 0
        for bs in new_bsd.values():
            unities = bs['unities']
            if unities > 0:
                book = bs['book']
                sale.total += unities * book.price
                sale.books_sales.append(
                    BookSale(book=book, unities=unities)
                )
        db.session.add(sale)
        db.session.commit()
        return sale
    def getPix(self, pix_name:str, pix_key:str) -> pybrcode.pix.Pix:
        try:
            return pybrcode.pix.generate_simple_pix(
                fullname=pix_name, key=pix_key,
                city="None", value=self.total/100.0,
                description='Buying books.'
            )
        except (
            PixInvalidKeyException,
            PixInvalidPayloadException
        ) as e:
            raise MiniBookApiException(PIX_EXCEPTION, str(e))            
    def toDict(self) -> dict:
        return {
            'id': self.id,
            'uuid': self.uuid,
            'total': self.total,
            'sale_ts': self.sale_ts,
            'books_sales': [bs.toDict() for bs in self.books_sales]
        }

class Book(db.Model):
    __tablename__ = 'books'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(192), nullable=False)
    author      = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price       = db.Column(db.Integer, nullable=False)
    year        = db.Column(db.Integer, nullable=False)
    unities     = db.Column(db.Integer, nullable=False)
    img_res     = db.Column(db.String(32), nullable=True)
    books_sales  = db.relationship('BookSale')
    
    @staticmethod
    def new(title:str, author:str, price:int,
            unities: int, year:int, description:str=None,
            img_b64:str=None) -> 'Book':
        book = Book()
        book.title = title
        book.author = author
        book.price = price
        book.year = year
        book.unities = unities
        book.description = description
        book.img_res = store_pic_from_base64(img_b64)
        db.session.add(book)
        db.session.commit()
        return book
    def toDict(self) -> dict:
        return {
            'id'          : self.id,
            'title'       : self.title,
            'author'      : self.author,
            'description' : self.description,
            'price'       : self.price,
            'year'        : self.year,
            'unities'     : self.unities,
            'img_res'     : self.img_res
        }
