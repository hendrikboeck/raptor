## TODO: rework to google style docstring
# @file
# @author Hendrik Boeck <hendrikboeck.dev@protonmail.com>
#
# @package   Paperwrite.PyAdditions.Errors
# @namespace Paperwrite.PyAdditions.Errors
#
# Package containing additional Error types.

class NotSupportedError(Exception):
  """Error for a not supported feature, function, etc.."""
  pass

class RouteMatchingError(Exception):
  """Error for a not supported feature, function, etc.."""
  pass
