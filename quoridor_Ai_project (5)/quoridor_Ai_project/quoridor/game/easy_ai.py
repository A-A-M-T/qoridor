# game/easy_ai.py
from game.algorithms import easy_get_move

class EasyAI:
    def __init__(self, player):
        self.player = player
        self.last_pos = None 

    def get_move(self, state):
        # Delegate execution entirely to algorithms.py
        move, updated_last_pos = easy_get_move(state, self.player, self.last_pos)
        
        # Keep track of history context internally
        self.last_pos = updated_last_pos
        return move