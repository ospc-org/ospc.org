from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    if test_config is not None:
        app.config.update(test_config)

    from api import endpoints
    app.register_blueprint(endpoints.bp)

    return app
