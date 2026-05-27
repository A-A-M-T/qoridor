# game/medium_ai.py
import random
from game.algorithms import get_all_moves, evaluate

class MediumAI:
    def __init__(self, player, mistake_chance=0.1):
        self.player = player
        # 0.15 means there is a 15% chance the AI will make a random move instead of the perfect move.
        self.mistake_chance = mistake_chance

    def get_move(self, state):
        # 1. Get ALL possible moves (Pawn + some strategic walls)
        possible_moves = get_all_moves(state, self.player)
        
        if not possible_moves:
            return None

        # --- MISTAKE POLICY ---
        if random.random() < self.mistake_chance:
            return random.choice(possible_moves)
        # ----------------------
        
        best_score = float('-inf')
        best_moves = []

        # 2. "Look Ahead" 1 move
        for move in possible_moves:
            # Simulate move directly on the state reference to save memory overhead
            if move['type'] == 'pawn':
                old_pos = state.positions[self.player]
                state.positions[self.player] = move['pos']
                
                # Call centralized evaluate function with ai_type="medium"
                score = evaluate(state, self.player, ai_type="medium")
                
                state.positions[self.player] = old_pos
            else:
                r, c, ori = move['row'], move['col'], move['orientation']
                if ori == 'h': state.h_walls.add((r, c))
                else: state.v_walls.add((r, c))
                
                # Call centralized evaluate function with ai_type="medium"
                score = evaluate(state, self.player, ai_type="medium")
                
                # Remove wall to revert state
                if ori == 'h': state.h_walls.remove((r, c))
                else: state.v_walls.remove((r, c))

            # 3. Track the best options
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        return random.choice(best_moves) if best_moves else None