from http import HTTPStatus

import raptor
from flask import Response, make_response

from raptor.tools.flask import abort


def ping_handler() -> Response:
  resp = make_response("pong", 200)
  resp.mimetype = "text/plain"

  return resp


def abort_handler() -> Response:
  abort(HTTPStatus.BAD_REQUEST, "Job with JID 'test' could not be found")


def exception_handler() -> Response:
  raise Exception("what the fucking hell")


def main() -> None:
  raptor.tools.io.configure("info")

  rt = raptor.Router()
  rt.mount("/", ping_handler, ["GET"])
  rt.mount("/abort", abort_handler, ["GET"])
  rt.mount("/exception", exception_handler, ["GET"])

  pv = rt.build_provider("flask")
  pv.serve("127.0.0.1", 4321)


if __name__ == "__main__":
  main()
