import copy

from game.algorithms import minimax, get_all_moves, apply_move


class HardAI:

    def __init__(self, player):

        self.player = player

        self.tt = {}

    def get_move(self, state):

        best_move = None

        best_score = float("-inf")

        self.tt.clear()

        # iterative deepening
        for depth in range(1,3 ):

            for move in get_all_moves(state, self.player):

                ns = apply_move(copy.deepcopy(state), move, self.player)

                score = minimax(
                    ns,
                    depth - 1,
                    float("-inf"),
                    float("inf"),
                    False,
                    self.player,
                    self.tt,
                )

                if score > best_score:

                    best_score = score

                    best_move = move

        return best_move
