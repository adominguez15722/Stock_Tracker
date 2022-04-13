from pprint import pprint
from flask import Flask, jsonify, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, connect_to_db, Stocks, create_database, db
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
from yahoofinancials import YahooFinancials
import matplotlib.pyplot as plt
from datetime import date, timedelta, datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
load_dotenv()
import os

API_KEY = os.environ.get('API_KEY')


app=Flask(__name__)
def create_app():
    connect_to_db(app)

    create_database(app)

    login_manager = LoginManager()
    # login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Email already exists', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif password1 != password2:
            flash("Passwords don't match.", category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            # db.session['logged_in'] = True
            flash('Account created!', category='success')
            return render_template('user_homepage.html', user=current_user)

    return render_template('register.html', user=current_user)

@app.route('/homepage', methods=['POST', 'GET'])
def homepage():
    if request.method == 'GET':
            return render_template('user_homepage.html', user=current_user)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                
                # if not 'logged_in' in db.session or not db.session['logged_in']:
                flash('Logged in successfully', category='success')
                login_user(user, remember=True)
                # db.session['logged_in'] = True
                return render_template('user_homepage.html', user=current_user)
            else:
                flash('Incorrect password, try again', category='error')
                return render_template('base.html')
        else:
            flash('Email does not exist', category='error')
            return render_template('base.html')
    return render_template('user_page.html', user=current_user)

@app.route('/stock_info', methods=['POST'])
@login_required
def stock_information():
    stock_name = request.form.get('stock_name').upper()
    url = "https://yfapi.net/v6/finance/quote"

    querystring = {"symbols":f"{stock_name}"}
    headers = {
            'x-api-key': f"{API_KEY}"
            }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response_info = json.loads(response.text)
    
    # if KeyError:
    #     flash('Not a valid stock ticker', category='error')
    #     return render_template('user_homepage.html', user=current_user)
    # else:
    comp_name = response_info['quoteResponse']['result'][0]['longName']
    comp_sym = response_info['quoteResponse']['result'][0]['symbol']
    comp_fifty = response_info['quoteResponse']['result'][0]['fiftyDayAverage']
    comp_two_hundred = response_info['quoteResponse']['result'][0]['twoHundredDayAverage']

    stock_info = (comp_fifty - comp_two_hundred, comp_two_hundred, comp_fifty)
    new_stock = Stocks(stock_name=comp_name, user_id=current_user.id, stock_ticker=stock_name)

    stock = Stocks.query.filter_by(stock_name=comp_name).first()
    user = Stocks.query.filter_by(user_id=current_user.id).first()

    if stock and user:
        flash('Stock already on watchlist', category='error')
    else:
        db.session.add(new_stock)
        db.session.commit()
        flash(f'{stock_name} added!', category='success')
        return render_template('user_homepage.html', user=current_user)
    return render_template('user_homepage.html', user=current_user)

@app.route('/delete_stock', methods=['POST', 'GET'])
@login_required
def delete_stock():
    stock = request.get_json(force=True)
    stockId = stock['stockId']
    stock = Stocks.query.get(stockId)
    if stock:
        if stock.user_id == current_user.id:
            db.session.delete(stock)
            db.session.commit()
            # flash('Deleted stock', category='success')
    # return render_template('user_homepage.html', user=current_user)
    return jsonify({})


@app.route('/stock_page/<name>', methods=['GET'])
@login_required
def stock_details(name):
    stock = Stocks.query.filter_by(stock_name=name).first()
    tick = stock.stock_ticker
    
    ticker = yf.Ticker(f'{tick}')
    fifty_high = yf.Ticker(f'{tick}').info['fiftyTwoWeekHigh']
    fifty_low = yf.Ticker(f'{tick}').info['fiftyTwoWeekLow']
    cur_price = yf.Ticker(f'{tick}').info['regularMarketPrice']
    eps = yf.Ticker(f'{tick}').info['forwardPE']
    tick_df = ticker.institutional_holders
    comp_info = ticker.info['longBusinessSummary']
    investors = tick_df.head()

    today = date.today()
    d1 = today.strftime("%Y-%m-%d")
    N_DAYS_AGO = 5
    exact_date = datetime.now()    
    n_days_ago = exact_date - timedelta(days=N_DAYS_AGO)
    five_days = n_days_ago.date()


    yahoo_financials = YahooFinancials(f'{tick}')
    data = yahoo_financials.get_historical_price_data(start_date=f'{five_days}', 
                                                  end_date=f'{d1}', 
                                                  time_interval='daily')
    comp_df = pd.DataFrame(data[f'{tick}']['prices'])
    rounded = comp_df.round(2)
    # comp_df = comp_df.drop('date', axis=1).set_index('formatted_date')
    prices = rounded.head()
   
    hist = ticker.history(period='1y')
    # fig = go.Figure(data=go.Scatter(x=hist.index,y=hist['Close'], mode='lines'))
    # fig.show()

    hist['diff'] = hist['Close'] - hist['Open']
    hist.loc[hist['diff']>=0, 'color'] = 'green'
    hist.loc[hist['diff']<0, 'color'] = 'red'

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Candlestick(x=hist.index,
                                open=hist['Open'],
                                high=hist['High'],
                                low=hist['Low'],
                                close=hist['Close'],
                                name='Price'))
    fig3.add_trace(go.Scatter(x=hist.index,y=hist['Close'].rolling(window=20).mean(),marker_color='blue',name='20 Day MA'))
    fig3.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume', marker={'color':hist['color']}),secondary_y=True)
    fig3.update_yaxes(range=[0,700000000],secondary_y=True)
    fig3.update_yaxes(visible=False, secondary_y=True)
    fig3.update_layout(xaxis_rangeslider_visible=False)  #hide range slider
    fig3.update_layout(title={'text':f'{tick}', 'x':0.5})
    # fig3.show()

    
    fig3.write_html('./temp/temp.html')

    with open('./temp/temp.html', 'r') as f:
        return render_template('stock_page.html', user=current_user, prices=prices, investors=investors, stock=stock, comp_info=comp_info, fifty_high=fifty_high, fifty_low=fifty_low, cur_price=cur_price, eps=eps, plot=f.read())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('base.html')


