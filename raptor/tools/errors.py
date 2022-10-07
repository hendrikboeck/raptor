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
# @package   Paperwrite.PyAdditions.Errors
# @namespace Paperwrite.PyAdditions.Errors
#
# Package containing additional Error types.

from http import HTTPStatus
from typing import Any


class RaptorAbortException(Exception):

  http_status: HTTPStatus

  def __init__(self, http_status: HTTPStatus, *args: object) -> None:
    super().__init__(*args)
    self.http_status = http_status

  def payload(self) -> Any:
    payload = {}
    if len(self.args) == 1:
      payload["message"] = self.args
    else:
      payload = self.args
    return payload
