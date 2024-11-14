from enum import Enum
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Optional
from collections import Counter


class TileType(Enum):
    WAN = "Wan"  # 万
    TONG = "Tong"  # 筒
    TIAO = "Tiao"  # 条


@dataclass(frozen=True)
class Tile:
    type: TileType
    value: int  # 1-9 for suits

    def __str__(self):
        return f"{self.value}-{self.type.value}"

    def __hash__(self):
        return hash((self.type, self.value))
