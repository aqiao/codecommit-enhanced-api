from source.api_response import *
from source.db import get_db

from flask import (
    Blueprint, request,
)

bp = Blueprint('project', __name__, url_prefix='/project')


@bp.route('/index', methods=('GET',))
def index():
    """
    展示所有项目组信息
    ---
    tags:
      - project
    responses:
        '200':
          description: Successful operation
        '400':
          description: Invalid ID supplied
    """
    try:
        db = get_db()
        rows = db.execute(
            "select * from project"
        ).fetchall()
        projects = []
        for row in rows:
            projects.append(row_to_dict(row))
    except db.InternalError as e:
        return failed_with_data(e, e.strerror)
    else:
        return succeeded_with_data(projects)


@bp.route('/get/<int:project_id>', methods=('GET',))
def get_one(project_id):
    """
    根据id获取项目组信息
    ---
    tags:
      - project
    parameters:
        - name: project_id
          in: path
          description: project id
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
        if project_id is None:
            return failed_without_data(f"Please specify project id")
        row = db.execute(
            'select * from project where id = ?',
            (project_id,)
        ).fetchone()
        if row is None:
            return succeeded_without_data(f"Team {project_id} not found")

    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_with_data(row_to_dict(row))


@bp.route('/create', methods=('PUT',))
def create():
    """
    创建项目
    ---
    tags:
      - project

    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              project_name:
                type: string
                example: 'project1'
              status:
                type: string
                default: '正常'
                enum:
                  - 正常
                  - 停用
              owner_id:
                type: integer
                example: 1
              owner_name:
                type: string
                example: '管理员'
            required:
              - project_name
              - status
              - owner_id
              - owner_name

    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        project_name = request.form['project_name']
        status = request.form['status']
        operator = 1
        db.execute(
            "insert into project (project_name, status, operator) values (?, ?, ?)",
            (project_name, status, operator,)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"project {project_name} added successfully")


@bp.route('/update_name/<int:project_id>', methods=('POST',))
def update_name(project_id):
    """
    修改项目名称
    ---
    tags:
      - project
    parameters:
      - name: project_id
        in: path
        description: team id
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
              project_name:
                type: string
            required:
              - project_name
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        project_name = request.form['project_name']

        db.execute(
            'update project set project_name = ? where id = ?',
            (project_name, project_id)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"project {project_name} name changed successfully")


@bp.route('/update_status/<int:project_id>', methods=('POST',))
def update_status(project_id):
    """
    修改项目状态
    ---
    tags:
      - project
    parameters:
      - name: project_id
        in: path
        description: project id
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
            'update project set status = ? where id = ?',
            (status, project_id)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"project status is changed to {status} successfully")


@bp.route('/add_group', methods=('PUT',))
def add_group():
    """
    将项目添加到项目
    ---
    tags:
      - project
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              project_id:
                type: integer
                example: 1
              project_name:
                type: string
                example: project1
              group_id:
                type: integer
                example: 2
              group_name:
                type: string
                example: group1
          required:
            - project_id
            - group_id
    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    group_id = request.form['group_id']
    group_name = request.form['group_name']
    project_id = request.form['project_id']
    project_name = request.form['project_name']
    operator = 1
    db = get_db()
    try:
        db.execute(
            "insert into team_project (team_id, team_name, project_id, project_name, operator) values (?, ?, ?, ?, ?)",
            (group_id,group_name,project_id,project_name,operator)
        )
        db.commit()
    except Exception as e:
        return failed_without_data(f"When adding group {group_name} to project {project_name} occurred error {str(e)}")
    else:
        return succeeded_without_data(f"Aded group {group_name} to project {project_name} successfully")


@bp.route('/get_groups/<int:project_id>')
def get_groups(project_id):
    """
    根据项目ID获取对应的项目组
    ---
    tags:
      - project
    parameters:
        - name: project_id
          in: path
          description: project id
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
    db = get_db()
    rows = db.execute(
        "select * from team_project where project_id = ?",
        (project_id,)
    ).fetchall()
    groups = []
    if rows is None:
        return succeeded_without_data(f"No groups found within project {project_id}")
    for row in rows:
        groups.append(group_row_to_dict(row))
    return succeeded_with_data(groups)


@bp.route('/delete/<int:project_id>', methods=('DELETE',))
def delete(project_id):
    """
    根据id删除项目
    ---
    tags:
      - project
    parameters:
        - name: project_id
          in: path
          description: project id
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
        if project_id is None:
            return failed_without_data(f"Please specify project")
        db.execute(
            'delete from project where id = ?',
            (project_id,)
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"project deleted successfully")


@bp.route('/batch_delete', methods=("DELETE",))
def batch_delete():
    """
    批量删除项目
    ---
    tags:
      - project
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              project_ids:
                type: string
                example: '1,2,3'
            required:
              - project_ids

    responses:
      '200':
        description: Successful operation
      '505':
        description: Server internal issue
    """
    try:
        db = get_db()
        project_ids = request.form['project_ids']
        if project_ids is None or len(project_ids) == '':
            return failed_without_data(f"Please specify project")
        db.execute(
            'delete from project where id in (' + project_ids + ')'
        )
        db.commit()
    except db.InternalError as e:
        return failed_without_data(e.strerror)
    else:
        return succeeded_without_data(f"project delete in batch successfully")


def row_to_dict(row):
    """
    convert sqlite row object to dict
    :param row: sqlite row
    :return: dict
    """
    return {
        "id": row[0],
        "project_name": row[1],
        "status": row[2],
        "created": str(row[3]),
        "updated": str(row[4]),
        "owner_id": row[5],
        "owner_name": row[6],
        "operator": row[7]
    }


def group_row_to_dict(row):
    return {
        "group_id": row[0],
        "group_name": row[1],
        "project_id": row[2],
        "project_name": row[3],
        "created": str(row[4]),
        "updated": str(row[5]),
        "operator": row[6]
    }