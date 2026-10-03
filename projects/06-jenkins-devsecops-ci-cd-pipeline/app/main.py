"""A deliberately small Flask service.

It exists to give the DevSecOps pipeline something real to build, test, scan
and deploy. It has no database, no secrets and no outbound calls.
"""

import re

from flask import Flask, Response, jsonify

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,29}$")

INDEX_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>sample-app</title></head>
<body>
<h1>sample-app</h1>
<p>Target of the DevSecOps pipeline. Try:</p>
<ul>
<li><a href="/health">/health</a></li>
<li><a href="/api/greet/world">/api/greet/world</a></li>
<li><a href="/api/add/2/3">/api/add/2/3</a></li>
</ul>
</body>
</html>
"""

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cache-Control": "no-store",
}


def create_app() -> Flask:
    """Build the application. A factory keeps the tests independent."""
    # Every route is a GET and nothing here changes state, so CSRF protection does not apply.
    # SonarQube rule python:S4502 was reviewed for this reason (see sonar-project.properties).
    app = Flask(__name__)

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    @app.get("/")
    def index() -> Response:
        return Response(INDEX_HTML, mimetype="text/html")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/greet/<name>")
    def greet(name: str):
        if not NAME_PATTERN.match(name):
            return jsonify(error="name must start with a letter and use 1-30 letters, digits, - or _"), 400
        return jsonify(message=f"Hello, {name}!")

    @app.get("/api/add/<int:a>/<int:b>")
    def add(a: int, b: int):
        return jsonify(result=a + b)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="method not allowed"), 405

    return app


app = create_app()
