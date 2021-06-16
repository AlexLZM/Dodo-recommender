import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345678@dodo-vintage-recommender.cf4jjo88kn76.us-west-1.rds.amazonaws.com/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = True # flask-login uses sessions which require a secret Key


