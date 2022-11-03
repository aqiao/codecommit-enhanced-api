import datetime

import boto3

from source.api_response import *
from source.db import get_db
from flask import(
    Blueprint, request
)
from source.decorators import check_token
from io import StringIO

bp = Blueprint('policy', __name__, url_prefix='/policy')
iam_client = boto3.client('iam')

"""
To simplify current design, we just use aws managed policies to implement. There are three aws managed policies

https://docs.aws.amazon.com/codecommit/latest/userguide/security-iam-awsmanpol.html
AWSCodeCommitFullAccess
AWSCodeCommitPowerUser
AWSCodeCommitReadOnly
The first policy is for administrator
The second policy is for common use, since this policy doesn't allow to remove repo
The last one is for readonly users

For more references, see here:
https://docs.aws.amazon.com/service-authorization/latest/reference/list_awscodecommit.html
https://docs.aws.amazon.com/codecommit/latest/userguide/auth-and-access-control-permissions-reference.html
https://docs.amazonaws.cn/en_us/codecommit/latest/userguide/security-iam.html#security_iam_id-based-policy-examples
"""


@bp.route('/index',methods=("GET",))
# @check_token
def index():
    """
    展示所有策略信息
    ---
    tags:
      - policy
    parameters:
    - name: X-USER-NAME
      in: header
      description: 用户邮箱
      required: false
      schema:
        type: string
    - name: X-USER-TOKEN
      in: header
      description: 凭证
      required: false
      schema:
        type: string
    responses:
        '200':
          description: Successful operation
        '400':
          description: Invalid ID supplied
    """
    db = get_db()
    rows = db.execute("select * from policy").fetchall()
    if rows is None:
        succeeded_without_data("No policies found")
    policies = []
    for row in rows:
        policies.append(row_to_dict(row))
    return succeeded_with_data(policies)


def load_policy_template(policy_type):
    with open(f'aws_policies/{policy_type}_template.json', 'r') as json_file:
        print(json_file.read())
        json_file.close()
        # return json.load(json_file)


@bp.route('/create', methods=('PUT',))
def create():
    """
    创建策略
    ---
    tags:
      - policy
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              repos:
                type: string
                example: type * for all repo
              policy_type:
                type: string
                default: developer
                enum:
                  - readonly
                  - developer
                  - admin
            required:
              - repos
              - policy_type

    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        policy_type = request.form['policy_type']
        policy_template = load_policy_template(policy_type)
        # print('--------------')
        # print(policy_template)
        str_repos = request.form['repos']

        if str_repos is None or len(str_repos) == 0 or str_repos == '*':
            policy_template['Statement'][0]['Resource'] = '*'
        else:
            repos = str_repos.split(',')
            rows = db.execute('SELECT aws_arn FROM repo WHERE repo_name IN (%s)' % ("?," * len(repos))[:-1],
                              repos).fetchall()
            if rows is None or len(rows) == 0:
                return failed_without_data(f"No repo found, please verify repo name and try again")
            if len(rows) == 1:
                policy_template['Statement'][0]['Resource'] = rows[0][0]
            else:
                # https://docs.aws.amazon.com/codecommit/latest/userguide/customer-managed-policies.html
                resources = []
                for row in rows:
                    resources.append(row[0])
                policy_template['Statement'][0]['Resource'] = resources

        policy_name = f'codecommit_{policy_type}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        policy_detail = json.dumps(policy_template)
        # print('--------------------')
        # print(policy_detail)

        policy = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy_detail
        )
        operator = 1
        aws_arn = policy['Policy']['Arn']
        db.execute(
            "insert into policy (policy_name, detail,operator,aws_arn) values (?, ?, ?, ?)",
            (policy_name, policy_detail, operator, aws_arn)
        )
        db.commit()
    except Exception as e:
        return failed_without_data(f"Policy {policy_name} created failed: {str(e)}")
    else:
        return succeeded_without_data(f'Policy {policy_name} created successfully')


@bp.route('/get_policy/<string:policy_name>', methods=("GET",))
def get_policy(policy_name):
    """
    根据策略名称获取对应策略
    ---
    tags:
      - policy
    parameters:
        - name: policy_name
          in: path
          description: 策略名称
          required: true
          schema:
            type: string
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    policy = get_db_policy(policy_name)
    return succeeded_with_data(policy)


def get_db_policy(policy_name):
    db = get_db()
    row = db.execute("select * from policy where policy_name = ?",(policy_name,)).fetchone()
    if row is None:
        return None
    return row_to_dict(row)


def get_iam_policy(policy_arn):
    try:
        policy = iam_client.get_policy(PolicyArn=policy_arn)
    except iam_client.exceptions.NoSuchEntityException:
        return None
    except Exception as e:
        raise e
    else:
        if policy is None or 'Policy' not in policy:
            return None
        return policy['Policy']


@bp.route('/delete_policy/<string:policy_name>', methods=("DELETE",))
def delete_policy(policy_name):
    """
    根据策略名称获取对应策略
    ---
    tags:
      - policy
    parameters:
        - name: policy_name
          in: path
          description: 策略名称
          required: true
          schema:
            type: string
    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    db_policy = get_db_policy(policy_name)
    if db_policy is None:
        return succeeded_without_data(f"Policy {policy_name} not found")
    aws_arn = db_policy['aws_arn']
    iam_policy = get_iam_policy(aws_arn)
    if iam_policy:
        iam_client.delete_policy(PolicyArn=aws_arn)
        return succeeded_without_data(f"Policy {policy_name} removed")
    return succeeded_without_data(f"Policy {policy_name} not found")


def row_to_dict(row):
    return {
        "policy_name": row[0],
        "detail": row[1],
        "status": row[2],
        "created": str(row[3]),
        "updated": str(row[4]),
        "operator": row[5],
        "aws_arn": row[6]
    }