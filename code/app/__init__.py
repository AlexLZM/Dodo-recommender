from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import numpy as np
import os

# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
application = Flask(__name__)
application.config.from_object(Config)
SECRET_KEY = os.urandom(24)
application.secret_key = SECRET_KEY
db = SQLAlchemy(application)
db.create_all()
db.session.commit()

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(application)

UPLOAD_FOLDER = os.path.abspath(os.path.dirname(__file__))+'/static/uploads'


application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from app import classes



from app import model
features = model.features
transforms_valid = model.transforms_valid
feature_model = model.model
root = (os.path.abspath(os.path.dirname(__file__)))
arr = np.load(root+'/arr.npy', allow_pickle=True)
id_list = None

from app import routes # routes.py needs to import "application" variable in __init__.py (Altough it violates PEP8 standards)

