import random
from tiles import Tile, TileType
from typing import List, Optional


class GameState:
    def __init__(self):
        self.initialise_tiles()
        self.players = [PlayerState() for _ in range(4)]
        self.current_player = 0
        self.last_discarded: Optional[Tile] = None
        self.discarded_tiles: List[Tile] = []
        self.game_ended = False
        self.total_tiles = 3 * 9 * 4

    def initialise_tiles(self):
        """Initialise the complete set of Mahjong tiles"""
        self.wall_tiles = []
        # Add suited tiles (WAN, TONG, TIAO)
        for tile_type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            for value in range(1, 10):
                for _ in range(4):  # 4 of each tile
                    self.wall_tiles.append(Tile(tile_type, value))

        random.shuffle(self.wall_tiles)

    def deal_initial_hands(self):
        """Deal 13 tiles to each player"""
        print("Dealing initial hands...")
        for i in range(4):
            self.players[i].hand = self.wall_tiles[i*13:(i+1)*13]
            # Sort hands for better readability
            self.players[i].hand.sort(key=lambda t: (t.type.value, t.value))
            print(f"Player {i} dealt {len(self.players[i].hand)} tiles")
        self.wall_tiles = self.wall_tiles[52:]  # Remove dealt tiles from wall
        print(f"Remaining wall tiles: {len(self.wall_tiles)}")

    def draw_tile(self, player_idx: int) -> Optional[Tile]:
        """Draw a tile from the wall for a player"""
        if not self.wall_tiles:
            self.game_ended = True
            return None
        tile = self.wall_tiles.pop(0)
        self.players[player_idx].hand.append(tile)
        return tile


class PlayerState:
    def __init__(self):
        self.hand: List[Tile] = []
        self.revealed_melds: List[List[Tile]] = []
        self.discards: List[Tile] = []
        self.is_waiting = False  # Waiting for win
