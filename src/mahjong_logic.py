from collections import Counter
from typing import List, Set
from tiles import Tile, TileType


class MahjongLogic:
    @staticmethod
    def is_winning_hand(tiles: List[Tile]) -> bool:
        """Check if a hand is a winning hand (4 melds + 1 pair)"""
        if len(tiles) != 14:  # Must have exactly 14 tiles
            return False

        # Try each possible pair
        sorted_tiles = sorted(tiles, key=lambda t: (t.type.value, t.value))
        for i in range(len(sorted_tiles) - 1):
            if MahjongLogic.is_valid_pair([sorted_tiles[i], sorted_tiles[i + 1]]):
                # Remove pair and check if remaining tiles form valid melds
                remaining_tiles = sorted_tiles[:i] + sorted_tiles[i + 2 :]
                if MahjongLogic.can_form_melds(remaining_tiles):
                    return True
        return False

    @staticmethod
    def can_form_melds(tiles: List[Tile]) -> bool:
        """Check if tiles can be arranged into valid melds"""
        if not tiles:
            return True
        if len(tiles) % 3 != 0:
            return False

        # Try forming a pung
        if len(tiles) >= 3:
            if (
                tiles[0].type == tiles[1].type == tiles[2].type
                and tiles[0].value == tiles[1].value == tiles[2].value
            ):
                return MahjongLogic.can_form_melds(tiles[3:])

        # Try forming a chow
        if len(tiles) >= 3:
            sorted_vals = sorted(
                [t.value for t in tiles[:3] if t.type == tiles[0].type]
            )
            if len(sorted_vals) == 3 and sorted_vals[2] - sorted_vals[0] == 2:
                remaining = [t for t in tiles[3:]]
                return MahjongLogic.can_form_melds(remaining)

        return False

    @staticmethod
    def is_valid_meld(tiles: List[Tile]) -> bool:
        """Check if tiles form a valid meld (pung or chow)"""
        if len(tiles) != 3:
            return False

        # Check for pung (three of a kind)
        if all(t.type == tiles[0].type and t.value == tiles[0].value for t in tiles):
            return True

        # Check for chow (sequence in same suit)
        if all(t.type == tiles[0].type for t in tiles) and tiles[0].type in [
            TileType.WAN,
            TileType.TONG,
            TileType.TIAO,
        ]:
            values = sorted(t.value for t in tiles)
            if values == list(range(min(values), min(values) + 3)):
                return True

        return False

    @staticmethod
    def is_valid_pair(tiles: List[Tile]) -> bool:
        """Check if tiles form a valid pair"""
        return (
            len(tiles) == 2
            and tiles[0].type == tiles[1].type
            and tiles[0].value == tiles[1].value
        )

    @staticmethod
    def find_all_melds(tiles: List[Tile]) -> List[List[Tile]]:
        """Find all possible melds in a set of tiles"""
        melds = []
        # Convert tiles to counter for efficiency
        tile_counts = Counter(tiles)

        # Find pungs
        for tile in set(tiles):
            if tile_counts[tile] >= 3:
                melds.append([tile] * 3)

        # Find chows
        for tile_type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            for start_value in range(1, 8):
                sequence = [
                    Tile(tile_type, start_value),
                    Tile(tile_type, start_value + 1),
                    Tile(tile_type, start_value + 2),
                ]
                if all(tile_counts[tile] > 0 for tile in sequence):
                    melds.append(sequence)

        return melds

    @staticmethod
    def evaluate_waiting_tiles(hand: List[Tile]) -> Set[Tile]:
        """Find all tiles that would complete the hand"""
        waiting_tiles = set()

        # Try each possible tile
        for tile_type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            for value in range(1, 10):
                test_tile = Tile(tile_type, value)
                test_hand = hand + [test_tile]
                if MahjongLogic.is_winning_hand(test_hand):
                    waiting_tiles.add(test_tile)

        return waiting_tiles
