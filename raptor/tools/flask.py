from http import HTTPStatus
from typing import NoReturn

from flask import make_response, Response

from raptor.tools.errors import RaptorAbortException


def make_status_response(http_status: HTTPStatus) -> Response:
  http_code = http_status.value
  http_name = http_status.phrase
  resp = make_response(f"{http_code} {http_name}", http_code)
  resp.mimetype = "text/plain"
  return resp


def abort(http_status: HTTPStatus, *args: object) -> NoReturn:
  raise RaptorAbortException(http_status, *args)