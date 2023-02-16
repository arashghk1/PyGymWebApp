from flask import Flask, session, redirect, render_template, flash, jsonify, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate

from forms import LoginForm, RegisterForm
from models import db, Users, Product, Cart, ProductCart
import os
import bcrypt
import json
import stripe

stripe.api_key = 'sk_test_Hrs6SAopgFPF0bZXSN3f6ELN'

app = Flask(__name__)

app.secret_key = 'a long string value'
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///pyGym.sqlite'
app.config['USE_SESSION_FOR_NEXT'] = True

db.init_app(app)  # Add this line Before migrate line
migrate = Migrate(app, db)


class SessionUser(UserMixin):
    def __init__(self, username, email, phone, role, cart_id, password=None):
        self.id = username
        self.email = email
        self.phone = phone
        self.role = role
        self.password = password
        self.cart_id = cart_id


@login_manager.user_loader
def load_user(user_id):
    user = find_user(user_id)

    if user:
        user.password = None
    return user


def find_user(username):
    res = Users.query.get(username)
    if res:

        user = SessionUser(res.username, res.email, res.phone, res.role, res.cart_id, res.password)
    else:
        user = None
    return user


def calculate_order_total(cart_id):
    amount = 0
    productList = list(db.session.execute(
        db.select(Product.product_id, Product.name, Product.price, ProductCart.quantity)
        .where(ProductCart.cart_id == cart_id)
        .where(ProductCart.product_id == Product.product_id)
    ))
    for p in productList:
        amount += p[2] * p[3]

    return amount


def calculate_order_amount(cart_id):
    totalItems = 0
    totalPrice = 0
    productList = list(db.session.execute(
        db.select(Product.product_id, Product.name, Product.price, ProductCart.quantity)
        .where(ProductCart.cart_id == cart_id)
        .where(ProductCart.product_id == Product.product_id)
    ))
    for p in productList:
        totalPrice += p[2] * p[3]
        totalItems += 1

    return totalPrice, totalItems, productList


@app.route('/')
def index():  # put application's code here
    try:
        cart = Cart.query.get(current_user.cart_id)
        productList = db.session.execute(
            db.select(Product.product_id, Product.name, Product.price, ProductCart.quantity)
            .where(ProductCart.cart_id == cart.cart_id)
            .where(ProductCart.product_id == Product.product_id)
        )
    except:
        cart = None
        productList = None
    return render_template('index.html',
                           username=session.get('username'),
                           cart=cart,
                           products=productList)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user(form.username.data)
        # user could be None
        # passwords are kept in hashed form, using the bcrypt algorithm
        if user and bcrypt.checkpw(form.password.data.encode(), user.password.encode()):
            login_user(user)
            flash('Logged in successfully.')

            # check if the next page is set in the session by the @login_required decorator
            # if not set, it will default to '/'
            next_page = session.get('next', '/products')
            # reset the next page to default '/'
            session['next'] = '/'
            return redirect(next_page)
        else:
            flash('Incorrect username/password!')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()

    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():  # put application's code here
    form = RegisterForm()
    if form.validate_on_submit():
        # check first if user already exists
        user = find_user(form.username.data)
        if not user:
            cart = Cart()
            db.session.add(cart)
            db.session.commit()
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(form.password.data.encode(), salt)
            user = Users(username=form.username.data, email=form.email.data, phone=form.phone.data,
                         password=password.decode(), cart_id=cart.cart_id)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully.')
            return redirect('/login')
        else:
            flash('This username already exists, choose another one')
    return render_template('register.html', form=form)


@app.route('/about')
def about():  # put application's code here
    return render_template('about.html')


@app.route('/products')
def products():  # put application's code here
    DBproducts = Product.query.filter_by(category='Products').all()
    return render_template('newproducts.html', products=DBproducts)


@app.route('/memberships')
def memberships():  # put application's code here
    DBmemberships = Product.query.filter_by(category='Memberships').all()
    return render_template('purchasemembership.html', memberships=DBmemberships)


@app.route('/cart/addMembership/<int:product_id>')
@login_required
def add_to_membercart(product_id):
    c = Cart.query.get(current_user.cart_id)
    p = Product.query.get(product_id)
    try:
        pc = ProductCart.query.filter_by(cart_id=c.cart_id).filter_by(product_id=p.product_id).one()
        pc.quantity += 1
    except:
        pc = ProductCart(product_id=p.product_id, cart_id=c.cart_id)
    db.session.add(pc)
    db.session.commit()
    return redirect('/memberships')
@app.route('/cart/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    c = Cart.query.get(current_user.cart_id)
    p = Product.query.get(product_id)
    try:
        pc = ProductCart.query.filter_by(cart_id=c.cart_id).filter_by(product_id=p.product_id).one()
        pc.quantity += 1
    except:
        pc = ProductCart(product_id=p.product_id, cart_id=c.cart_id)
    db.session.add(pc)
    db.session.commit()
    return redirect('/products')

@app.route('/cart/complete-transaction')
@login_required
def completeTransaction():
    c = Cart.query.get(current_user.cart_id)
    ProductCart.query.filter_by(cart_id=c.cart_id).delete()
    db.session.commit()
    return redirect('/')


@app.route('/checkout')
@login_required
def checkout():
    amount, items, productsList = calculate_order_amount(current_user.cart_id)
    return render_template('checkout.html', amount=amount, items=items, productsList=productsList)


@app.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment():
    try:
        data = json.loads(request.data)
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=calculate_order_total(current_user.cart_id),
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403


if __name__ == '__main__':
    app.run()
