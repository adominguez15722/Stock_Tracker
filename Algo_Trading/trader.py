import requests
from flask import Flask, render_template
import json
from pprint import pprint 
from dotenv import load_dotenv
load_dotenv()
import os

API_KEY = os.environ.get('API_KEY')


def stocks_info():
    url = "https://yfapi.net/v6/finance/quote"

    querystring = {"symbols":"AAPL"}

    headers = {
        'x-api-key': f"{API_KEY}"
        }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response_info = json.loads(response.text)
    comp_name = response_info['quoteResponse']['result'][0]['longName']
    comp_sym = response_info['quoteResponse']['result'][0]['symbol']
    comp_fifty = response_info['quoteResponse']['result'][0]['fiftyDayAverage']
    comp_two_hundred = response_info['quoteResponse']['result'][0]['twoHundredDayAverage']

    stock_info = (comp_fifty - comp_two_hundred, comp_two_hundred, comp_fifty)
    return stock_info

stocks_info()