# -*- coding: utf-8 -*-

from flask import Flask
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList, ResourceRelationship
from flask_rest_jsonapi.exceptions import ObjectNotFound
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields

# Create the Flask application
app = Flask(__name__)
app.config['DEBUG'] = True


# Initialize SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


# Create data storage
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    author = db.Column(db.String)
    publish_date = db.Column(db.Date)
    isbn = db.Column(db.String)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    book = db.relationship('Book', backref=db.backref('reviews'))

db.create_all()


# Create logical data abstraction (same as data storage for this first example)
class BookSchema(Schema):
    class Meta:
        type_ = 'book'
        self_view = 'book_detail'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'book_list'

    id = fields.Integer(as_string=True, dump_only=True)
    name = fields.Str(required=True, load_only=True)
    email = fields.Email(load_only=True)
    publish_date = fields.Date()
    reviews = Relationship(
        self_view='book_reviews',
        self_view_kwargs={'id': '<id>'},
        related_view='review_list',
        related_view_kwargs={'id': '<id>'},
        many=True,
        schema='ReviewSchema',
        type_='review'
    )


class ReviewSchema(Schema):
    class Meta:
        type_ = 'review'
        self_view = 'review_detail'
        self_view_kwargs = {'id': '<id>'}

    id = fields.Integer(as_string=True, dump_only=True)
    text = fields.Str(required=True)
    book = Relationship(
        attribute='book',
        self_view='review_book',
        self_view_kwargs={'id': '<id>'},
        related_view='book_detail',
        related_view_kwargs={'review_id': '<id>'},
        schema='BookSchema',
        type_='book'
    )


# Create resource managers
class BookList(ResourceList):
    schema = BookSchema
    data_layer = {'session': db.session,
                  'model': Book}


class BookDetail(ResourceDetail):
    def before_get_object(self, view_kwargs):
        if view_kwargs.get('review_id') is not None:
            try:
                review = self.session.query(Review).filter_by(id=view_kwargs['review_id']).one()
            except NoResultFound:
                raise ObjectNotFound({'parameter': 'review_id'},
                                     "Review: {} not found".format(view_kwargs['review_id']))
            else:
                if review.book is not None:
                    view_kwargs['id'] = review.book.id
                else:
                    view_kwargs['id'] = None

    schema = BookSchema
    data_layer = {'session': db.session,
                  'model': Book,
                  'methods': {'before_get_object': before_get_object}}


class BookRelationship(ResourceRelationship):
    schema = BookSchema
    data_layer = {'session': db.session,
                  'model': Book}


class ReviewList(ResourceList):
    def query(self, view_kwargs):
        query_ = self.session.query(Review)
        if view_kwargs.get('id') is not None:
            try:
                self.session.query(Book).filter_by(id=view_kwargs['id']).one()
            except NoResultFound:
                raise ObjectNotFound({'parameter': 'id'}, "Book: {} not found".format(view_kwargs['id']))
            else:
                query_ = query_.join(Book).filter(Book.id == view_kwargs['id'])
        return query_

    def before_create_object(self, data, view_kwargs):
        if view_kwargs.get('id') is not None:
            book = self.session.query(Book).filter_by(id=view_kwargs['id']).one()
            data['book_id'] = book.id

    schema = ReviewSchema
    data_layer = {'session': db.session,
                  'model': Review,
                  'methods': {'query': query,
                              'before_create_object': before_create_object}}


class ReviewDetail(ResourceDetail):
    schema = ReviewSchema
    data_layer = {'session': db.session,
                  'model': Review}


class ReviewRelationship(ResourceRelationship):
    schema = ReviewSchema
    data_layer = {'session': db.session,
                  'model': Review}


# Create endpoints
api = Api(app)
api.route(BookList, 'book_list', '/books')
api.route(BookDetail, 'book_detail', '/books/<int:id>', '/reviews/<int:review_id>/book')
api.route(BookRelationship, 'book_reviews', '/books/<int:id>/relationships/reviews')
api.route(ReviewList, 'review_list', '/reviews', '/books/<int:id>/reviews')
api.route(ReviewDetail, 'review_detail', '/reviews/<int:id>')
api.route(ReviewRelationship, 'review_book', '/reviews/<int:id>/relationships/book')

if __name__ == '__main__':
    # Start application
    app.run(debug=True)
