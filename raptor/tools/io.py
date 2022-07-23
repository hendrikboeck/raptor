##
# @file
# @author Hendrik Boeck <hendrikboeck.dev@protonmail.com>
#
# @package   raptor.io
# @namespace raptor.io
#
# Package containing internal logger and io functions, this package will be
# initialized in the Paperwrite.Application.ApplicationContext.__init__
# function. Furthermore can this package be configured through the global
# configuration file in the section `io`
# (see Paperwrite.Configuration.ioConfiguration).
#
# @see
#   - Paperwrite.Application.ApplicationContext
#   - Paperwrite.Configuration.ioConfiguration

# -- STL
from datetime import datetime
import logging
import sys
import time
from typing import Optional

TZ_NAME = time.tzname[0]

LOGGER_NAME = "ppw-logger"
"""
str: Name of logger, which will be used to write to CLI and to log file in
package.
"""

LEVELS = {
    "DEBUG": logging.DEBUG,  # 10
    "INFO": logging.INFO,  # 20
    "WARNING": logging.WARN,  # 30
    "ERROR": logging.ERROR,  # 40
    "CRITICAL":
        logging.CRITICAL  # 50
}
"""
dict[str, int]: Dictionary, mapping configureable logger levels from
configuration file to internal values from `logging` library.
"""

IO_STREAMS = {"SYS:STDOUT": sys.stdout, "SYS:STDERR": sys.stderr}
"""
dict[str, TextIO]: Dictionary mapping configureable CLI-streams from
configuration file options to internal values from `sys` package.
"""

_logger = logging.getLogger(LOGGER_NAME)
"""
logging.Logger: Logger object, which has LOGGER_NAME as identification. Will be
independent from root logger of python, as it will not propage messages to it.
"""


class ColoredCliFormatter(logging.Formatter):
  """
  Class that creates a specific logging.Formatter for the CLI logger of _logger.
  Colors that are used for different logging levels can be configured via the
  static variable FORMATS. Colors use the prefix `\033`  (see
  https://misc.flogisoft.com/bash/tip_colors_and_formatting).

  Attributes:
    FORMAT (str): Format string from `_log_formatter` with added general
      formating like bold text and space reserved for levelname. Placeholder
      `%(logcolor)` is used for later replacement with levelcolor.
    DATETIME (str): Format string for formating the time inside log messages.
    FORMATS (dict[int, str]): Dictionary that holds specific value for
      placeholder `%(logcolor)` mapped to different logging levels.
  """

  FORMAT = f"\033[1m%(asctime)s ({TZ_NAME}) %(logcolor)%(levelname)-8s\033[39m |\033[0m %(message)s"
  DATETIME = "%Y/%m/%d %H:%M:%S"
  FORMATS = {
      logging.DEBUG: FORMAT.replace("%(logcolor)", "\033[96m"),  # light cyan
      logging.INFO: FORMAT.replace("%(logcolor)", "\033[90m"),  # light gray
      logging.WARNING: FORMAT.replace("%(logcolor)",
                                      "\033[93m"),  # light yellow
      logging.ERROR: FORMAT.replace("%(logcolor)", "\033[91m"),  # light red
      logging.CRITICAL: FORMAT.replace("%(logcolor)",
                                       "\033[95m"),  # light magenta
  }

  def format(self, record: logging.LogRecord) -> str:
    """
    Args:
      record (logging.LogRecord): specific log record

    Returns:
      str: formated record as str
    """
    logFmt = self.FORMATS.get(record.levelno)
    formatter = logging.Formatter(logFmt, self.DATETIME)
    return formatter.format(record)

  def get_prefix(self, level: str, indent: Optional[int] = 0) -> str:
    level = level.upper()
    levelno = LEVELS.get(level)

    result = self.FORMATS.get(levelno)
    result = result.replace("%(asctime)s",
                            datetime.now().strftime(self.DATETIME))
    result = result.replace("%(levelname)-8s",
                            level.ljust(8)).replace("%(message)s", "")
    return result + indent * "    "


_log_formatter = logging.Formatter(
    f"%(asctime)s ({TZ_NAME}) %(levelname)-8s | %(message)s",
    "%Y/%m/%d %H:%M:%S")
"""
logging.Formatter: Global formatter object, which defines the formatting of
logging messages printed to log file of logger.
"""

_cli_formatter = ColoredCliFormatter()
"""
ColoredCliFormatter: Global formatter object, which defines the formatting of
logging messages printed to cli output of logger.
"""


def configure(level: str,
              stream: Optional[str] = "SYS:STDERR",
              filepath: Optional[str] = None) -> None:
  """Configures global variables and adds file- and cli-handler to logger.

  Args:
    level (str):
    stream (str, optional):
    filepath (str, optional):
  """
  global _logger, _cli_formatter, _log_formatter

  level = level.upper()
  log_level = LEVELS.get(level, LEVELS["INFO"])
  _logger.setLevel(log_level)

  console_stream = IO_STREAMS.get(stream, "SYS:STDERR")
  console_handler = logging.StreamHandler(console_stream)
  console_handler.setLevel(log_level)
  console_handler.setFormatter(_cli_formatter)
  _logger.addHandler(console_handler)

  if filepath is not None:
    file_handler = logging.FileHandler(filepath)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(_log_formatter)
    _logger.addHandler(file_handler)

  # dont't propagate log messages to main logger
  _logger.propagate = False


println = print
"""Alias for default python `print` function.

This function is just an alias for the default `print` function of python. It
is used so that all io operations are streamlined and can be altered in a
single place.

Examples:

  >>> from raptor import io
  >>> io.println("Hello World!")
  Hello World
"""

debug = _logger.debug
"""Alias for `logging.debug` function over static `_logger`.

This function is just an alias for the `logging.debug` function over the
static `_logger` variable. It is used so that all io operations are streamlined
and can be altered in a single place.

Examples:

  >>> from raptor import io
  >>> io.debug("Hello World!")
  2022/04/05 10:42:35 (UTC) DEBUG    | Hello World!
"""

info = _logger.info
"""Alias for `logging.info` function over static `_logger`.

This function is just an alias for the `logging.info` function over the
static `_logger` variable. It is used so that all io operations are streamlined
and can be altered in a single place.

Examples:

  >>> from raptor import io
  >>> io.info("Hello World!")
  2022/04/05 10:42:08 (UTC) INFO     | Hello World!
"""

warning = _logger.warning
"""Alias for `logging.warning` function over static `_logger`.

This function is just an alias for the `logging.warning` function over the
static `_logger` variable. It is used so that all io operations are streamlined
and can be altered in a single place.

Examples:

  >>> from raptor import io
  >>> io.warning("Hello World!")
  2022/04/05 10:41:28 (UTC) WARNING  | Hello World!
"""

error = _logger.error
"""Alias for `logging.error` function over static `_logger`.

This function is just an alias for the `logging.error` function over the
static `_logger` variable. It is used so that all io operations are streamlined
and can be altered in a single place.

Examples:

  >>> from raptor import io
  >>> io.error("Hello World!")
  2022/04/05 10:42:16 (UTC) ERROR    | Hello World!
"""

critical = _logger.critical
"""Alias for `logging.critical` function over static `_logger`.

This function is just an alias for the `logging.critical` function over the
static `_logger` variable. It is used so that all io operations are streamlined
and can be altered in a single place.

Examples:

  >>> from raptor import io
  >>> io.critical("Hello World!")
  2022/04/05 10:41:34 (UTC) CRITICAL | Hello World!

"""

get_prefix = _cli_formatter.get_prefix