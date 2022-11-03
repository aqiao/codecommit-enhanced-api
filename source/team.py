import boto3

from source.api_response import *
from source.db import get_db

from flask import (
    Blueprint, request,
)

bp = Blueprint('team', __name__, url_prefix='/team')
iam_client = boto3.client("iam")


@bp.route('/index', methods=('GET',))
def index():
    """
    展示所有项目组信息
    ---
    tags:
      - team
    responses:
        '200':
          description: Successful operation
        '400':
          description: Invalid ID supplied
    """
    try:
        db = get_db()
        rows = db.execute(
            "select * from team"
        ).fetchall()
        teams = []
        for row in rows:
            teams.append(row_to_dict(row))
    except db.InternalError as e:
        return failed_with_data(e, e.strerror)
    else:
        return succeeded_with_data(teams)


@bp.route('/get/<int:team_id>', methods=('GET',))
def get_team(team_id):
    """
    根据id获取项目组信息
    ---
    tags:
      - team
    parameters:
        - name: team_id
          in: path
          description: 项目组id
          required: true
          schema:
            type: integer
            format: int32
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    try:
        db_group = get_db_group(team_id)
        if db_group is None:
            return succeeded_without_data(f"team {team_id} not found")
        iam_group = get_iam_group(db_group['team_name'])
        if iam_group is None:
            return succeeded_without_data(f"Group {db_group['team_name']} not found")
        return succeeded_with_data(db_group)

    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_with_data(row_to_dict(row))


def get_iam_group(team_name):
    try:
        group = iam_client.get_group(GroupName=team_name)
    except iam_client.exceptions.NoSuchEntityException:
        return None
    except Exception as e:
        raise e
    else:
        if group is None or 'Group' not in group:
            return None
        return group


def get_db_group(team_id):
    db = get_db()
    if team_id is None:
        raise Exception("team_id is required")
    row = db.execute(
        'select * from team where id = ?',
        (team_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_dict(row)


@bp.route('/create', methods=('PUT',))
def create():
    """
    创建项目组
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              team_name:
                type: string
                example: 'team1'
              status:
                type: string
                default: '正常'
                enum:
                  - 正常
                  - 停用
              leader_id:
                type: integer
                example: 1
              leader_name:
                type: string
                example: '管理员'
            required:
              - team_name
              - status
              - leader_id
              - leader_name

    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        team_name = request.form['team_name']
        status = request.form['status']
        operator = 1
        iam_group = get_iam_group(team_name)
        if iam_group is None:
            response = iam_client.create_group(GroupName=team_name)
            aws_arn = response['Group']['Arn']
            db.execute(
                "insert into team (team_name, status, operator, aws_arn) values (?, ?, ?, ?)",
                (team_name, status, operator, aws_arn)
            )
            db.commit()
        else:
            return succeeded_without_data(f"team {team_name} is existed")
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"team {team_name} added successfully")


@bp.route('/update_name/<int:team_id>', methods=('POST',))
def update_name(team_id):
    """
    修改项目名称
    ---
    tags:
      - team
    parameters:
      - name: team_id
        in: path
        description: 项目组id
        required: true
        schema:
          type: integer
          format: int32
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              team_name:
                type: string
            required:
              - team_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        team_name = request.form['team_name']

        db.execute(
            'update team set team_name = ? where id = ?',
            (team_name, team_id)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"team {team_name} name changed successfully")


@bp.route('/update_status/<int:team_id>', methods=('POST',))
def update_status(team_id):
    """
    修改项目状态
    ---
    tags:
      - team
    parameters:
      - name: team_id
        in: path
        description: 项目组id
        required: true
        schema:
          type: integer
          format: int32
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              status:
                type: string
                default: '正常'
                enum:
                  - 正常
                  - 停用
            required:
              - status
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        status = request.form['status']

        db.execute(
            'update team set status = ? where id = ?',
            (status, team_id)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"team status is changed to {status} successfully")


@bp.route('/delete/<int:team_id>', methods=('DELETE',))
def delete(team_id):
    """
    根据id删除项目组
    ---
    tags:
      - team
    parameters:
        - name: team_id
          in: path
          description: 项目组id
          required: true
          schema:
            type: integer
            format: int32
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    try:
        db = get_db()
        db_group = get_db_group(team_id)
        if db_group is None:
            return succeeded_without_data("Team not found")
        iam_group = get_iam_group(db_group['team_name'])
        if iam_group:
            iam_client.delete_group(GroupName=db_group['team_name'])

        db.execute('delete from team where id = ?', (team_id,))
        db.commit()
    except Exception as e:
        print(e)
        return failed_without_data(str(e))
    else:
        return succeeded_without_data("team removed successfully")


@bp.route('/add_member', methods=("PUT",))
def add_member():
    """
    将用户添加到项目组
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              user_name:
                type: string
                example: 'tom@nwcdcloud.cn'
              team_name:
                type: string
                example: 'team1'
          required:
            - user_name
            - team_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    user_name = request.form['user_name']
    team_name = request.form['team_name']
    db = get_db()
    try:
        db.execute(
            "insert into team_member (user_name, team_name) values (?, ?)",
            (user_name, team_name)
        )
        iam_client.add_user_to_group(UserName=user_name, GroupName=team_name)
        db.commit()
    except Exception as e:

        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"Assigned user {user_name} to team {team_name}")


@bp.route('/delete_member', methods=("DELETE",))
def delete_member():
    """
    将用户从项目组中移除
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              user_name:
                type: string
                example: 'tom@nwcdcloud.cn'
              team_name:
                type: string
                example: 'team1'
          required:
            - user_name
            - team_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    user_name = request.form['user_name']
    team_name = request.form['team_name']
    db = get_db()
    try:
        db.execute(
            "delete from team_member where team_name = ? and user_name = ?",
            (team_name, user_name)
        )
        iam_client.remove_user_from_group(UserName=user_name, GroupName=team_name)
        db.commit()
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"Removed user {user_name} from team {team_name}")


@bp.route('/attach_policy',methods=('PUT',))
def attach_policy():
    """
    将策略添加到项目组
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              policy_arn:
                type: string
                example: 'arn:aws-cn:iam::aws:policy/AWSCodeCommitReadOnly'
              team_name:
                type: string
                example: 'team1'
          required:
            - user_name
            - team_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    policy_arn = request.form['policy_arn']
    team_name = request.form['team_name']
    db = get_db()
    try:
        iam_client.attach_group_policy(
            GroupName=team_name,
            PolicyArn=policy_arn
        )
        db.execute(
            "insert into team_policy (team_name, policy_arn) values (?,?)",
            (team_name, policy_arn)
        )
        db.commit()
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"Attached policy {policy_arn} to team {team_name}")


@bp.route('/detach_policy',methods=('DELETE',))
def detach_policy():
    """
    将策略从项目组中移除
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              policy_arn:
                type: string
                example: 'arn:aws-cn:iam::aws:policy/AWSCodeCommitReadOnly'
              team_name:
                type: string
                example: 'team1'
          required:
            - user_name
            - team_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    policy_arn = request.form['policy_arn']
    team_name = request.form['team_name']
    db = get_db()
    try:
        iam_client.detach_group_policy(
            GroupName=team_name,
            PolicyArn=policy_arn
        )
        db.execute(
            "delete from team_policy where team_name = ? and policy_arn = ?",
            (team_name, policy_arn)
        )
        db.commit()
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"Removed policy {policy_arn} to team {team_name}")


@bp.route('/get_policies/<string:team_name>', methods=('GET',))
def get_policies(team_name):
    """
    根据项目组名称获取对应策略
    ---
    tags:
      - team
    parameters:
        - name: team_name
          in: path
          description: 项目组名称
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
    rows = db.execute(
        'select team_name, policy_arn from team_policy where team_name = ?',
        (team_name,)
    ).fetchall()
    if rows is None:
        return succeeded_without_data(f"No policies found within team {team_name}")
    policies = []
    for row in rows:
        policies.append(policy_team_row_to_dict(row))
    return policies


@bp.route('/get_users/<string:team_name>', methods=('GET',))
def get_users(team_name):
    """
    根据项目组名称获取对应成员
    ---
    tags:
      - team
    parameters:
        - name: team_name
          in: path
          description: 项目组名称
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
    rows = db.execute(
        'select team_name, user_name from team_member where team_name = ?',
        (team_name,)
    ).fetchall()
    if rows is None:
        return succeeded_without_data(f"No users found within team {team_name}")
    users = []
    for row in rows:
        users.append(user_team_row_to_dict(row))
    return users


@bp.route('/batch_delete', methods=("DELETE",))
def batch_delete():
    """
    批量删除项目组
    ---
    tags:
      - team
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              team_ids:
                type: string
                example: '1,2,3'
            required:
              - team_ids

    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        team_ids = request.form['team_ids']
        if team_ids is None or len(team_ids) == '':
            return failed_without_data(f"Please specify team")
        db.execute(
            'delete from team where id in (' + team_ids + ')'
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"team delete in batch successfully")


def row_to_dict(row):
    """
    convert sqlite row object to dict
    :param row: sqlite row
    :return: dict
    """
    return {
        "id": row[0],
        "team_name": row[1],
        "status": row[2],
        "created": str(row[3]),
        "updated": str(row[4]),
        "leader_id": row[5],
        "leader_name": row[6],
        "operator": row[7],
        "aws_arn": row[8]
    }


def user_team_row_to_dict(row):
    return {
        "team_name": row[0],
        "user_name": row[1]
    }


def policy_team_row_to_dict(row):
    return {
        "team": row[0],
        "policy_arn": row[1]
    }