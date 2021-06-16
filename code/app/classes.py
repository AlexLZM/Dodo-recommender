from flask_login import UserMixin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

from app import db, login_manager




# ----------------------------Users--------------------------
# class name changed to Users to avoid conflict with default user table in postgres
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80), nullable=False)
    lname = db.Column(db.String(80), nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __init__(self, fname, lname, mobile,  email, password):
        self.fname = fname
        self.lname = lname
        self.mobile = mobile
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# user_loader :
# This callback is used to reload the user object
# from the user ID stored in the session.
@login_manager.user_loader
def load_user(id):
   return Users.query.get(int(id))


# class RegistrationForm(FlaskForm):
#     username = StringField('Username:', validators=[DataRequired()])
#     email = StringField('Email:', validators=[DataRequired()])
#     password = PasswordField('Password:', validators=[DataRequired()])
#     submit = SubmitField('Submit')

# class LogInForm(FlaskForm):
#     username = StringField('Username:', validators=[DataRequired()])
#     password = PasswordField('Password:', validators=[DataRequired()])
    # submit = SubmitField('Login')



# ----------------------------Uploads--------------------------
upload_img_bucket = "deep-fashion-uploaded-img"
class Uploads(db.Model):
    # __tablename__ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), unique=True, nullable=False)
    embedding = db.Column(db.ARRAY(db.Float, dimensions=1), nullable=False)
    
    def __init__(self, image_path, embedding):
        self.image_path = image_path
        self.embedding = embedding
        
# ----------------------------Candidates--------------------------
class Candidates(db.Model):
    # __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    designer = db.Column(db.String(100), nullable=True)
    image_path = db.Column(db.String(200), nullable=False)
    embedding = db.Column(db.ARRAY(db.Float, dimensions=1), nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(50), nullable=True)
    price_usd = db.Column(db.Float, nullable=True)
    url = db.Column(db.String(300), nullable=False)
    stock = db.Column(db.Integer, nullable=True)
    condition = db.Column(db.String(100), nullable=True)
    authentication = db.Column(db.String(100), nullable=True)
    
    def __init__(self, name, source, designer, image_path, embedding,
                 original_price, currency, price_usd, url, stock, 
                 condition, authentication):
        self.name = name
        self.source = source
        self.designer = designer
        self.image_path = image_path
        self.embedding = embedding
        self.original_price = original_price
        self.currency = currency
        self.price_usd = price_usd
        self.url = url
        self.stock = stock
        self.condition = condition
        self.authentication = authentication
        
# ----------------------------User Log--------------------------
class UserLog(db.Model):
    # __tablename__ = "user_log"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    event_type = db.Column(db.String, nullable=True)
    image_upload_id = db.Column(db.Integer, nullable=True)
    candidate_id = db.Column(db.Integer, nullable=True)
    
    def __init__(self, timestamp, event_type, image_upload_id, candidate_id):
        self.timestamp = timestamp
        self.event_type = event_type
        self.image_upload_id = image_upload_id
        self.candidate_id = candidate_id





db.create_all()
db.session.commit()


