################################################################################
# raptor, a regex based REST routing library                                   #
# Copyright (C) 2022, Hendrik Boeck <hendrikboeck.dev@protonmail.com>          #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for    #
# more details.                                                                #
#                                                                              #
# You should have received a copy of the GNU General Public License along with #
# this program.  If not, see <https://www.gnu.org/licenses/>.                  #
################################################################################

# -- STL
from dataclasses import dataclass
import traceback
from typing import Any, Optional
from http import HTTPStatus

# -- LIBRARY
from flask import Flask, request, Response, make_response, jsonify
from flask_cors import CORS
import waitress
import fastwsgi
import bjoern

# -- PROJECT
from raptor.providers.provider import AbstractProvider
from raptor.tools import io
from raptor.tools.errors import RaptorAbortException
from raptor.tools.flask import make_status_response


@dataclass
class FlaskProvider(AbstractProvider):
  """
  Provider for the flask library

  Attributes:
    _flask (Flask): flask app for routing through the library

  Args:
    router (Router):
  """

  _flask: Flask

  def __init__(self, router: Any) -> None:
    super().__init__(router)
    self._flask = _factory_build_flask_from_provider(self)

  def serve(self,
            host: str,
            port: int,
            provider: Optional[str] = "waitress") -> None:
    super().serve(host, port)
    self.router.print_debug_information(host, port, self)

    if provider == "fastwsgi":
      fastwsgi.run(wsgi_app=self._flask, host=host, port=port)
    elif provider == "bjoern":
      bjoern.run(self._flask, host, port)
    else:
      waitress.serve(app=self._flask, host=host, port=port)

  def handle_func(self, path: str, http_method: str) -> Response:
    spec = self.router.match(path, http_method)
    return spec.func(**spec.r_vars)


def _tools_capitalize_all_string(_s: str) -> str:
  """
  Capitalizes every word in a string and not just the first letter, as default
  `capitalize() -> str`.

  Args:
    _s (str): string that should be capitalized

  Returns:
    str: capitalized string
  """
  return " ".join([word.capitalize() for word in _s.split(" ")])


def _factory_build_flask_from_provider(_prv: FlaskProvider) -> Flask:
  """
  Capsules the Router inside a Flask application. All changes made to
  router object after built, will affect built Flask provider object.

  Args:
    _prv (FlaskProvider): refrence to parent provider object

  Returns:
    Flask: flask application of parent provider.
  """
  # constant list of all supported REST HTTP method types currently supported by
  # flask.
  FLASK_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

  # create a new Flask app.
  flask = Flask(__name__)

  # if router has the CORS option set, support CORS in flask. Mostly necessary
  # if working with Node.js based frontends in Debug Mode.
  if _prv.router.cors:
    CORS(flask)

  # flask does not recognize an empty path as part of `<path:_path>`. For this
  # reason the empty path has to handled seperatly. Raptor recognizes the empty
  # path as `""`.
  @flask.route(f"{_prv.router.prefix}/", methods=FLASK_HTTP_METHODS)
  def _flask_default_route() -> Response:
    return _prv.handle_func("", request.method)

  # root path supports all rest methods and just passes through the path after
  # the prefix (defined in config)
  @flask.route(f"{_prv.router.prefix}/<path:_path>", methods=FLASK_HTTP_METHODS)
  def _flask_root_route(_path: str) -> Response:
    return _prv.handle_func(_path, request.method)

  # log all incoming request with raptors internal logging tool `io`.
  @flask.before_request
  def _flask_before_request() -> None:
    io.debug(f"{request.method} {request.path} {request.scheme}")

  # Wrapper for
  @flask.after_request
  def _flask_after_request(_resp: Response) -> Response:
    status_code = _resp.status_code
    status_text = HTTPStatus(status_code).phrase

    io.debug(f"    => Outcome: {status_code}, {status_text}")
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

  @flask.errorhandler(Exception)
  def _flask_error_handler(_ex: Exception) -> Response:
    if isinstance(_ex, RaptorAbortException):
      status_code = _ex.http_status
      status_text = HTTPStatus(status_code).phrase

      if status_code < 400:
        io.debug(
            f"    => Called abort(): But why? (HTTP STATUS < 400): {str(_ex)}")
        return make_response(jsonify(_ex.payload()), _ex.http_status.value)
      elif status_code >= 500:
        io.debug(f"    => Called abort(): Internal Error: {str(_ex)}")
        for line in traceback.format_exception(_ex):
          io.error(line)
      else:
        io.debug(f"    => Called abort(): User Error: {str(_ex)}")
        io.warning(
            "User Error may be investigated. Is something suspicious happening?"
        )
        io.warning(f"⋮ Ip: {request.remote_addr}")
        io.warning(f"⋮ On: {request.path}")
        io.warning(f"⋮ Exception: {str(_ex)}")
        io.warning(f"⋮ Response: {status_code} {status_text}")

      return make_status_response(_ex.http_status)
    else:
      io.error("Caught unhandled Exception. Please fix issue in code.")
      io.error("Will treat exception as Internal Server Error (CODE 500).")
      io.error("Program won't terminate, handling Exception gracefully.")
      io.error("⋮")
      for part in traceback.format_exception(_ex):
        for line in part.split("\n"):
          io.error(f"⋮  {line}")
      return make_status_response(HTTPStatus.INTERNAL_SERVER_ERROR)

  return flask
