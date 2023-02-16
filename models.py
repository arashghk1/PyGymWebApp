import datetime as datetime
from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.Text(), primary_key=True)
    password = db.Column(db.Text(), nullable=False)
    email = db.Column(db.Text())
    phone = db.Column(db.Text())
    role = db.Column(db.Text())
    cart_id = db.Column(db.Integer(), db.ForeignKey('cart.cart_id'))

    def __ref__(self):
        return f"<Users {self.username}:{self.email}>"


# class Memberships(db.Model):
#     __tablename__ = 'memberships'
#     memberships = db.Column(db.Text(), primary_key=True)
#     price = db.Column(db.Numeric(precision=10, scale=2))
#     url = db.Column(db.Text())
#
#     def __ref__(self):
#         return f"<Memberships {self.memberships}: {self.price}>"
#

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.Text(), nullable=False)
    category = db.Column(db.Text())
    url = db.Column(db.Text())
    size = db.Column(db.Text())
    price = db.Column(db.Numeric(precision=10, scale=2))
    carts = db.relationship('Cart', secondary='product_cart', backref=db.backref('carts', lazy=True), lazy=True,
                            viewonly=True)

    def __ref__(self):
        return f"<Products {self.name}: {self.category} {self.url} {self.size} {self.price} >"


class Cart(db.Model):
    __tablename__ = 'cart'
    cart_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    datetime = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now)
    products = db.relationship('Product', secondary='product_cart', backref=db.backref('products', lazy=True),
                               lazy=True)

    def __repr__(self):
        return f"<Cart {self.cart_id}: {self.datetime}>"


class ProductCart(db.Model):
    __tablename__ = 'product_cart'
    product_id = db.Column(db.Integer(), db.ForeignKey('product.product_id'), primary_key=True)
    cart_id = db.Column(db.Integer(), db.ForeignKey('cart.cart_id'), primary_key=True)
    quantity = db.Column(db.Integer(), default=1)

    def __repr__(self):
        return f"<ProductCart {self.product_id} {self.cart_id}: {self.quantity}>"
