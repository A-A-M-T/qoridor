# game/algorithms.py
import copy
import random
from collections import deque
from utils.constants import BOARD_SIZE

# ------------------------------------------------
# PATHFINDING (BFS)
# ------------------------------------------------
def get_shortest_path_distance(state, player): 
    goal_row = 0 if player == 1 else BOARD_SIZE - 1
    start = state.positions[player]
    visited = {start}
    queue = deque([(start, 0)])
    
    while queue:
        (r, c), dist = queue.popleft()
        if r == goal_row:
            return dist
            
        # Uses the neighbors() method from GameState to respect walls
        for nr, nc in state.neighbors(r, c):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append(((nr, nc), dist + 1))
    return float('inf')

# ------------------------------------------------
# CENTRALIZED EVALUATION FUNCTION
# ------------------------------------------------
def evaluate(state, player, ai_type):
    """
    Heuristic to score the board state.
    Positive = Good for AI, Negative = Good for Opponent.
    """
    opponent = 2 if player == 1 else 1

    my_dist = get_shortest_path_distance(state, player)
    opp_dist = get_shortest_path_distance(state, opponent)

    # --- MEDIUM AI SPECIFIC EVALUATION ---
    if ai_type == "medium":
        if my_dist == float('inf'): return -999
        if opp_dist == float('inf'): return 999
        return opp_dist - my_dist

    # --- HARD AI SPECIFIC EVALUATION ---
    # Terminal state checks
    if my_dist == float("inf"): return -99999
    if opp_dist == float("inf"): return 99999

    # Mobility: How many squares can the player move to?
    my_moves = len(state.get_valid_pawn_moves(player))
    opp_moves = len(state.get_valid_pawn_moves(opponent))

    # Wall advantage
    wall_adv = state.walls_left[player] - state.walls_left[opponent]
    
    return (
        (opp_dist - my_dist) * 20 +  # Priority 1: Distance gap
        (my_moves - opp_moves) * 4 + # Priority 2: Mobility
        wall_adv * 4                 # Priority 3: Wall count
    )

# ------------------------------------------------
# MOVE GENERATION
# ------------------------------------------------
def get_all_moves(state, player):
    """Generates all possible pawn moves and a subset of the best wall moves."""
    opponent = 2 if player == 1 else 1
    moves = []

    # 1. All valid pawn moves
    for pos in state.get_valid_pawn_moves(player):
        moves.append({"type": "pawn", "pos": pos})

    # 2. Strategic wall moves
    if state.walls_left[player] > 0:
        scored_walls = []
        for r in range(BOARD_SIZE - 1):
            for c in range(BOARD_SIZE - 1):
                for ori in ("h", "v"):
                    if state.is_valid_wall(ori, r, c):
                        before = get_shortest_path_distance(state, opponent)
                        
                        if ori == "h": state.h_walls.add((r, c))
                        else: state.v_walls.add((r, c))
                        
                        after = get_shortest_path_distance(state, opponent)
                        
                        if ori == "h": state.h_walls.remove((r, c))
                        else: state.v_walls.remove((r, c))

                        impact = after - before
                        if impact >= 0:
                            scored_walls.append((impact, 
                                {"type": "wall", "orientation": ori, "row": r, "col": c}))

        scored_walls.sort(reverse=True, key=lambda x: x[0])
        for _, wall in scored_walls[:15]:
            moves.append(wall)

    return moves

# ------------------------------------------------
# CENTRALIZED EASY AI ALGORITHM
# ------------------------------------------------
def _get_internal_smart_wall(state, player, opponent):
    """Finds a wall that actually helps block the opponent (used for Easy AI)."""
    if state.walls_left[player] <= 0:
        return None
        
    curr_opp_dist = get_shortest_path_distance(state, opponent)
    wall_candidates = []

    for _ in range(25):
        r = random.randint(0, 7)
        c = random.randint(0, 7)
        for ori in ["h", "v"]:
            if state.is_valid_wall(ori, r, c):
                if ori == 'h': state.h_walls.add((r, c))
                else: state.v_walls.add((r, c))
                
                new_dist = get_shortest_path_distance(state, opponent)
                
                if ori == 'h': state.h_walls.remove((r, c))
                else: state.v_walls.remove((r, c))
                
                if new_dist > curr_opp_dist:
                    wall_candidates.append({"type": "wall", "orientation": ori, "row": r, "col": c})
    
    return random.choice(wall_candidates) if wall_candidates else None

def easy_get_move(state, player, last_pos):
    """Centralized move selector for Easy AI difficulty level."""
    opponent = 2 if player == 1 else 1
    pawn_moves = state.get_valid_pawn_moves(player)
    
    if not pawn_moves:
        return None, last_pos

    # 1. CALCULATE BEST PAWN MOVE (Shortest Path)
    move_scores = []
    original_pos = state.positions[player]
    
    for pos in pawn_moves:
        state.positions[player] = pos
        dist = get_shortest_path_distance(state, player)
        score = dist + (2 if pos == last_pos else 0)
        move_scores.append((score, pos))
        
    state.positions[player] = original_pos 
    move_scores.sort(key=lambda x: x[0])
    best_pawn_move = move_scores[0][1]

    # 2. DECISION POLICY (78% / 21% / 1%)
    r = random.random()

    # --- 78% CHANCE: SHORTEST PATH ---
    if r < 0.78:
        new_last_pos = state.positions[player]
        return {"type": "pawn", "pos": best_pawn_move}, new_last_pos
    
    # --- 21% CHANCE: SMART WALL INTERRUPTION ---
    elif r < 0.99:
        wall = _get_internal_smart_wall(state, player, opponent)
        new_last_pos = state.positions[player]
        if wall:
            return wall, new_last_pos
        return {"type": "pawn", "pos": best_pawn_move}, new_last_pos

    # --- 1% CHANCE: RANDOM MISTAKE ---
    else:
        new_last_pos = state.positions[player]
        return {"type": "pawn", "pos": random.choice(pawn_moves)}, new_last_pos

# ------------------------------------------------
# MINIMAX WITH ALPHA-BETA PRUNING
# ------------------------------------------------
def apply_move(state, move, player):
    """Creates a new state with the move applied."""
    temp_state = copy.deepcopy(state)
    temp_state.current_player = player
    if move["type"] == "pawn":
        temp_state.move_pawn(move["pos"][0], move["pos"][1])
    else:
        temp_state.place_wall(move["orientation"], move["row"], move["col"])
    return temp_state

def minimax(state, depth, alpha, beta, maximizing, player, tt):
    """Standard Minimax algorithm with Transposition Table."""
    opponent = 2 if player == 1 else 1
    
    key = (tuple(state.positions.items()), tuple(state.h_walls), tuple(state.v_walls), depth, maximizing)
    if key in tt:
        return tt[key]

    if state.winner == player: return 10000 + depth
    if state.winner == opponent: return -10000 - depth
    
    if depth == 0: return evaluate(state, player, "hard")

    curr_p = player if maximizing else opponent
    moves = get_all_moves(state, curr_p)

    if maximizing:
        best = float("-inf")
        for move in moves:
            ns = apply_move(state, move, curr_p)
            score = minimax(ns, depth - 1, alpha, beta, False, player, tt)
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha: break
        tt[key] = best
        return best
    else:
        best = float("inf")
        for move in moves:
            ns = apply_move(state, move, curr_p)
            score = minimax(ns, depth - 1, alpha, beta, True, player, tt)
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha: break
        tt[key] = best
        return best