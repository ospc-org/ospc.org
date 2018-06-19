from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    if test_config is not None:
        app.config.update(test_config)

    from taxbrain_server import api
    app.register_blueprint(api.bp)

    return app
