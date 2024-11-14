from collections import Counter
from typing import Dict, List, Optional, Tuple
from game_state import GameState
from tiles import Tile, TileType
from mahjong_logic import MahjongLogic


class MahjongAgent:
    def __init__(self, player_idx: int, game_state: GameState):
        self.player_idx = player_idx
        self.game_state = game_state

    def calculate_tile_probabilities(self) -> Dict[Tile, float]:
        """Calculate probability of drawing each tile"""
        if not self.game_state:
            return {}

        # Count visible tiles
        visible_tiles = Counter()
        # Add discards
        for player in self.game_state.players:
            visible_tiles.update(player.discards)
        # Add revealed melds
        for player in self.game_state.players:
            for meld in player.revealed_melds:
                visible_tiles.update(meld)
        # Add own hand
        visible_tiles.update(self.game_state.players[self.player_idx].hand)

        # Calculate probabilities
        probabilities = {}
        total_unknown = 3 * 9 * 4 - sum(visible_tiles.values())

        # Prevent division by zero
        if total_unknown <= 0:
            return {tile: 0.0 for tile in visible_tiles}

        for tile_type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            for value in range(1, 10):
                tile = Tile(tile_type, value)
                visible_count = visible_tiles[tile]
                remaining = max(0, 4 - visible_count)
                probabilities[tile] = (
                    remaining / total_unknown if total_unknown > 0 else 0.0
                )

        return probabilities

    def evaluate_hand(self) -> float:
        """Evaluate current hand strength"""
        if not self.game_state:
            return 0.0

        hand = self.game_state.players[self.player_idx].hand
        if not hand:
            return 0.0

        # First find potential melds
        all_melds = MahjongLogic.find_all_melds(hand)

        # Score for complete melds
        meld_score = len(all_melds) * 10

        # Score for potential pairs
        hand_counter = Counter(hand)
        pair_score = sum(2 for count in hand_counter.values() if count >= 2)

        # Score for sequences that are one tile away from completion
        sequence_potential = 0
        for tile_type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            values = sorted([t.value for t in hand if t.type == tile_type])
            for i in range(len(values) - 1):
                if values[i + 1] - values[i] <= 2:  # Sequential or one gap
                    sequence_potential += 1

        # Score for terminal tiles (1 and 9)
        terminal_score = sum(1 for t in hand if t.value in [1, 9])

        # Combine all scores with weights
        total_score = (
            meld_score * 2.0  # Complete melds are most valuable
            + pair_score * 1.5  # Pairs are good for potential completion
            + sequence_potential * 1.0  # Potential sequences
        )

        # Print detailed scoring for debugging
        # print(f"\nPlayer {self.player_idx} hand evaluation:")
        # print(f"Hand: {[str(t) for t in hand]}")
        # print(
        #     f"Melds ({len(all_melds)}): {[[str(t) for t in meld] for meld in all_melds]}"
        # )
        # print(f"Pairs: {pair_score}")
        # print(f"Sequence potential: {sequence_potential}")
        # print(f"Terminal tiles: {terminal_score}")
        # print(f"Total score: {total_score}")

        return total_score

    def _calculate_efficiency_score(self, hand: List[Tile]) -> float:
        """Calculate how well tiles work together"""
        score = 0
        sorted_hand = sorted(hand, key=lambda t: (t.type.value, t.value))

        for i in range(len(sorted_hand) - 1):
            current = sorted_hand[i]
            next_tile = sorted_hand[i + 1]

            if current.type == next_tile.type:
                # Score for sequential tiles
                if abs(current.value - next_tile.value) <= 2:
                    score += 3 - abs(current.value - next_tile.value)

        return score * 2

    def _would_complete_meld(self, tile: Tile) -> bool:
        """Check if adding this tile would complete a meld"""
        if not self.game_state:
            return False

        hand = self.game_state.players[self.player_idx].hand
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                test_tiles = [hand[i], hand[j], tile]
                if MahjongLogic.is_valid_meld(test_tiles):
                    return True
        return False

    def choose_discard(self) -> Optional[Tile]:
        """Choose which tile to discard using decision theory"""
        if not self.game_state:
            raise ValueError("Game state not set")

        hand = self.game_state.players[self.player_idx].hand
        if not hand:
            return None

        best_discard = None
        best_score = float("-inf")

        for tile in hand:
            # Simulate discard
            hand.remove(tile)
            score = self.evaluate_hand()
            hand.append(tile)

            if score > best_score:
                best_score = score
                best_discard = tile

        return best_discard

    def get_advice(self, hand: List[Tile], visible_tiles: List[Tile] = None) -> str:
        """Provide advice for the current hand"""
        if visible_tiles is None:
            visible_tiles = []

        advice = []
        advice.append("\n=== Hand Analysis ===")
        advice.append(f"Current hand: {', '.join(str(t) for t in sorted(hand, key=lambda x: (x.type.value, x.value)))}")

        # Find complete melds
        complete_melds = MahjongLogic.find_all_melds(hand)
        if complete_melds:
            advice.append("\n✅ Complete melds:")
            for meld in complete_melds:
                advice.append(f"  • {', '.join(str(t) for t in meld)}")

        # Find pairs
        hand_counter = Counter(hand)
        pairs = [(tile, count) for tile, count in hand_counter.items() if count >= 2]
        if pairs:
            advice.append("\n👥 Pairs:")
            for tile, count in pairs:
                advice.append(f"  • {str(tile)} (×{count})")

        # Suggest discards
        suggested_discards = self._get_discard_suggestions(hand)
        if suggested_discards:
            advice.append("\n🗑️ Suggested discards:")
            for tile, reason in suggested_discards[:3]:  # Top 3 suggestions
                advice.append(f"  • {str(tile)}: {reason}")

        # Strategic advice
        score = self.evaluate_hand()
        advice.append("\n💭 Strategic advice:")
        if score > 20:
            advice.append("  Your hand is strong - focus on completing it!")
        elif score > 10:
            advice.append("  Keep building your hand structure.")
        else:
            advice.append("  Consider defensive play and rebuilding your hand.")

        return "\n".join(advice)

    def _get_discard_suggestions(self, hand: List[Tile]) -> List[Tuple[Tile, str]]:
        """Get suggested tiles to discard with reasons"""
        suggestions = []

        for tile in hand:
            # Try discarding this tile
            hand.remove(tile)
            score_after = self.evaluate_hand()
            hand.append(tile)

            # Check if it's connected to other tiles
            is_connected = any(
                abs(t.value - tile.value) <= 2
                for t in hand
                if t.type == tile.type and t != tile
            )

            if not is_connected:
                suggestions.append((tile, "Isolated tile"))
            elif not self._would_complete_meld(tile):
                suggestions.append((tile, "Not part of any potential meld"))

        # Sort by preference (isolated tiles first)
        return sorted(suggestions, key=lambda x: "Isolated" not in x[1])
