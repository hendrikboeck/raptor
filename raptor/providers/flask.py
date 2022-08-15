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
from typing import Any, Optional
from http import HTTPStatus

# -- LIBRARY
import werkzeug
from flask import Flask, request, Response, make_response
from flask_cors import CORS
import waitress

# -- PROJECT
from raptor.providers.provider import AbstractProvider
from raptor.tools import io


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

    def serve(self, host: str, port: int) -> None:
        super().serve(host, port)

        self.router.print_debug_information(host, port, self)
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
    @flask.route(f"{_prv.router.prefix}/<path:_path>",
                 methods=FLASK_HTTP_METHODS)
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
        status_text = _tools_capitalize_all_string(status_code)

        io.debug(f"    => Outcome: {status_text}")
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
        if isinstance(_ex, werkzeug.exceptions.HTTPException):
            return make_response(_ex)
        else:
            return make_response(str(_ex),
                                 HTTPStatus.INTERNAL_SERVER_ERROR.value)

    return flask
