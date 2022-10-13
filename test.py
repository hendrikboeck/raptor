from http import HTTPStatus

import raptor
from flask import Response, make_response
from raptor.tools import io

from raptor.tools.flask import abort, make_status_response


def ping_handler() -> Response:
  resp = make_response("pong", 200)
  resp.mimetype = "text/plain"

  return resp


def excpetion() -> Exception:
  return Exception("lul")


def abort_handler() -> Response:
  #abort(HTTPStatus.BAD_REQUEST, "Job with JID 'test' could not be found")
  some_task = excpetion()
  print(f"{some_task=}")
  abort(HTTPStatus.INTERNAL_SERVER_ERROR, some_task)


def exception_handler() -> Response:
  raise Exception("what the fucking hell")


def test_handler(var: str) -> Response:
  io.debug(f"    => {var=}")
  return make_status_response(HTTPStatus.OK)


def main() -> None:
  raptor.tools.io.configure("debug", simple=True)

  rt = raptor.Router()
  rt.mount("/", ping_handler, ["GET"])
  rt.mount("/abort", abort_handler, ["GET"])
  rt.mount("/exception", exception_handler, ["GET"])
  rt.mount("/test/{var:str}.jpg", test_handler, ["GET"])

  pv = rt.build_provider("flask")
  pv.serve("127.0.0.1", 4321)


if __name__ == "__main__":
  main()
