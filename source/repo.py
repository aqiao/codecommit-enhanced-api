import boto3

from source.api_response import *
from flask import(
    Blueprint, request
)
from source.db import get_db

bp = Blueprint('repo', __name__, url_prefix='/repo')
codecommit_client = boto3.client('codecommit')


@bp.route('/index', methods=('GET',))
def index():
    """
    展示所有代码库信息
    ---
    tags:
      - repo
    responses:
        '200':
          description: Successful operation
        '400':
          description: Invalid ID supplied
    """
    db = get_db()
    rows = db.execute('select * from repo').fetchall()
    print(len(rows))
    repos = []
    for row in rows:
        repos.append(row_to_dict(row))
    return succeeded_with_data(repos)


@bp.route('/create', methods=('PUT',))
def create():
    """
    创建CodeCommit代码库
    ---
    tags:
      - repo
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              repo_name:
                type: string
                default: xxx_web
                order: 1
              project_id:
                type: integer
              project_name:
                type: string
              owner_id:
                type: integer
              owner_name:
                type: string
              description:
                type: string
              status:
                type: string
                default: '正常'
                enum:
                  - 正常
                  - 停用
            required:
              - repo_name
              - project_id
              - project_name
              - owner_id
              - owner_name
              - status
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    repo_name = request.form['repo_name']
    project_id = request.form['project_id']
    project_name = request.form['project_name']
    owner_id = request.form['owner_id']
    owner_name = request.form['owner_name']
    description = request.form['description']
    status = request.form['status']
    tags = {
        "project_id": project_id,
        "project_name": project_name,
        "owner_id": owner_id,
        "owner_name": owner_name,
    }
    try:
        repo = codecommit_client.create_repository(repositoryName=repo_name, repositoryDescription=description,
                                                   tags=tags)
        if (not repo) or ('repositoryMetadata' not in repo):
            return None
        repository_meta_data = repo['repositoryMetadata']
        aws_arn = repository_meta_data['Arn']
        clone_url_http = repository_meta_data['cloneUrlHttp']
        clone_url_ssh = repository_meta_data['cloneUrlSsh']
        db = get_db()
        db.execute(
            """
            insert into repo (repo_name
            , description
            , project_id
            , project_name
            , owner_id
            , owner_name
            , status
            , aws_arn
            , clone_url_https
            , clone_url_ssh) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (repo_name, description, project_id, project_name, owner_id, owner_name, status, aws_arn, clone_url_http, clone_url_ssh)
        )
        db.commit()
    except Exception as e:
        return failed_without_data(str(e))
    else:
        return succeeded_without_data(f"CodeCommit repository {repo_name} created successfully")


@bp.route('/get/<string:repo_name>', methods=('GET',))
def get_one(repo_name):
    """
    根据名称获取CodeCommit代码库信息
    ---
    tags:
      - repo
    parameters:
        - name: repo_name
          in: path
          description: 代码库名称
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
    row = db.execute(
        "select * from repo where repo_name = ?",
        (repo_name,)
    ).fetchone()
    if row is None:
        return succeeded_without_data(f"No repo found by name {repo_name}")
    return succeeded_with_data(row_to_dict(row))


@bp.route('/delete/<string:repo_name>', methods=("DELETE",))
def delete(repo_name):
    """
    根据项目名称删除CodeCommit代码库
    ---
    tags:
      - repo
    parameters:
        - name: repo_name
          in: path
          description: 代码库名称
          required: true
          schema:
            type: string

    responses:
        '200':
          description: Successful operation
        '505':
          description: Server internal issue
    """
    try:
        codecommit_client.delete_repository(repositoryName=repo_name)
        db = get_db()
        db.execute("delete from repo where repo_name = ?", (repo_name,))
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"{repo_name} removed")


def row_to_dict(row):
    return {
        "id": row[0],
        "project_id": row[1],
        "project_name": row[2],
        "owner_id": row[3],
        "owner_name": row[4],
        "repo_name": row[5],
        "description": row[6],
        "status": row[7],
        "origin_link": row[8],
        "created": str(row[9]),
        "updated": str(row[10]),
        "operator": row[11],
        "aws_arn": row[12],
        "clone_url_https": row[13],
        "clone_url_ssh": row[14]
    }