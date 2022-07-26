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

## TODO: rework to google style docstring
# @file
# @author Hendrik Boeck <hendrikboeck.dev@protonmail.com>
#
# @package   raptor.routing
# @namespace raptor.routing
#
# Package containing REST routing capabilities of Router.

# -- FUTURE (subject to change, handle with care)
from __future__ import annotations
from ctypes import Union
from mimetypes import types_map

# -- STL
import re
import os
import sys
from types import FunctionType
from typing import NamedTuple, Optional, Any, OrderedDict, Pattern
from enum import Enum
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from xml.dom.minidom import NamedNodeMap

# -- PROJECT
from raptor.tools import io
from raptor.tools.errors import RaptorAbortException
from raptor.providers import AbstractProvider, FlaskProvider

SUPPORTED_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
"""list[str]: All supported HTTP methods by raptor.routing package."""


@dataclass
class _RouteVariableTypeRepr():
  """
  Representation tuple for values in RouteVariableType enum.

  Attributes:
    ty (type): Python type of RouteVariableType.
    rx (str): Regular expression for RouteVariableType.

  Args:
    ty (type): Python type of RouteVariableType.
    rx (str): Regular expression for RouteVariableType.
  """

  ty: type
  rx: str


class RouteVariableType(Enum):
  """
  Enum of type identifiers for variables in api-paths. Enum objects hold
  python internal type and regex-expression for variable-type.

  Attributes:
    HEX (_RouteVariableTypeRepr): `hex` -- Hexadecimal number.
    STR (_RouteVariableTypeRepr): `str` -- String.
    INT (_RouteVariableTypeRepr): `int` -- Signed interger.
    UINT (_RouteVariableTypeRepr): `uint` -- Unsigned interger.
    FLOAT (_RouteVariableTypeRepr): `float` -- Floatingpoint number.
    UUID (_RouteVariableTypeRepr): `uuid` -- UUID all versions.
    UUID4 (_RouteVariableTypeRepr): `uuid` -- UUID version 4.
    MD5 (_RouteVariableTypeRepr): `md5` -- MD5 hash.
    SHA1 (_RouteVariableTypeRepr): `sha1` -- SHA-1 hash.
    SHA224 (_RouteVariableTypeRepr): `sha224` -- SHA2-224 hash.
    SHA256 (_RouteVariableTypeRepr): `sha256` -- SHA2-256 hash.
    SHA384 (_RouteVariableTypeRepr): `sha384` -- SHA2-384 hash.
    SHA512 (_RouteVariableTypeRepr): `sha512` -- SHA2-512 hash.
    SHA3_224 (_RouteVariableTypeRepr): `sha3_224` -- SHA3-224 hash.
    SHA3_256 (_RouteVariableTypeRepr): `sha3_256` -- SHA3-256 hash.
    SHA3_384 (_RouteVariableTypeRepr): `sha3_384` -- SHA3-384 hash.
    SHA3_512 (_RouteVariableTypeRepr): `sha3_512` -- SHA3-512 hash.
  """

  HEX = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]+")
  STR = _RouteVariableTypeRepr(str, r"[-a-zA-Z0-9@:%._\+~#=]+")
  PATH = _RouteVariableTypeRepr(str, r"[-a-zA-Z0-9@:%._\+~#=/]+")
  INT = _RouteVariableTypeRepr(int, r"[-+]?\d+")
  UINT = _RouteVariableTypeRepr(int, r"\d+")
  FLOAT = _RouteVariableTypeRepr(float, r"[-+]?\d*\.?\d+|\d+")
  UUID0 = _RouteVariableTypeRepr(
      str, r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}")
  UUID = _RouteVariableTypeRepr(
      str,
      r"[a-f0-9]{8}-?[a-f0-9]{4}-?[1-5][a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
  )
  UUID4 = _RouteVariableTypeRepr(
      str,
      r"[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
  )
  MD5 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{32}")
  SHA1 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{40}")
  SHA224 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{56}")
  SHA256 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{64}")
  SHA384 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{96}")
  SHA512 = _RouteVariableTypeRepr(str, r"[0-9a-fA-F]{128}")
  SHA3_224 = SHA224
  SHA3_256 = SHA256
  SHA3_384 = SHA384
  SHA3_512 = SHA512

  @staticmethod
  def get_rx_types() -> str:
    return "|".join(
        [RouteVariableType.as_string(ty) for ty in RouteVariableType])

  @staticmethod
  def as_string(ty: _RouteVariableTypeRepr) -> str:
    """
    Converts enum-object in string descriptor in lowercase.

    Args:
      ty (_RouteVariableTypeRepr): type as enum-object

    Returns:
      str: enum-object as lowercase string descriptor
    """
    return ty._name_.lower()

  @staticmethod
  def from_string(ty: str) -> _RouteVariableTypeRepr:
    """
    Gets the corresponding enum-object for specified type defined as string in
    template route. Defaults to RouteVariableType.STR.

    Args:
      ty (str): type in template route as string

    Returns:
      _RouteVariableTypeRepr: enum-object for specified type
    """
    ty = str(ty).upper()
    return RouteVariableType.__dict__.get(ty, RouteVariableType.STR)


@dataclass
class RouteVariable():
  """
  Named tuple for specifying a path-variable template in a template route.

  Attributes:
    index (int): Index of module after .split("/")
    ty (type): Represented python type of variable
    key (str): Key of variable.

  Args:
    ty (type): Represented python type of variable
    key (str): Key of variable.
  """

  key: str
  rxt: RouteVariableType


class HttpMethodsMap():
  """
  Class for storing an retrieving function-pointers corresponding to a
  specific HTTP Method.
  """

  _internal: dict[str, FunctionType]
  """Dictionary for mapping HTTP methods to a function pointer"""

  def __init__(self) -> None:
    self._internal = {}

  def register(self, http_methods: list[str], func: FunctionType) -> None:
    """
    Maps a function-pointer to specific HTTP Method(s).

    Args:
      http_methods (list[str]): List of HTTP Methods that are accepted.
      func (FunctionType): Function-pointer to function, that should be
          executed when http-methods are called.

    Raises:
      Exception: If HTTP method is unkown and therefore not in the
          `SUPPORTED_HTTP_METHODS` list.
    """
    for method in http_methods:
      # check if `method` is valid http-method
      if method in SUPPORTED_HTTP_METHODS:
        # map function pointer to key `method`
        self._internal[method] = func
      else:
        # throw excpetion, if `method` is not a http-method
        raise Exception(f"unsupported rest-method: '{method}'")

  def get(self, http_method_type: str) -> Optional[FunctionType]:
    """
    Returns the function-pointer corresponding to HTTP request method.

    @return function-pointer for HTTP Method, None if invalid HTTP request
    method
    """
    return self._internal.get(http_method_type)


@dataclass
class VarFilter():
  type_map: list[type]

  def use(self, vars: Union[tuple, list]) -> list:
    return [t(v) for t, v in zip(self.type_map, vars)]


class Route():
  """
  Defines a templated path object for Router to figure out the original
  templated path, position and type of path-variables and function pointers
  for specific HTTP method.

  Attributes:
    tmpl_string (str): Original templated path string from which object was
        built.
    tmpl_vars (list[RouteVariable]): List of extracted path variables, with
        position, type and name.
    http_methods_map (HttpMethodsMap): Dictionary of HTTP methods mapped to
        corresponding function pointers.

  Args:
    tmpl_string (str): string that describes route template
    tmpl_vars (list[RouteVariable]): list of extracted vars from tmpl_string
    func (FunctionType): function-pointer
    http_methods (list[str]): list of HTTP Methods that are accepted
  """

  tpl: str
  var_filter: VarFilter
  http_methods_map: HttpMethodsMap

  def __init__(self, tpl: str, var_filter: VarFilter, func: FunctionType,
               http_methods: list[str]) -> None:
    self.tpl = tpl
    self.var_filter = var_filter
    self.http_methods_map = HttpMethodsMap()
    self.http_methods_map.register(http_methods, func)


class RouteHandle(NamedTuple):
  args: list
  func: FunctionType


class Router():
  """
  Class is a superset of the flask library. flask is used to serve the API and
  also to handle the request via the request object, which flask provides. The
  Router class only replaces the standard routing of flask, with a more
  versatile regex router, than the default flask router.

  Attributes:
    routes (dict[Pattern, TemplatedRoute]):
    prefix (str):
    cors (bool):

  Args:
    prefix (str, optional):
    cors (bool, optional):
  """

  routes: OrderedDict[Pattern, Route]
  prefix: str

  def __init__(self, prefix: str = "") -> None:
    self.routes = OrderedDict()
    self.prefix = prefix

  def mount(self, tpl: str, func: FunctionType,
            http_methods: list[str]) -> Router:
    """
    Registers a handler function for a specific template-route. Variables
    have to be declared as "{name:type}" (supported types can be found in
    RocketPathVariableTypes).

    Args:
      route_string (str): Template path for route as string.
      func (FunctionType): Function that should be run on route-match.
      accepted_http_methods (list[str]): List of HTTP Methods that are
          accepted.

    Returns:
      Router: Reference to self object, for chaining commands
    """
    # split route into individual modules
    modules = tpl.split("/")
    modules = list(filter(("").__ne__, modules))
    tpl = "/".join(modules)
    rxr = tpl
    print(f"{rxr=}")
    # initialize list for varibles found in path
    var_rx = f"{{(\w+):({RouteVariableType.get_rx_types()})}}"
    var_list = re.findall(var_rx, tpl)
    var_filters = []
    for key, ty in var_list:
      rvt = RouteVariableType.from_string(ty).value
      rxr = rxr.replace(f"{{{key}:{ty}}}", f"({rvt.rx})")
      var_filters.append(rvt.ty)
    rxr = f"^{rxr}$"

    print(f"registered {rxr}")

    # register route-template under regex in container 'routes'
    if self.routes.get(rxr) is None:
      self.routes[rxr] = Route(tpl, VarFilter(var_filters), func, http_methods)
    else:
      self.routes[rxr].http_methods_map.register(http_methods, func)

    return self

  def match(self, req_route: str, http_method: str) -> RouteHandle:
    """
    Will try to find a match for a given route in internal template-paths. If
    none can be found, None will be returned. If a route has been found, a
    RocketSpecificPath with the variables and function will be returned.

    @param  route   api path with variables set
    @param  http_method   HTTP method that was used for request as string

    @return RocketSpecificPath for first parameter in tuple. If an error occurs,
    second parameter will be set to an Error object of scheme
    `Error(Msg, HttpStatus)`.
    """
    r = None
    args = None

    # get templates that match regex and path
    for rx, route in self.routes.items():
      if re.match(rx, req_route):
        r = route
        uargs = re.findall(rx, req_route)[0]
        args = route.var_filter.use(uargs)
        break

    # only one template should be returned for a route. If more then one are
    # returned, raise RaptorAbortException.
    if r is None:
      raise RaptorAbortException(
          HTTPStatus.NOT_FOUND,
          "Route could not be matched to a registered template")

    # check if function is supported by
    func = r.http_methods_map.get(http_method)
    if func is None:
      raise RaptorAbortException(HTTPStatus.METHOD_NOT_ALLOWED,
                                 "No function was mapped to HTTP method")

    # return route object for specific route
    io.debug(f"    => Matched: ({func.__name__}) {http_method} {r.tpl}")
    io.debug(f"    => Vars: {args}")
    return RouteHandle(args, func)

  def print_debug_information(self, host: str, port: int,
                              provider: AbstractProvider) -> None:
    """
    Prints detailed debug information on router.

    Examples:

      2022/04/20 08:53:07 (UTC) DEBUG    | Routes:
      2022/04/20 08:53:07 (UTC) DEBUG    |     - /hello/{name:str} GET,POST
      2022/04/20 08:53:07 (UTC) DEBUG    | Environment: "/pate-wapi"
      2022/04/20 08:53:07 (UTC) DEBUG    | Serving REST API at "/pate-wapi/Paperwrite/Router.py"
      2022/04/20 08:53:07 (UTC) DEBUG    | Mounting at http://0.0.0.0:4321/api/w
    """
    routes_detailed = self.get_routes_detailed()
    home_path = str(Path.home())
    intepreter_path = sys.executable.replace(home_path, "~")
    cwd_path = os.getcwd().replace(home_path, "~")

    io.debug(f"Python Interpreter: {intepreter_path}")
    io.debug(f"Working Directory:  {cwd_path}")
    io.debug(f"REST Provider:      {provider.__class__.__name__}")
    io.debug(f"Router Mountpoint:  http://{host}:{port}{self.prefix}")
    io.debug("Routes:")
    for route in routes_detailed:
      io.debug(f"    - {route}")

  def get_routes(self) -> list[str]:
    """
    Will return a list with templated path strings of all routes as strings,
    that are currently stored inside the router.

    Returns:
      list[str]: List of routes as string.
    """
    return [t.tpl for t in self.routes.values()]

  def get_routes_detailed(self) -> list[str]:
    """
    Will return a list with templated path string of all routes, that are
    currently stored inside the router, with their accepted REST method(s)
    (divided by `,`) appended as strings (scheme:
    `<Templated Path> <REST Methods>`).

    Returns:
      list[str]: List of routes and their accepted HTTP method(s) as string.
    """
    results = []

    # iterate through routes
    for t in self.routes.values():
      # get all methods, for which the function-pointer is not None and
      # therefore accepted by the route
      methods = t.http_methods_map._internal.keys()
      methods = ",".join(methods)
      # append combined string to results
      results.append(f"{t.tpl} {methods}")

    return results

  def build_provider(self, name: str = "flask") -> AbstractProvider:
    name = name.lower()
    if name == "flask":
      return FlaskProvider(self)
    else:
      raise RuntimeError()
