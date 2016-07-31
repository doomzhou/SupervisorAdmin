#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File Name : app.py
''''''
# Creation Date : 1469836662
# Last Modified :
# Release By : Doom.zhou
###############################################################################


from flask import Flask, url_for, render_template, send_from_directory\
        ,request, redirect
from handler import *


app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/api/auth', methods=["POST"])
def apiauth():
    if ApiAuth(request.json):
        return "0"
    else:
        return "1"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['email']
        result = Login(request.form)
        return render_template('login.html', result = result, user = user)
    return render_template('login.html', result = {})


@app.route('/')
def indext():
    return render_template('index.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/<pagename>')
def admin(pagename):
    return render_template(pagename+'.html')


@app.route('/<path:resource>')
def serveStaticResource(resource):
        return send_from_directory('static/', resource)

if __name__ == '__main__':
    app.debug = CONFIGS['AppDebugOption']
    app.run(host=CONFIGS['Host'], port=CONFIGS['Port'])
