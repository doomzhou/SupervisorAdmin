#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File Name : app.py
''''''
# Creation Date : 1469836662
# Last Modified :
# Release By : Doom.zhou
###############################################################################


from flask import Flask, url_for, render_template, send_from_directory\
        ,request, redirect, session
from handler import *


app = Flask(__name__)
app.config['SECRET_KEY'] = CONFIGS['SecretKey']


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['email']
        result = Login(request.form)
        return render_template('login.html', result = result, user = user)
    return render_template('login.html', result = {})


@app.route('/logout')
@require_api_token
def loginout():
    session.pop('token', None)
    return redirect(url_for("login"))


@app.route('/')
@app.route('/index')
@require_api_token
def index():
    return render_template('index.html')


@app.route('/<pagename>')
@require_api_token
def admin(pagename):
    return render_template(pagename+'.html')


@app.route('/<path:resource>')
def serveStaticResource(resource):
        return send_from_directory('static/', resource)

if __name__ == '__main__':
    app.debug = CONFIGS['AppDebugOption']
    app.run(host=CONFIGS['Host'], port=CONFIGS['Port'])
