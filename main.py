from flask import Flask, jsonify, render_template, request, make_response, redirect, url_for, session, flash, blueprints
import requests, re, time
from blueprints.bus import bus_bp
from blueprints.login import login_bp
from blueprints.model import model_bp
from blueprints.skin import skin_bp

app = Flask(__name__)
app.secret_key = 'sitsitbus_key'

# 註冊 blueprint
app.register_blueprint(bus_bp, url_prefix='/bus')
app.register_blueprint(login_bp, url_prefix='/login')
app.register_blueprint(model_bp, url_prefix='/model')
app.register_blueprint(skin_bp, url_prefix='/skin')

# app.route
@app.route('/')
def home():
    if not request.cookies.get('visited'):
        resp = make_response(render_template('welcome.html'))
        resp.set_cookie('visited', 'yes', max_age=60*60*24*365)  # 有效期一年
        return resp
    return render_template('home.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/about')
def about():
    return render_template('about.html')
