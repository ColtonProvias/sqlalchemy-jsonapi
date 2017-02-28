"""Must set up flask app for sqlalchmey_jsonapi unittesting."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.testing = True

db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_ECHO'] = False

if __name__ == '__main__':
    app.run()
