from game_state import GameState
from game_engine import MahjongGame
from agent import MahjongAgent
from tiles import Tile, TileType


def main():
    # Play multiple games and collect statistics
    num_games = 1000
    wins = [0] * 4

    for game_num in range(num_games):
        print(f"Playing game {game_num + 1}")
        game = MahjongGame()
        winner = game.play_game()
        wins[winner] += 1

    # Print results
    for i in range(4):
        print(f"Player {i} won {wins[i]} games ({wins[i]/num_games*100:.1f}%)")
    # game_state = GameState()
    # agent = MahjongAgent(0, game_state)  # Player 0

    # # Example hand (you can input your own hand)
    # example_hand = [
    #     Tile(TileType.WAN, 1),
    #     Tile(TileType.WAN, 2),
    #     Tile(TileType.TONG, 3),
    #     Tile(TileType.TONG, 3),
    #     Tile(TileType.TIAO, 5),
    #     Tile(TileType.TIAO, 6),
    #     Tile(TileType.TIAO, 7),
    #     Tile(TileType.WAN, 7),
    #     Tile(TileType.WAN, 8),
    #     Tile(TileType.WAN, 9),
    #     Tile(TileType.TONG, 1),
    #     Tile(TileType.TONG, 9),
    #     Tile(TileType.TIAO, 1),
    # ]

    # # Get and print advice
    # print(agent.get_advice(example_hand))


if __name__ == "__main__":
    main()
