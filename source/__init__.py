import os
from flask import Flask
from flasgger import Swagger


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'source.sqlite'),
        Host='0.0.0.0',
        Port=5000
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    swagger_config = Swagger.DEFAULT_CONFIG
    swagger_config['title'] = "亚信CodeCommit增强API使用说明"
    swagger_config['openapi'] = '3.0.2'
    Swagger(app)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    from . import team
    app.register_blueprint(team.bp)
    from . import project
    app.register_blueprint(project.bp)
    from . import user
    app.register_blueprint(user.bp)
    from . import repo
    app.register_blueprint(repo.bp)
    from . import policy
    app.register_blueprint(policy.bp)
    return app
