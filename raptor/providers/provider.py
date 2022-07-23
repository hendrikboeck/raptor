from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from raptor.tools import io

PROVIDER_DEFAULT_ADDR = "127.0.0.1"
PROVIDER_DEFAULT_PORT = 8080


@dataclass
class AbstractProvider(ABC):

  router: Any

  @staticmethod
  @abstractmethod
  def build(router) -> AbstractProvider:
    raise NotImplementedError()

  @abstractmethod
  def serve(self,
            host: Optional[str] = PROVIDER_DEFAULT_ADDR,
            port: Optional[int] = PROVIDER_DEFAULT_PORT) -> None:
    io.info(f"Serving HTTP server at http://{host}:{port}")