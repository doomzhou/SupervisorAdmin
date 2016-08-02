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
    if request.method == "POST":
        user = request.form['email']
        result = Login(request.form)
        print(result)
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
    result = {}
    field = ["statename", "description", "name"]
    programslist, result = Index()
    pdict = {}
    pkeys = []
    for i in programslist:
        node = i['nodes']
        if node in pdict:
            pdict[node].append(i)
        else:
            pdict[node] = [i]
        pass
    pkeys = pdict.keys()
    return render_template('index.html', field = field, result = result,
        pdict = pdict, pkeys = pkeys)


@app.route('/nodeslist/<inact>')
@require_api_token
def nodeslist(inact):
    result = NodesList(inact)
    field = ["hostport", "status", "createtime"]
    panelheading = "节点列表"
    return render_template('tables.html', result = result, field = field,
            panelheading = panelheading, title = 'NodesList')


@app.route('/programslist/<inact>')
@require_api_token
def programslist(inact):
    panelheading = "进程列表"
    result = ProgramsList(inact)
    field = ["name", "nodes", "description", "statename"]
    return render_template('tables.html', result = result, field = field,
            panelheading = panelheading, title = 'ProgramsList')


@app.route('/addnode', methods=["POST"])
@require_api_token
def addnode():
    result = {"code": 1, "msgs": "None"}
    if request.method == "POST":
        result = AddNode(request.form)
        return render_template('addnode.html', result = result)
    return render_template('addnode.html', result = result)


@app.route('/rpcconnecttest', methods=["POST"])
@require_api_token
def rpcconnecttest():
    return RpcConnectTest(request.json['connectstr'])


@app.route('/userinvite', methods=["GET", "POST"])
@require_api_token
def userinvite():
    result = {}
    if request.method == "POST":
        result = UserInvite(request.json['email'])
        return str(result)
    return render_template('userinvite.html', result = result)


@app.route('/<pagename>')
@require_api_token
def admin(pagename):
    return render_template(pagename+'.html')


@app.route('/chpass')
@require_api_token
def chpass():
    if "user" in session:
        verifycode = Generate_auth_token(session["user"], 'verifykey').decode()
        result = {"code": 2, "msgs": "请重新设置密码", "email": session["user"], "verifycode": verifycode}
    return render_template('setpass.html', result = result)


@app.route('/action')
@require_api_token
def action():
    result = {}
    result = Action(request.args)
    return result['msgs'].replace('\n', '<br>')


#############################above 需要验证 below 不需要验证#####################


@app.route('/userverify')
def userverify():
    result = {}
    if request.args.get('verifycode') and request.args.get('email'):
        result = UserInvite(request.args.get('email'), request.args.get('verifycode'))
    if result['code'] == 2:
        return render_template('setpass.html', result = result)
    else:
        return render_template('login.html', result = result)


@app.route('/<path:resource>')
def serveStaticResource(resource):
        return send_from_directory('static/', resource)

if __name__ == '__main__':
    app.debug = CONFIGS['AppDebugOption']
    app.run(host=CONFIGS['Host'], port=CONFIGS['Port'])
