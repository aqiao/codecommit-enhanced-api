from flask import request, g
from functools import wraps
import jwt
from source.api_response import *
from werkzeug.security import check_password_hash

# def retrieve_token(f):
#     @wraps(f)
#     def get_token(*args, **kwargs):
#         user_name = request.headers.get('X-USER-NAME')
#         password = request.headers.get('X-USER-PASSWORD')
#
# def valid_password(user_name, password):
#     pas


def check_token(f):
    @wraps(f)
    def get_token(*args, **kwargs):
        secret = "Asia_Info_88*"

        user_name = request.headers.get('X-USER-NAME', None)
        token = request.headers.get('X-USER-TOKEN', None)
        try:
            payload = jwt.decode(token, secret, algorithms="HS256")
            iss = payload['iss']
            identify_hash = payload['data']['hash']
            identify = user_name + iss
            if check_password_hash(identify_hash, identify):
                return f(*args, **kwargs)
            else:
                return failed_without_data(f"User {user_name} not authorized")
        except jwt.exceptions.ExpiredSignatureError:
            return failed_without_data("Token expired, please refresh your token")
        except jwt.exceptions.InvalidTokenError:
            return failed_without_data("Invalid token, please retrieve a valid token")
        except Exception as e:
            return failed_without_data(f"Unexpected error: {str(e)}. Please try again or contact administrator")
    return get_token

