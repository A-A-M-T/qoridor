from utils.constants import AI_EASY, AI_MEDIUM, AI_HARD
from game.easy_ai import EasyAI
from game.medium_ai import MediumAI
from game.hard_ai import HardAI


class QuoridorAI:
    def __init__(self, player, difficulty):
        self.player = player
        self.difficulty = difficulty
        self.tt = {}  # Shared transposition table container for non-class strategies

        if difficulty == AI_EASY:
            self.ai = EasyAI(player)

        elif difficulty == AI_MEDIUM:
            self.ai = MediumAI(player)
            
        elif difficulty == AI_HARD:
            self.ai = HardAI(player)

        else:
            # Fallback strategy if custom rules are requested out of boundaries
            self.ai = None

    def get_move(self, state):
            return self.ai.get_move(state)
            
       
