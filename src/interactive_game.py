from typing import List, Optional, Tuple, Set, Dict
from collections import Counter
from tiles import Tile, TileType
from game_state import GameState, PlayerState
from agent import MahjongAgent


class InteractiveMahjongGame:
    def __init__(self):
        self.game_state = GameState()
        self.ai_players = [MahjongAgent(i, self.game_state) for i in range(1, 4)]
        self.assistant = MahjongAgent(0, self.game_state)
        self.winning_player = None

    def start_game(self):
        """Start a new game"""
        self.game_state.initialise_tiles()
        self.game_state.deal_initial_hands()
        print("\n=== Game Started ===")
        self.print_game_state()
        self.play_game()

    def check_win(self, player_idx: int) -> bool:
        """Check if a player has won"""
        hand = self.game_state.players[player_idx].hand

        # Sort hand for easier checking
        sorted_hand = sorted(hand, key=lambda t: (t.type.value, t.value))

        # Count tiles of each type
        tile_counts = Counter(sorted_hand)

        # Must have pair and complete melds
        has_valid_hand = False

        # Find one pair and check if remaining tiles form valid melds
        for tile in set(sorted_hand):
            if tile_counts[tile] >= 2:  # Can form a pair
                # Remove pair temporarily
                test_hand = sorted_hand.copy()
                test_hand.remove(tile)
                test_hand.remove(tile)

                # Check remaining tiles
                remaining_melds = self.find_all_possible_melds(test_hand)
                if len(remaining_melds) * 3 == len(
                    test_hand
                ):  # All tiles used in melds
                    has_valid_hand = True
                    break

        # Check revealed melds
        revealed_tiles = sum(
            len(meld) for meld in self.game_state.players[player_idx].revealed_melds
        )

        return has_valid_hand and (len(sorted_hand) + revealed_tiles) >= 14

    def find_all_possible_melds(self, tiles: List[Tile]) -> List[List[Tile]]:
        """Find all possible melds in a list of tiles"""
        melds = []
        if not tiles:
            return melds

        # Try pung
        if len(tiles) >= 3 and tiles[0] == tiles[1] == tiles[2]:
            melds.append([tiles[0], tiles[1], tiles[2]])
            remaining_melds = self.find_all_possible_melds(tiles[3:])
            if remaining_melds is not None:
                melds.extend(remaining_melds)

        # Try chow
        if len(tiles) >= 3 and tiles[0].type in [
            TileType.WAN,
            TileType.TONG,
            TileType.TIAO,
        ]:
            sorted_vals = sorted(
                [t.value for t in tiles[:3] if t.type == tiles[0].type]
            )
            if len(sorted_vals) == 3 and sorted_vals[2] - sorted_vals[0] == 2:
                chow = [t for t in tiles[:3] if t.type == tiles[0].type]
                melds.append(sorted(chow, key=lambda t: t.value))
                remaining_melds = self.find_all_possible_melds(tiles[3:])
                if remaining_melds is not None:
                    melds.extend(remaining_melds)

        return melds

    def play_game(self):
        """Main game loop with winning condition"""
        while not self.game_state.game_ended:
            current_player = self.game_state.current_player

            print(f"\n=== Player {current_player}'s Turn ===")
            print(f"Tiles in wall: {len(self.game_state.wall_tiles)}")

            # Check win condition before draw
            if self.check_win(current_player):
                print(f"Player {current_player} wins!")
                self.game_state.game_ended = True
                self.winning_player = current_player
                break

            # Check if wall is empty
            if len(self.game_state.wall_tiles) < 4:  # Leave some minimum tiles
                print("Game ended in draw - Not enough tiles!")
                self.game_state.game_ended = True
                break

            if current_player == 0:
                self.handle_human_turn()
            else:
                self.handle_ai_turn(current_player)

            # Check win condition after turn
            if self.check_win(current_player):
                print(f"Player {current_player} wins!")
                self.game_state.game_ended = True
                self.winning_player = current_player
                break

            # Update current player
            self.game_state.current_player = (current_player + 1) % 4

    def get_visible_tiles(self) -> List[Tile]:
        """Get all visible tiles in the game"""
        visible_tiles = []

        # Add all discards
        for player in self.game_state.players:
            visible_tiles.extend(player.discards)

        # Add revealed melds
        for player in self.game_state.players:
            for meld in player.revealed_melds:
                visible_tiles.extend(meld)

        # Add human player's hand
        visible_tiles.extend(self.game_state.players[0].hand)

        return visible_tiles

    def handle_human_turn(self):
        """Handle human player's turn with AI assistance"""
        # Draw tile
        drawn_tile = self.game_state.draw_tile(0)
        if not drawn_tile:
            print("No more tiles in wall.")
            return

        print(f"\nYou drew: {drawn_tile}")
        self.print_hand()

        # Check for win
        if self.check_win(0):
            print("You can declare win!")
            choice = input("Declare win? (yes/no): ").strip().lower()
            if choice == "yes":
                print("Congratulations! You win!")
                self.game_state.game_ended = True
                self.winning_player = 0
                return

        # Get and show AI analysis
        analysis = self.get_ai_analysis()
        self.show_analysis(analysis)

        # Get player action
        while True:
            action = self.get_player_action()
            if self.process_player_action(action):
                break

    def handle_ai_turn(self, player_idx: int):
        """Handle AI player's turn with claiming and meld formation"""
        # Draw tile
        drawn_tile = self.game_state.draw_tile(player_idx)
        if not drawn_tile:
            return

        print(f"Player {player_idx} drew a tile")

        # Check for win
        if self.check_win(player_idx):
            print(f"Player {player_idx} declares win!")
            self.game_state.game_ended = True
            self.winning_player = player_idx
            return

        # Try to form melds with the drawn tile
        meld_formed = self._try_form_meld_ai(player_idx, drawn_tile)

        # Always discard a tile at the end of turn, even if meld was formed
        ai_agent = self.ai_players[player_idx - 1]
        discard = ai_agent.choose_discard()

        if discard:
            self.game_state.players[player_idx].hand.remove(discard)
            self.game_state.players[player_idx].discards.append(discard)
            self.game_state.last_discarded = discard
            print(f"Player {player_idx} discards: {discard}")

            # Check if other players can claim the discard
            for other_idx in [(player_idx + i) % 4 for i in range(1, 4)]:  # Check in order
                if other_idx == 0:  # Human player
                    claims = self.can_claim_tile(discard)
                    if claims["pung"] or claims["chow"]:
                        self.handle_claim_opportunity(discard)
                        return  # End turn after claim is handled
                else:  # AI player
                    if self._ai_can_claim(other_idx, discard):
                        if self._handle_ai_claim(other_idx, discard):
                            return  # End turn after claim is handled

            # If no one claimed, move to next player
            self.game_state.current_player = (player_idx + 1) % 4

        print("\nCurrent game state after move:")
        print(
            f"Player {player_idx} melds: {[', '.join(str(t) for t in meld) for meld in self.game_state.players[player_idx].revealed_melds]}"
        )
        print(
            f"Player {player_idx} discards: {len(self.game_state.players[player_idx].discards)}"
        )

    def _try_form_meld_ai(self, player_idx: int, new_tile: Tile) -> bool:
        """Try to form a meld for AI player with the new tile"""
        hand = self.game_state.players[player_idx].hand

        # Try to form pung (three identical tiles)
        matching = [t for t in hand if t.type == new_tile.type and t.value == new_tile.value]
        if len(matching) >= 2:
            # Form pung
            for t in matching[:2]:
                hand.remove(t)
            meld = matching[:2] + [new_tile]
            self.game_state.players[player_idx].revealed_melds.append(meld)
            print(f"Player {player_idx} forms pung: {', '.join(str(t) for t in meld)}")
            
            # Must discard after forming meld
            ai_agent = self.ai_players[player_idx - 1]
            discard = ai_agent.choose_discard()
            if discard:
                hand.remove(discard)
                self.game_state.players[player_idx].discards.append(discard)
                self.game_state.last_discarded = discard
                print(f"Player {player_idx} discards after forming meld: {discard}")
            return True

        # Try to form chow (three consecutive numbers in the same suit)
        if new_tile.type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            # Get all tiles of the same type
            type_tiles = [t for t in hand if t.type == new_tile.type]
            tile_value = new_tile.value

            # Check all possible consecutive sequences that could include the new tile
            for start_value in range(max(1, tile_value - 2), min(8, tile_value + 1)):
                sequence = range(start_value, start_value + 3)
                if tile_value in sequence:
                    # Find the needed values excluding the new tile
                    needed_values = set(sequence) - {tile_value}
                    # Check if we have tiles with these values
                    sequence_tiles = []
                    for value in needed_values:
                        matching_tile = next((t for t in type_tiles if t.value == value), None)
                        if matching_tile:
                            sequence_tiles.append(matching_tile)

                    # If we found both needed tiles, form the chow
                    if len(sequence_tiles) == 2:
                        # Remove the tiles from hand
                        for t in sequence_tiles:
                            hand.remove(t)
                        # Create the meld in correct order
                        meld = sorted([new_tile] + sequence_tiles, key=lambda t: t.value)
                        self.game_state.players[player_idx].revealed_melds.append(meld)
                        print(f"Player {player_idx} forms chow: {', '.join(str(t) for t in meld)}")
                        
                        # Must discard after forming meld
                        ai_agent = self.ai_players[player_idx - 1]
                        discard = ai_agent.choose_discard()
                        if discard:
                            hand.remove(discard)
                            self.game_state.players[player_idx].discards.append(discard)
                            self.game_state.last_discarded = discard
                            print(f"Player {player_idx} discards after forming meld: {discard}")
                        return True

        return False

    def _ai_can_claim(self, player_idx: int, tile: Tile) -> bool:
        """Check if AI player can claim a tile"""
        hand = self.game_state.players[player_idx].hand

        # Check for pung
        matching = [t for t in hand if t.type == tile.type and t.value == tile.value]
        if len(matching) >= 2:
            return True

        # Check for chow (only from player to left)
        if (player_idx - self.game_state.current_player) % 4 == 1:  # Only check for left player
            if tile.type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
                type_tiles = [t for t in hand if t.type == tile.type]
                tile_value = tile.value
                
                # Find possible sequences
                for start in range(tile_value - 2, tile_value + 1):
                    if start >= 1 and start + 2 <= 9:
                        needed = set(range(start, start + 3)) - {tile_value}
                        if all(any(t.value == v for t in type_tiles) for v in needed):
                            return True

        return False

    def _handle_ai_claim(self, player_idx: int, tile: Tile):
        """Handle AI claiming a tile"""
        hand = self.game_state.players[player_idx].hand
        claim_made = False

        # Try pung first
        matching = [t for t in hand if t.type == tile.type and t.value == tile.value]
        if len(matching) >= 2:
            # Form pung
            for t in matching[:2]:
                hand.remove(t)
            meld = matching[:2] + [tile]
            self.game_state.players[player_idx].revealed_melds.append(meld)
            print(f"Player {player_idx} claims pung: {', '.join(str(t) for t in meld)}")
            claim_made = True

        # Try chow if pung wasn't formed
        elif tile.type in [TileType.WAN, TileType.TONG, TileType.TIAO]:
            type_tiles = [t for t in hand if t.type == tile.type]
            values = sorted([t.value for t in type_tiles])
            tile_value = tile.value

            # Find best chow sequence
            for start in range(tile_value - 2, tile_value + 1):
                if start >= 1 and start + 2 <= 9:
                    needed = set(range(start, start + 3)) - {tile_value}
                    sequence_tiles = [t for t in type_tiles if t.value in needed]
                    if len(sequence_tiles) == 2:
                        # Form chow
                        for t in sequence_tiles:
                            hand.remove(t)
                        meld = sorted([tile] + sequence_tiles, key=lambda t: t.value)
                        self.game_state.players[player_idx].revealed_melds.append(meld)
                        print(f"Player {player_idx} claims chow: {', '.join(str(t) for t in meld)}")
                        claim_made = True
                        break

        if claim_made:
            # AI must discard a tile after claiming
            ai_agent = self.ai_players[player_idx - 1]
            discard = ai_agent.choose_discard()
            if discard:
                self.game_state.players[player_idx].hand.remove(discard)
                self.game_state.players[player_idx].discards.append(discard)
                self.game_state.last_discarded = discard
                print(f"Player {player_idx} discards after claim: {discard}")
            
            self.game_state.current_player = player_idx
            return True

        return False

    def get_ai_analysis(self) -> dict:
        """Get comprehensive AI analysis for the current situation"""
        analysis = {
            "hand_evaluation": self.assistant.evaluate_hand(),
            "suggested_discards": self._get_suggested_discards(),
            "winning_probability": self._calculate_winning_probability(),
            "safe_tiles": self._identify_safe_tiles(),
            "dangerous_tiles": self._identify_dangerous_tiles(),
            "strategic_advice": self._get_strategic_advice(),
        }
        return analysis

    def _get_suggested_discards(self) -> List[Tuple[Tile, str]]:
        """Get ordered list of suggested discards with explanations"""
        hand = self.game_state.players[0].hand
        suggestions = []

        for tile in hand:
            # Simulate discard
            hand.remove(tile)
            score_after = self.assistant.evaluate_hand()
            hand.append(tile)

            # Calculate danger level
            danger_level = self._calculate_danger_level(tile)

            suggestions.append(
                (
                    tile,
                    score_after,
                    danger_level,
                    f"Score after discard: {score_after:.1f}, Danger level: {danger_level:.1f}",
                )
            )

        return sorted(suggestions, key=lambda x: (-x[1], x[2]))

    def _calculate_danger_level(self, tile: Tile) -> float:
        """Calculate how dangerous it is to discard this tile"""
        danger = 0
        for player_idx in range(1, 4):
            player_state = self.game_state.players[player_idx]
            waiting_tiles = self._estimate_waiting_tiles(player_state)
            if tile in waiting_tiles:
                danger += 1
        return danger

    def _estimate_waiting_tiles(self, player_state: PlayerState) -> Set[Tile]:
        """Estimate what tiles a player might be waiting for"""
        waiting = set()
        for meld in player_state.revealed_melds:
            if len(meld) == 3:
                tile_type = meld[0].type
                values = sorted(t.value for t in meld)

                if values[2] - values[0] == 2:  # Sequential meld
                    if values[0] > 1:
                        waiting.add(Tile(tile_type, values[0] - 1))
                    if values[2] < 9:
                        waiting.add(Tile(tile_type, values[2] + 1))
        return waiting

    def can_claim_tile(self, tile: Tile) -> dict:
        """Check what claims are possible for a tile"""
        hand = self.game_state.players[0].hand
        claims = {"pung": False, "chow": False}

        # Check for pung
        matching = [t for t in hand if t.type == tile.type and t.value == tile.value]
        if len(matching) >= 2:
            claims["pung"] = True

        # Check for chow (only from player to left)
        if self.game_state.current_player == 3 and tile.type in [
            TileType.WAN,
            TileType.TONG,
            TileType.TIAO,
        ]:
            values = [t.value for t in hand if t.type == tile.type]
            tile_value = tile.value
            for start in range(tile_value - 2, tile_value + 1):
                if start >= 1 and start + 2 <= 9:
                    needed = set(range(start, start + 3)) - {tile_value}
                    if all(v in values for v in needed):
                        claims["chow"] = True
                        break

        return claims

    def handle_claim_opportunity(self, tile: Tile):
        """Handle the opportunity to claim a discarded tile"""
        claims = self.can_claim_tile(tile)

        if not (claims["pung"] or claims["chow"]):
            return

        print(f"\nThe tile {tile} was discarded.")
        available_claims = []
        if claims["pung"]:
            available_claims.append("pung")
        if claims["chow"]:
            available_claims.append("chow")

        print("Available claims:")
        for i, claim in enumerate(available_claims, 1):
            print(f"{i}. {claim}")
        print(f"{len(available_claims) + 1}. pass")

        while True:
            try:
                choice = input("Enter your choice (number): ").strip()
                if not choice.isdigit():
                    print("Please enter a number")
                    continue

                choice = int(choice)
                if choice == len(available_claims) + 1:
                    print("Passed on claiming")
                    return

                if 1 <= choice <= len(available_claims):
                    claim_type = available_claims[choice - 1]
                    if claim_type == "pung":
                        self.handle_pung_claim(tile)
                    elif claim_type == "chow":
                        self.handle_chow_claim(tile)
                    break

                print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def handle_pung_claim(self, tile: Tile):
        """Handle pung claim"""
        hand = self.game_state.players[0].hand
        matching = [t for t in hand if t.type == tile.type and t.value == tile.value]
        if len(matching) >= 2:
            # Form the pung
            for t in matching[:2]:
                hand.remove(t)
            meld = matching[:2] + [tile]
            self.game_state.players[0].revealed_melds.append(meld)
            print(f"Claimed pung: {', '.join(str(t) for t in meld)}")

            # Must discard a tile after claiming
            print("\nYour hand after claim:")
            self.print_hand()
            print("\nYou must discard a tile after claiming.")
            
            while True:
                action = input("\nEnter tile to discard (e.g., 'WAN-1'): ").strip()
                try:
                    discard = self._parse_tile_input(f"discard {action}")
                    if discard in hand:
                        hand.remove(discard)
                        self.game_state.players[0].discards.append(discard)
                        self.game_state.last_discarded = discard
                        print(f"You discarded: {discard}")
                        self.game_state.current_player = 0
                        break
                    else:
                        print("Invalid tile! Choose a tile from your hand.")
                except (ValueError, TypeError):
                    print("Invalid tile format! Use format like 'WAN-1'")

    def handle_chow_claim(self, tile: Tile):
        """Handle chow claim"""
        hand = self.game_state.players[0].hand
        possible_sequences = []
        values = sorted([t.value for t in hand if t.type == tile.type])
        tile_value = tile.value

        # Find all possible chow sequences
        for start in range(tile_value - 2, tile_value + 1):
            if start >= 1 and start + 2 <= 9:
                sequence = set(range(start, start + 3))
                needed = sequence - {tile_value}
                if all(v in values for v in needed):
                    seq_tiles = []
                    for v in range(start, start + 3):
                        if v == tile_value:
                            seq_tiles.append(tile)
                        else:
                            matching = next(t for t in hand if t.type == tile.type and t.value == v)
                            seq_tiles.append(matching)
                    possible_sequences.append(seq_tiles)

        if not possible_sequences:
            print("No valid chow sequences available")
            return

        print("\nPossible chow sequences:")
        for i, sequence in enumerate(possible_sequences, 1):
            print(f"{i}. {', '.join(str(t) for t in sequence)}")
        print(f"{len(possible_sequences) + 1}. cancel")

        # Choose sequence
        while True:
            try:
                choice = input("Choose sequence (number): ").strip()
                if not choice.isdigit():
                    print("Please enter a number")
                    continue

                choice = int(choice)
                if choice == len(possible_sequences) + 1:
                    print("Cancelled chow claim")
                    return

                if 1 <= choice <= len(possible_sequences):
                    sequence = possible_sequences[choice - 1]
                    # Remove used tiles from hand
                    for t in sequence:
                        if t != tile and t in hand:
                            hand.remove(t)
                    self.game_state.players[0].revealed_melds.append(sequence)
                    print(f"Claimed chow: {', '.join(str(t) for t in sequence)}")

                    # Must discard a tile after claiming
                    print("\nYour hand after claim:")
                    self.print_hand()
                    print("\nYou must discard a tile after claiming.")
                    
                    while True:
                        action = input("\nEnter tile to discard (e.g., 'WAN-1'): ").strip()
                        try:
                            discard = self._parse_tile_input(f"discard {action}")
                            if discard in hand:
                                hand.remove(discard)
                                self.game_state.players[0].discards.append(discard)
                                self.game_state.last_discarded = discard
                                print(f"You discarded: {discard}")
                                self.game_state.current_player = 0
                                break
                            else:
                                print("Invalid tile! Choose a tile from your hand.")
                        except (ValueError, TypeError):
                            print("Invalid tile format! Use format like 'WAN-1'")
                    break

                print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def _calculate_winning_probability(self) -> float:
        """Calculate approximate winning probability"""
        hand_score = self.assistant.evaluate_hand()
        return min(max(hand_score / 100.0, 0.0), 1.0)

    def _identify_safe_tiles(self) -> List[Tile]:
        """Identify relatively safe tiles to discard"""
        safe_tiles = []
        hand = self.game_state.players[0].hand

        for tile in hand:
            similar_discarded = sum(
                1
                for player in self.game_state.players
                for discarded in player.discards
                if discarded.type == tile.type and discarded.value == tile.value
            )

            if similar_discarded >= 2:
                safe_tiles.append(tile)

        return safe_tiles

    def _identify_dangerous_tiles(self) -> List[Tile]:
        """Identify potentially dangerous tiles to discard"""
        dangerous_tiles = []
        hand = self.game_state.players[0].hand

        for tile in hand:
            danger_level = 0

            for player_idx in range(1, 4):
                player = self.game_state.players[player_idx]

                for meld in player.revealed_melds:
                    if self._could_complete_sequence(tile, meld):
                        danger_level += 1

                if any(
                    t.type == tile.type and abs(t.value - tile.value) <= 2
                    for meld in player.revealed_melds
                    for t in meld
                ):
                    danger_level += 1

            if danger_level >= 2:
                dangerous_tiles.append(tile)

        return dangerous_tiles

    def _could_complete_sequence(self, tile: Tile, meld: List[Tile]) -> bool:
        """Check if tile could complete a sequence with given meld"""
        if len(meld) < 2 or tile.type not in [
            TileType.WAN,
            TileType.TONG,
            TileType.TIAO,
        ]:
            return False

        values = sorted([t.value for t in meld])
        tile_value = tile.value

        return (
            tile.type == meld[0].type
            and abs(tile_value - values[0]) <= 2
            and abs(tile_value - values[-1]) <= 2
        )

    def _get_strategic_advice(self) -> str:
        """Generate strategic advice based on current situation"""
        hand_score = self.assistant.evaluate_hand()
        tiles_in_wall = len(self.game_state.wall_tiles)

        if self.check_win(0):
            return "You can declare win!"

        if hand_score >= 80:
            return "Very close to winning! Focus on completing the hand."
        elif hand_score >= 60:
            if tiles_in_wall < 30:
                return "Good hand but running out of tiles. Consider aggressive play."
            else:
                return "Strong hand. Look for key tiles to complete it."
        elif hand_score >= 40:
            if tiles_in_wall < 30:
                return (
                    "Time running out. Consider defensive play and quick combinations."
                )
            else:
                return "Decent hand. Watch other players and build your hand carefully."
        else:
            if tiles_in_wall < 30:
                return "Low scoring hand and running out of tiles. Focus on quick completions."
            else:
                return "Rebuild your hand. Focus on efficient tile combinations."

    def show_analysis(self, analysis: dict):
        """Display AI analysis in a readable format"""
        print("\n=== AI Analysis ===")

        print("\n🎯 Suggested Discards:")
        for tile, score, danger, explanation in analysis["suggested_discards"][:3]:
            print(f"  • {tile}: {explanation}")

        print("\n⚠️ Dangerous Tiles:")
        for tile in analysis["dangerous_tiles"]:
            print(f"  • {tile}")

        print("\n✅ Safe Tiles:")
        for tile in analysis["safe_tiles"]:
            print(f"  • {tile}")

        print("\n💭 Strategic Advice:")
        print(f"  {analysis['strategic_advice']}")

        print(f"\n🎲 Winning Probability: {analysis['winning_probability']:.1%}")

    def get_player_action(self) -> str:
        """Get action from human player"""
        print("\nAvailable actions:")
        print("1. Discard <tile> (e.g., 'discard WAN-1')")
        print("2. Show hand")
        print("3. Show analysis")
        print("4. Show game state")

        return input("\nEnter your action: ").strip().lower()

    def process_player_action(self, action: str) -> bool:
        """Process player's action. Returns True if turn is complete."""
        if action.startswith("d"):
            try:
                tile = self._parse_tile_input(action)
                if tile in self.game_state.players[0].hand:
                    self.game_state.players[0].hand.remove(tile)
                    self.game_state.players[0].discards.append(tile)
                    self.game_state.last_discarded = tile
                    print(f"You discarded: {tile}")
                    return True
                else:
                    print("Invalid tile!")
            except ValueError:
                print("Invalid discard format!")
        elif action == "hand":
            self.print_hand()
        elif action == "analysis":
            self.show_analysis(self.get_ai_analysis())
        elif action == "state":
            self.print_game_state()
        else:
            print("Invalid action!")

        return False

    def _parse_tile_input(self, action: str) -> Optional[Tile]:
        """Parse tile from input string (e.g., 'discard WAN-1')"""
        try:
            parts = action.split()
            if len(parts) != 2:
                return None

            tile_str = parts[1]
            value, tile_type = tile_str.split("-")

            tile_type = TileType[tile_type.upper()]
            value = int(value)

            return Tile(tile_type, value)
        except (ValueError, KeyError, IndexError):
            return None

    def print_hand(self):
        """Print human player's hand"""
        hand = sorted(
            self.game_state.players[0].hand, key=lambda t: (t.type.value, t.value)
        )
        print("\nYour hand:")
        print(", ".join(str(tile) for tile in hand))

    def print_game_state(self):
        """Print current game state"""
        print("\n=== Game State ===")
        print(f"Tiles in wall: {len(self.game_state.wall_tiles)}")
        print(f"Current player: {self.game_state.current_player}")

        for i in range(4):
            print(f"\nPlayer {i}:")
            if i == 0:
                print(
                    "Hand:",
                    ", ".join(
                        str(tile)
                        for tile in sorted(
                            self.game_state.players[i].hand,
                            key=lambda x: (x.type.value, x.value),
                        )
                    ),
                )
            else:
                print(f"Hand size: {len(self.game_state.players[i].hand)}")
            print(
                "Discards:",
                ", ".join(str(tile) for tile in self.game_state.players[i].discards),
            )
            print(
                "Revealed melds:",
                [
                    ", ".join(str(tile) for tile in meld)
                    for meld in self.game_state.players[i].revealed_melds
                ],
            )


def main():
    while True:
        game = InteractiveMahjongGame()
        print("Starting Mahjong game...")
        print("Commands:")
        print("- 'discard TYPE-VALUE' (e.g., 'discard WAN-1')")
        print("- 'show hand'")
        print("- 'show analysis'")
        print("- 'show game state'")
        game.start_game()

        if game.winning_player is not None:
            print(f"\nGame ended! Player {game.winning_player} wins!")
        else:
            print("\nGame ended in draw!")

        play_again = input("\nPlay another game? (yes/no): ").strip().lower()
        if play_again != "yes":
            break


if __name__ == "__main__":
    main()
