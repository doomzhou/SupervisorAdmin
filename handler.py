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


with open('config.yaml') as f:
    CONFIGS = yaml.load(f)


def RedisConn():
    DBPrefix = CONFIGS['DBPrefix']
    conn = redis.StrictRedis(host=CONFIGS['Redis']['Host'],
            port=CONFIGS['Redis']['Port'],
            password=CONFIGS['Redis']['Auth'])
    return conn, DBPrefix


def Generate_auth_token(email):
    s = Serializer(CONFIGS['SecretKey'], expires_in = CONFIGS['Token_expire'])
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
    if req['email'] and req['password']:
        if conn.hget('%suser' % dbprefix, req['email']):
            if req['password'] == conn.hget('%suser' % dbprefix, req['email']).decode():
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
                with  xmlrpc.client.ServerProxy(connectstr) as proxy:
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

if __name__ == '__main__':
    pass
