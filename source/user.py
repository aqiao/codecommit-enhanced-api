import datetime

import jwt

from source.api_response import *
from source.db import get_db
from flask import (
    Blueprint, request
)
import boto3
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('user', __name__, url_prefix='/user')
iam_client = boto3.client('iam')


@bp.route('/index', methods=('GET',))
def index():
    """
    展示所有用户
    ---
    tags:
      - user
    responses:
        '200':
          description: Successful operation
        '400':
          description: Invalid ID supplied
    """
    try:
        # json_data = create_readonly_policy()
        # print(json_data)
        db = get_db()
        rows = db.execute(
            "select * from user"
        ).fetchall()
        users = []
        for row in rows:
            users.append(row_to_dict(row))
    except db.InternalError as e:
        return failed_with_data(e, e.strerror)
    else:
        return succeeded_with_data(users)


@bp.route('/create', methods=('PUT',))
def create():
    """
    创建用户
    ---
    tags:
      - user
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              user_name:
                type: string
                example: '张三'
              email:
                type: string
                example: 'zhangsan@sample.com'
              password:
                type: string
                example: 'Asia_Info_888'
              status:
                type: string
                default: '正常'
                enum:
                  - 正常
                  - 停用
          required:
            - user_name
            - email
            - password
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        user_name = request.form['user_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        status = request.form['status']
        user = get_iam_user(email)
        if user is None:
            # create account
            user = iam_client.create_user(UserName=email)
            # create password
            iam_client.create_login_profile(UserName=email, Password=request.form['password'])
            # create AKSK
            access_key = iam_client.create_access_key(
                UserName=email
            )
            ak = access_key['AccessKey']['AccessKeyId']
            sk = access_key['AccessKey']['SecretAccessKey']
            operator = 1
            db.execute(
                """
                insert into user (user_name, email, password, status, operator, aws_arn, ak, sk) 
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_name, email, password, status, operator, user['User']['Arn'],ak, sk)
            )
            db.commit()
            return succeeded_without_data(f"User {email} added successfully")

    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"User {user_name} existed already, please use another one")


@bp.route('/delete/<string:email>', methods=('DELETE',))
def delete(email):
    """
    根据邮箱删除用户
    ---
    tags:
      - user
    parameters:
        - name: email
          in: path
          description: 邮箱
          required: true
          schema:
            type: string
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    db = get_db()
    try:

        iam_user = get_iam_user(email)
        if iam_user is None:
            return succeeded_without_data(f"User {email} not found in iam")
        db_user = get_db_user(email)
        if db_user is None:
            return succeeded_without_data(f"User {email} not found in database")
        try:
            iam_client.delete_access_key(UserName=email, AccessKeyId=db_user['ak'])
        except Exception as e:
            print(f'warning: when removing delete_access_key for {email} occurred error')

        try:
            iam_client.delete_login_profile(UserName=email)
        except Exception as e:
            print(f'warning: when removing delete_access_key for {email} occurred error')

        try:
            iam_client.delete_user(UserName=email)
        except Exception as e:
            print(f'warning: when removing delete_access_key for {email} occurred error')

        db.execute("delete from user where email = ?", (email,))
        db.commit()
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"User {email} removed successfully")


@bp.route('/get/<string:email>',methods=('GET',))
def get_user(email):
    """
    根据邮箱获取用户信息
    ---
    tags:
      - user
    parameters:
        - name: email
          in: path
          description: 用户邮箱
          required: true
          schema:
            type: string
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    user = get_iam_user(email)
    if user is None:
        return succeeded_without_data(f"User {email} not existed")
    db_user = get_db_user(email)
    return succeeded_with_data(db_user)


def get_iam_user(email):
    try:
        user = iam_client.get_user(UserName=email)
    except iam_client.exceptions.NoSuchEntityException:
        return None
    except Exception as e:
        raise e
    else:
        if user is None or 'User' not in user:
            return None
        return user


def get_db_user(email):
    db = get_db()
    row = db.execute("select * from user where email = ?",(email,)).fetchone()
    if row is None:
        return None
    return row_to_dict(row)


@bp.route('/get_token',methods=("GET",))
def get_token():
    """
    根据邮箱和密码获取用户token
    ---
    tags:
      - user
    parameters:
        - name: X-USER-NAME
          in: header
          description: 用户邮箱
          required: true
          schema:
            type: string
        - name: X-USER-PASSWORD
          in: header
          description: 密码
          required: true
          schema:
            type: string
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    email = request.headers.get("X-USER-NAME",None)
    password = request.headers.get("X-USER-PASSWORD", None)
    if email is None or password is None:
        return succeeded_without_data("Please specify user name and password")
    db_user = get_db_user(email)
    if db_user is None:
        return failed_without_data(f"User {email} not found")
    if check_password_hash(db_user['password'], password) is False:
        return failed_without_data(f"Invalid user or password, please try again")
    identify = email + db_user['ak']
    identify_hash = generate_password_hash(identify)
    secret = "Asia_Info_88*"
    payload = {
        "iss": db_user['ak'],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1),
        "iat": datetime.datetime.utcnow(),
        "data": {
            "hash": identify_hash
        }
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return succeeded_without_data(token)


def row_to_dict(row):
    """
    :param row:
    :return:
    """
    return {
        "id": row[0],
        "user_name": row[1],
        "email": row[2],
        "password": row[3],
        "status": row[4],
        "created": str(row[5]),
        "updated": str(row[6]),
        "operator": row[7],
        "iam_arn": row[8],
        "ak": row[9],
        "sk": row[10]
    }