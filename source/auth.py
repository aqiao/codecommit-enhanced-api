import functools
from source.api_response import *
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from source.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        operator = request.headers['operator']
        token = request.headers['token']
        if not username:
            return failed_without_data("User name is required")
        if not email:
            return failed_without_data("Email is required")
        db = get_db()
        password = generate_password_hash(email)
        try:
            db.execute(
                "INSERT INTO user (username, email, password, operator) values (?, ?, ?, ?)",
                (username, email, password, operator)
            )
            db.commit()
        except db.IntegrityError:
            return failed_without_data(f"User {username} is already existed")
        else:
            return succeeded_without_data(f"User {username} register successfully")
