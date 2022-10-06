from http import HTTPStatus

from flask import make_response, Response


def make_status_response(http_status: HTTPStatus) -> Response:
  http_code = http_status.value
  http_name = http_status.phrase
  resp = make_response(f"{http_code} {http_name}", http_code)
  resp.mimetype = "text/plain"
  return resp