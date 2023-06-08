import logging.config
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from statement_reader.utils import default_field, now

logger = logging.getLogger()


@dataclass
class Metadata:
    """
    The base metadata object. Contains helper functions and generalized
    metadata
    """

    parse_time: datetime = default_field(now(), init=False, repr=False)

    def get_parse_time_as_iso(self):
        """
        returns parse time in ISO format
        """
        return self.parse_time.isoformat()

    def get_parse_time_as_unix_epoch(self):
        """
        returns parse time in Unix Epoch format
        """
        return self.parse_time.timestamp()


@dataclass
class Input(Metadata):
    """
    The input data to converted from pdf to csv
    """

    path: str = default_field(".")

    def __post_init__(self):
        self.resolved_path = self._resolve_path()

    def _resolve_path(self) -> str:
        """
        resolves input path
        """
        try:
            path = Path(self.path)
        except:
            breakpoint()
        return str(path.resolve())
