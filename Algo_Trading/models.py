from flask_login import UserMixin
# from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, flash
from dotenv import load_dotenv
load_dotenv()
import os



db = SQLAlchemy()
DB_NAME = "database.db"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password=db.Column(db.String(150))
    stocks = db.relationship('Stocks')

class Stocks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(100))
    stock_ticker = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


def connect_to_db(app):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    app.config['SECRET_KEY'] = SECRET_KEY 
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


def create_database(app):
    if not os.path.exists('website/' + DB_NAME):
        db.create_all()
        print('Created Database!')
