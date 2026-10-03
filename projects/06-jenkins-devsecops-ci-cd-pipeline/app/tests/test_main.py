import pytest

from main import SECURITY_HEADERS, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_index_is_html_and_links_to_the_api(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"/api/greet/world" in response.data


def test_greet_returns_a_greeting(client):
    response = client.get("/api/greet/Jacques")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello, Jacques!"}


@pytest.mark.parametrize("name", ["1bad", "-bad", "a" * 31, "bad.name", "bad%20name"])
def test_greet_rejects_invalid_names(client, name):
    response = client.get(f"/api/greet/{name}")
    assert response.status_code in (400, 404)
    assert "error" in response.get_json()


def test_add_sums_integers(client):
    response = client.get("/api/add/2/3")
    assert response.status_code == 200
    assert response.get_json() == {"result": 5}


def test_add_rejects_non_integers(client):
    assert client.get("/api/add/two/3").status_code == 404


def test_unknown_route_returns_json_404(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}


def test_wrong_method_returns_json_405(client):
    response = client.post("/health")
    assert response.status_code == 405
    assert response.get_json() == {"error": "method not allowed"}


@pytest.mark.parametrize("path", ["/", "/health", "/api/greet/world", "/nope"])
def test_every_response_carries_the_security_headers(client, path):
    response = client.get(path)
    for header, value in SECURITY_HEADERS.items():
        assert response.headers[header] == value
