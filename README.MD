Intro
===
把supervisord 统一管理 保留原管理平台的功能

## requirement ##

* Python3+
* Flask
* redis
* pyyaml

## 部署代码,安装依赖 ##


`git clone https://github.com/doomzhou/SupervisorAdmin.git`

`cd SupervisorAdmin`

`pip install -r requirements.t`


## 关于配置文件 ##

`cp config.yaml.example config.yaml`


    AppDebugOption : False              # Debug开关
    Host           : 0.0.0.0
    Port           : 5001
    Redis:                              # Redis 配置项
        Host: 127.0.0.1
        Port: 6379
        Auth: redisauthkey              # 需要配置Redis密码验证
    DBPrefix: prefix
    SecretKey: wtfsecret                # key is wtf
    Token_expire: 3600                  # 登录session超时时间 

    ## mail server for userinvite       需要邮件邀请功请配置
    Email:
        From: noreply@g.cn
        Pass: noreply'spassword
        Smtpser: smtp.exmail.qq.com
        Smtpport: 465

## 运行 ##

`python app.py`

## 初始化登录 ##

user: admin@g.cn

password: admin

#####另:请及时修改密码


## Screenshots ##

![cap1](https://66.media.tumblr.com/5c77272c6669a59d0406f6b87bbcc420/tumblr_ob9wmw1yLU1r68ev5o1_1280.png)

![cap2](https://67.media.tumblr.com/552b8b7a65c7eb7fcdd7f97d045be1aa/tumblr_ob9wmw1yLU1r68ev5o2_1280.png)

![cap3](https://67.media.tumblr.com/c57a66dc3cc3959ca4c07b38df599f45/tumblr_ob9wmw1yLU1r68ev5o3_1280.png)
