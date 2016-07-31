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
        ,request, redirect
from itsdangerous import (TimedJSONWebSignatureSerializer
    as Serializer, BadSignature, SignatureExpired)
import os, re, sys, time
import redis, yaml


with open('config.yaml') as f:
    CONFIGS = yaml.load(f)


def RedisConn():
    DBPrefix = CONFIGS['DBPrefix']
    conn = redis.StrictRedis(host=CONFIGS['Redis']['Host'],
            port=CONFIGS['Redis']['Port'],
            password=CONFIGS['Redis']['Auth'])
    return conn, DBPrefix


def generate_auth_token(email):
    s = Serializer(CONFIGS['SecretKey'], expires_in = CONFIGS['Token_expire'])
    return s.dumps(email)


def ApiAuth(req):
    # Check to see if it's in their session
    token = req["user"]
    ID = req["ID"]
    s = Serializer(CONFIGS['SecretKey'])
    try:
        data = s.loads(token.encode())
    except:
        data = None
    if data == None or data != ID:
        return False
    return True


def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        # Check to see if it's in their session
        token = request.args.get('user')
        ID = request.args.get('ID')
        print(ID)
        print(token)
        s = Serializer(CONFIGS['SecretKey'])
        try:
            data = s.loads(token.encode())
        except SignatureExpired:
            data = "expired" # valid token, but expired
        except BadSignature:
            data = "BadSignature" # invalid token
        except:
            data = None
        if data == None or data != ID:
            # If it isn't return our access denied message (you can also return a redirect or render_template)
                    return render_template('login.html', result = {"code": 1, "msgs": "token invalid"})
        # Otherwise just send them where they wanted to go
        return func(*args, **kwargs)
    return check_token


def Login(req):
    result = {"code": 0, "msgs": "None"}
    conn, dbprefix = RedisConn()
    if req['email'] and req['password']:
        if conn.hget('%suser' % dbprefix, req['email']):
            if req['password'] == conn.hget('%suser' % dbprefix, req['email']).decode():
                token = generate_auth_token(req['email']).decode()
                result = {"code": 0, "msgs": "Success", "user": token}
            else:
                result = {"code": 1, "msgs": "U&P incorrect"}
        else:
            result = {"code": 1, "msgs": "U not exists"}
    else:
        result = {"code": 1, "msgs": "U&P nil"}
    return result


if __name__ == '__main__':
    pass
