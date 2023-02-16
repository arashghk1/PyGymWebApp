from app import app
from models import db, Users, Cart, Product, ProductCart


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, Users=Users, Cart=Cart, Product=Product, ProductCart=ProductCart)
