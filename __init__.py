from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
# from flask_wtf.csrf import CSRFProtect
from html import unescape
import importlib


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://honomara:honomara@localhost/honomara'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.jinja_env.globals.update(len=len, int=int, unescape=unescape)

# csrf = CSRFProtect(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)

routes = importlib.import_module('honomara_members_site.routes')
