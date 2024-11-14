from game_state import GameState
from agent import MahjongAgent
from mahjong_logic import MahjongLogic
from tiles import Tile


class MahjongGame:
    def __init__(self):
        self.game_state = GameState()
        self.agents = [MahjongAgent(i, self.game_state) for i in range(4)]

    def play_game(self) -> int:
        """Play a complete game, return winning player index"""
        try:
            self.game_state.deal_initial_hands()
            max_turns = 100
            turn_count = 0

            # Print initial hands
            print("\nInitial hands:")
            for i, player in enumerate(self.game_state.players):
                print(f"Player {i}: {[str(t) for t in player.hand]}")

            while not self.game_state.game_ended and turn_count < max_turns:
                current_player = self.game_state.current_player

                # Draw tile
                drawn_tile = self.game_state.draw_tile(current_player)
                if not drawn_tile:
                    break

                print(
                    f"\nTurn {turn_count + 1}: Player {current_player} drew {drawn_tile}"
                )

                # Check for win after draw
                if MahjongLogic.is_winning_hand(
                    self.game_state.players[current_player].hand
                ):
                    print(f"Player {current_player} wins by self-draw!")
                    return current_player

                # Let AI choose discard
                discard = self.agents[current_player].choose_discard()
                if not discard:
                    print(f"Warning: Player {current_player} couldn't choose a discard")
                    break

                print(f"Player {current_player} discards {discard}")

                # Process discard
                self.game_state.players[current_player].hand.remove(discard)
                self.game_state.players[current_player].discards.append(discard)
                self.game_state.last_discarded = discard

                # Check if any player can win from this discard
                for i in range(4):
                    if i != current_player:
                        test_hand = self.game_state.players[i].hand + [discard]
                        if MahjongLogic.is_winning_hand(test_hand):
                            print(f"Player {i} wins from discard!")
                            return i

                # Check if any player can claim the discard
                claimed = False
                for i in range(4):
                    if i != current_player and self._can_claim_tile(i, discard):
                        claimed = True
                        self.game_state.current_player = i
                        break

                if not claimed:
                    self.game_state.current_player = (current_player + 1) % 4

                turn_count += 1

            print(f"\nGame ended after {turn_count} turns")
            return self._get_winner()

        except Exception as e:
            print(f"Error during game: {e}")
            return -1

    def _can_claim_tile(self, player_idx: int, tile: Tile) -> bool:
        """Check if player can claim a discarded tile"""
        hand = self.game_state.players[player_idx].hand
        # Check for pung
        matching_tiles = [
            t for t in hand if t.type == tile.type and t.value == tile.value
        ]
        return len(matching_tiles) >= 2

    def _get_winner(self) -> int:
        """Determine the winner based on hand evaluation"""
        best_score = float("-inf")
        winner = -1
        scores = []

        for i in range(4):
            score = self.agents[i].evaluate_hand()
            scores.append(score)
            if score > best_score:
                best_score = score
                winner = i

        print("\nFinal scores:")
        for i, score in enumerate(scores):
            print(f"Player {i}: {score:.2f}")

        return winner
