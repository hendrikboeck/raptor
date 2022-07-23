from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime
from http import HTTPStatus

import werkzeug
from flask import Flask, request, Response, make_response, jsonify
from flask_cors import CORS
import waitress

from raptor.providers.provider import AbstractProvider, PROVIDER_DEFAULT_ADDR, PROVIDER_DEFAULT_PORT
from raptor.tools import io


@dataclass
class FlaskProvider(AbstractProvider):

  app: Flask

  @staticmethod
  def build(router: Any) -> AbstractProvider:
    app = _build_flask_provider_from_router(router)
    return FlaskProvider(router, app)

  def serve(self,
            host: Optional[str] = PROVIDER_DEFAULT_ADDR,
            port: Optional[int] = PROVIDER_DEFAULT_PORT) -> None:
    super().serve(host, port)

    self.router.print_debug_information(host, port, self)
    waitress.serve(app=self.app, host=host, port=port)

  def handle_func(self) -> Response:
    pass


##
# Capsules the Router inside a Flask application. All changes made to
# router object after built, will affect built Flask provider object.
#
# @param  router  router object from which provider should be built
# @return Flask application of router
def _build_flask_provider_from_router(router: Any) -> Flask:
  # create base flask provider object
  provider = Flask(__name__)
  # enable cors for flask
  if router.cors:
    CORS(provider)

  def _capitalize(_s: str) -> str:
    return " ".join([word.capitalize() for word in _s.split(" ")])

  # root path supports all rest methods and just passes through the path after
  # the prefix (defined in config)
  @provider.route(f"{router.prefix}/",
                  methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
  def _provider_index_route() -> Response:
    # passthrough to Router
    return router.handle_func("", request.method)

  # root path supports all rest methods and just passes through the path after
  # the prefix (defined in config)
  @provider.route(f"{router.prefix}/<path:_p>",
                  methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
  def _provider_root_route(_p: str) -> Response:
    # passthrough to Router
    return router.handle_func(_p, request.method)

  @provider.before_request
  def _provider_before_request() -> None:
    io.debug(f"{request.method} {request.path} {request.scheme}")

  @provider.after_request
  def _provider_after_request(_resp: Response) -> Response:
    status_code = _resp.status_code

    io.debug(f"    => Outcome: {_capitalize(_resp.status)}")
    if status_code < 400:
      io.info(f"{request.method} {request.path} {request.scheme}, "
              f"{request.remote_addr} - {status_code}")
    elif status_code >= 500:
      io.error(f"{request.method} {request.path} {request.scheme}, "
               f"{request.remote_addr} - {status_code}")
    else:
      io.warning(f"{request.method} {request.path} {request.scheme}, "
                 f"{request.remote_addr} - {status_code}")

    return _resp

  # global error handler for flask.
  @provider.errorhandler(Exception)
  def _provider_error_handler(_ex: Exception) -> Response:
    if router.propagate_errors:
      http_status = HTTPStatus.INTERNAL_SERVER_ERROR
      ex_msg = str(_ex)

      if isinstance(_ex.args, tuple):
        http_status = _ex.args[1]
        ex_msg = str(_ex.args[0])

      # create json response with information on caught error
      msg = {
          "success": False,
          "tod": datetime.now().isoformat(),  # time of discovery
          "error": {
              "type": _ex.__class__.__name__,
              "message": ex_msg,
              "http_name": http_status.phrase,
              "http_code": http_status.value
          }
      }
      # print debug information on caught error
      io.debug(f"    => Exeption: {_ex.__class__.__name__}")
      io.debug(f"        !> {ex_msg}")

      return make_response(jsonify(msg), http_status.value)
    else:
      if isinstance(_ex, werkzeug.exceptions.HTTPException):
        return make_response(_ex)
      else:
        return make_response("", HTTPStatus.INTERNAL_SERVER_ERROR.value)

  # return built provider
  return provider