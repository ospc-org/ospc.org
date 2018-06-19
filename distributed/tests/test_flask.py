import pytest

@pytest.fixture
def app():
    app = create_app({'TESTING': True})

    yield app

@pytest.fixture
def client(app):
    return app.test_client()


def test_hello(client):
    resp = client.get('/hello')
    print(resp)
