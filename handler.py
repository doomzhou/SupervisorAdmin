#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File Name : handler.py
'''handler for app'''
# Creation Date : 1469850170
# Last Modified :
# Release By : Doom.zhou
###############################################################################


from functools import wraps
from flask import Flask, url_for, render_template, send_from_directory\
        ,request, redirect, session
from itsdangerous import (TimedJSONWebSignatureSerializer
    as Serializer, BadSignature, SignatureExpired)
from datetime import datetime
import os, re, sys, time
import redis, yaml
import xmlrpc.client
import ast
#custom module
from myemail import mailsender


with open('config.yaml') as f:
    CONFIGS = yaml.load(f)


def RedisConn():
    DBPrefix = CONFIGS['DBPrefix']
    conn = redis.StrictRedis(host=CONFIGS['Redis']['Host'],
            port=CONFIGS['Redis']['Port'],
            password=CONFIGS['Redis']['Auth'])
    return conn, DBPrefix


def Generate_auth_token(email, secondkey=''):
    s = Serializer("%s%s" % (CONFIGS['SecretKey'], secondkey), expires_in = CONFIGS['Token_expire'])
    return s.dumps(email)


def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        # Check to see if it's in their session
        if 'token' not in session:
            return render_template('login.html', result = {"code": 1, "msgs": "Access denied"})
        s = Serializer(CONFIGS['SecretKey'])
        try:
            data = s.loads(session['token'])
        except SignatureExpired:
            data = "expired" # valid token, but expired
            return render_template('login.html', result = {"code": 1, "msgs": "SignatureExpired"})
        except BadSignature:
            data = "BadSignature" # invalid token
            return render_template('login.html', result = {"code": 1, "msgs": "BadSignature"})
        except:
            data = None
            return render_template('login.html', result = {"code": 1, "msgs": "token invalid"})
        # if data == user:
            # If it isn't return our access denied message (you can also return a redirect or render_template)
            # return render_template('login.html', result = {"code": 1, "msgs": "token invalid"})
        # Otherwise just send them where they wanted to go
        return func(*args, **kwargs)
    return check_token


def Login(req):
    result = {"code": 0, "msgs": "None"}
    conn, dbprefix = RedisConn()
    keyname = "%suser" % dbprefix
    if 'password1' in req and 'verify' in req:
        result = UserInvite(req['email'], req['verify'])
        if result['code'] == 2 and req['password1'] == req['password2']:
            if req['email'] in [x.decode() for x in conn.hkeys(keyname)]:
                conn.hset(keyname, req['email'], req['password1'])
                result = {"code": 2, "msgs": "密码已经更新"}
            else:
                conn.hset(keyname, req['email'], req['password1'])
                result = {"code": 2, "msgs": "密码已经设置"}
        else:
            result = {"code": 1, "msgs": "verifycode 不正确或者前后密码不一致"}
    elif 'password' in req and 'email' in req:
        if conn.hget(keyname, req['email']):
            if req['password'] == conn.hget(keyname, req['email']).decode():
                token = Generate_auth_token(req['email']).decode()
                session['token'] = token
                session['user'] = req['email']
                result = {"code": 0, "msgs": "Success", "user": token}
            else:
                result = {"code": 1, "msgs": "U&P incorrect"}
        else:
            result = {"code": 1, "msgs": "U not exists"}
    else:
        result = {"code": 1, "msgs": "U&P nil"}
    return result


def RpcConnectTest(connectstr):
    with xmlrpc.client.ServerProxy(connectstr) as proxy:
        try:
            proxy.system.listMethods()
            return "0"
        except Exception as e:
            print(e)
            return str(e)


def AddNode(req, inact="active"):
    conn, dbprefix = RedisConn()
    keyname = "%snodelist" % dbprefix
    result = {"code": 1, "msgs": "None"}
    value = []
    if conn.exists(keyname):
        # origin value
        value = ast.literal_eval(conn.get(keyname).decode())
        # remove duplicate hostport
        value = [x for x in value if x['hostport'] != req['hostport']]
        # update newest to value
        value.append({"userpass": req['userpass'], "hostport": req["hostport"],
            "status": inact, "createtime": datetime.strftime(datetime.now(), '%D %T')})
        result = {"code": 0, "msgs": "%s exists updated it" % req['hostport']}
    else:
        value.append({"userpass": req['userpass'], "hostport": req["hostport"],
            "status": inact, "createtime": datetime.strftime(datetime.now(), '%D %T')})
        result = {"code": 0, "msgs": "%s Added" % req['hostport']}
    try:
        conn.set(keyname, value)
    except:
        result = {"code": 1, "msgs": "Unknown error"}
    return result


def NodesList(inact):
    conn, dbprefix = RedisConn()
    keyname = "%snodelist" % dbprefix
    result = {"code": 1, "msgs": "None"}
    value = []
    if conn.exists(keyname):
        value = ast.literal_eval(conn.get(keyname).decode())
    return value


def ProgramsList(inact):
    conn, dbprefix = RedisConn()
    keyname = "%snodelist" % dbprefix
    result = {"code": 1, "msgs": "None"}
    value = []
    if conn.exists(keyname):
        nodeslist = ast.literal_eval(conn.get(keyname).decode())
        for i in nodeslist:
            connectstr = "http://%s@%s/RPC2" % (i['userpass'], i['hostport'])
            # 如果连接成功的话,进行Programslist解析
            if RpcConnectTest(connectstr) == "0":
                # real values with Programslist
                result = AddNode(i, "active")
                with xmlrpc.client.ServerProxy(connectstr) as proxy:
                    try:
                        allprocesslist = proxy.supervisor.getAllProcessInfo()
                        # add node info
                        [x.update({"nodes": i["hostport"]}) for x in allprocesslist]
                        value += allprocesslist
                    except Exception as e:
                        pass
            else:
                result = AddNode(i, "inactive")
    return value


def Index():
    nodeslist = NodesList("e")
    FailedNodes = [x for x in nodeslist if x['status'] == "inactive"]
    programslist = ProgramsList("e")
    FailedProgrames = [x for x in programslist if x['statename'] != "RUNNING"]
    result = {"code": 1, "msgs": "None"}
    value = {"Programes": len(programslist), "FailedProgrames": len(FailedProgrames),
            "Nodes": len(nodeslist), "FailedNodes": len(FailedNodes)}
    return programslist, value


def UserInvite(email, verify=""):
    result = {"code": 1, "msgs": "None"}
    if verify != "":
        s = Serializer("%s%s" % (CONFIGS['SecretKey'], "verifykey"))
        data = None
        try:
            data = s.loads(verify)
        except SignatureExpired:
            result = {"code": 1, "msgs": "SignatureExpired"}
        except BadSignature:
            result = {"code": 1, "msgs": "BadSignature"}
        except Exception as e:
            print(e)
            result = {"code": 1, "msgs": "验证不通过"}
        if data == email:
            result = {"code": 2, "msgs": "验证通过, 请设置密码", "email": email, "verifycode": verify}
        else:
            result = {"code": 1, "msgs": "签名失效或未知错误"}
    else:
        mailfrom = CONFIGS['Email']['From']
        mailfrompass = CONFIGS['Email']['Pass']
        smtpser = CONFIGS['Email']['Smtpser']
        smtpport = CONFIGS['Email']['Smtpport']
        if not re.match('[^@]+@[^@]+\.[^@]+', email):
            result = {"code": 1, "msgs": "Email address invalid"}
        else:
            try:
                verifycode = Generate_auth_token(email, 'verifykey').decode()
                mailcontent = "请点击激活帐号. %suserverify?verifycode=%s&email=%s" % (request.url_root, verifycode, email)
                mailsender(mailfrom, mailfrompass, smtpser, smtpport, email, mailcontent)
                result = {"code": 0, "msgs": "Mail sended"}
            except Exception as e:
                result = {"code": 1, "msgs": e}
    return result


def Action(req):
    conn, dbprefix = RedisConn()
    keyname = "%snodelist" % dbprefix
    result = {"code": 1, "msgs": "None"}
    value = []
    act = req.get('action')
    node = req.get('node')
    name = req.get('name')

    value = ast.literal_eval(conn.get(keyname).decode())
    value = [x for x in value if x['hostport'] == node][0]
    connectstr = "http://%s@%s/RPC2" % (value['userpass'], value['hostport'])

    with xmlrpc.client.ServerProxy(connectstr) as proxy:
        try:
            if act == "clear":
                if proxy.supervisor.clearProcessLogs(name):
                    result = {"code": 0, "msgs": "%s %s Success" % (name, act)}
                else:
                    result = {"code": 1, "msgs": "%s %s Failed" % (name, act)}
            elif act == "restart":
                if proxy.supervisor.stopProcess(name) and proxy.supervisor.startProcess(name):
                    result = {"code": 0, "msgs": "%s %s Success" % (name, act)}
                else:
                    result = {"code": 1, "msgs": "%s %s Failed" % (name, act)}
            elif act == "stop":
                if proxy.supervisor.stopProcess(name):
                    result = {"code": 0, "msgs": "%s %s Success" % (name, act)}
                else:
                    result = {"code": 1, "msgs": "%s %s Failed" % (name, act)}
            elif act == "start":
                if proxy.supervisor.startProcess(name):
                    result = {"code": 0, "msgs": "%s %s Success" % (name, act)}
                else:
                    result = {"code": 1, "msgs": "%s %s Failed" % (name, act)}
            elif act == "tail":
                offset = proxy.supervisor.tailProcessStdoutLog(name, 0, 1)[1]
                length = 1000
                res = proxy.supervisor.tailProcessStdoutLog(name, offset - length , length)[0]
                result = {"code": 0, "msgs": res}
        except Exception as e:
            print(e)

    return result


if __name__ == '__main__':
    pass
