"""
Quoridor Core Game Logic
- Board state management
- Move validation
- Wall placement validation (BFS path check)
- Win detection
"""

from collections import deque
from utils.constants import BOARD_SIZE, WALLS_PER_PLAYER


class GameState:
    """Complete game state for Quoridor."""

    def __init__(self):
        self.reset()

    def reset(self):
        # Player positions: (row, col) 0-indexed
        # Player 1 starts at row 8 (bottom center), goal is row 0
        # Player 2 starts at row 0 (top center),   goal is row 8
        self.positions = {
            1: (8, 4),
            2: (0, 4),
        }
        self.walls_left = {1: WALLS_PER_PLAYER, 2: WALLS_PER_PLAYER}
        # Horizontal walls: set of (r, c) meaning wall below row r between col c and c+1
        # Wall covers edge between (r,c)-(r+1,c) and (r,c+1)-(r+1,c+1)
        self.h_walls = set()   # (r, c): top-left corner of the wall pair
        # Vertical walls: set of (r, c) meaning wall right of col c between row r and r+1
        self.v_walls = set()   # (r, c)
        self.current_player = 1
        self.winner = None
        self.move_history = []  # list of (type, data) for undo

    # ------------------------------------------------------------------ #
    #  Adjacency / Movement
    # ------------------------------------------------------------------ #

    def is_wall_between_h(self, r1, c1, r2, c2):
        top_row = min(r1, r2)
        # A wall at (top_row, c1) blocks movement
        # A wall at (top_row, c1-1) also blocks movement because walls are 2 units wide
        return (top_row, c1) in self.h_walls or (top_row, c1 - 1) in self.h_walls
    def is_wall_between_v(self, r1, c1, r2, c2):
        """
        Check if vertical wall blocks horizontal movement.
        A wall at (r1, left) or (r1-1, left) blocks the path.
        """
        left = min(c1, c2)
        return (
            (r1, left) in self.v_walls or 
            (r1 - 1, left) in self.v_walls
        )
    def can_move(self, r1, c1, r2, c2):
        """Check if a single-step orthogonal move is physically possible (walls only)."""
        if r2 == r1 + 1 or r2 == r1 - 1:
            return not self.is_wall_between_h(r1, c1, r2, c2)
        if c2 == c1 + 1 or c2 == c1 - 1:
            return not self.is_wall_between_v(r1, c1, r2, c2)
        return False

    def neighbors(self, r, c):
        """Return all cells directly reachable from (r,c) ignoring pawns."""
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if self.can_move(r, c, nr, nc):
                    result.append((nr, nc))
        return result

    def get_valid_pawn_moves(self, player=None):
        """Return all valid destination squares for the given player's pawn."""
        if player is None:
            player = self.current_player
            
        r, c = self.positions[player]
        opp = 2 if player == 1 else 1
        opp_pos = self.positions[opp]
        moves = []

        # Iterate through the 4 orthogonal directions
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            # 1. BOUNDARY CHECK: Is the adjacent square on the board?
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                continue
            
            # 2. WALL CHECK: Is there a wall between my current pos and the neighbor?
            # This is what fixes the issue in your image! 
            if not self.can_move(r, c, nr, nc):
                continue
            
            # 3. OCCUPANCY CHECK: Is the opponent standing there?
            if (nr, nc) == opp_pos:
                # JUMP LOGIC: Try to jump over the opponent
                jnr, jnc = nr + dr, nc + dc
                
                # Can we jump straight over? (Check board edge and walls)
                if (0 <= jnr < BOARD_SIZE and 0 <= jnc < BOARD_SIZE 
                        and self.can_move(nr, nc, jnr, jnc)):
                    moves.append((jnr, jnc))
                else:
                    # DIAGONAL LOGIC: Straight jump is blocked by wall or edge.
                    # Now we check the two possible diagonal squares relative to the opponent.
                    for ddr, ddc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        # We only care about the 2 directions perpendicular to our approach
                        if (ddr, ddc) == (dr, dc) or (ddr, ddc) == (-dr, -dc):
                            continue
                            
                        dnr, dnc = nr + ddr, nc + ddc
                        # Can we move from the OPPONENT'S square to the diagonal square?
                        if (0 <= dnr < BOARD_SIZE and 0 <= dnc < BOARD_SIZE 
                                and self.can_move(nr, nc, dnr, dnc)):
                            moves.append((dnr, dnc))
            else:
                # NO OPPONENT: The square is empty and not blocked by a wall.
                moves.append((nr, nc))
                
        # Remove duplicates and return
        return list(set(moves))
    # ------------------------------------------------------------------ #
    #  Wall Validation
    # ------------------------------------------------------------------ #

    def is_valid_wall(self, orientation, r, c):
        # 1. Check if player has walls remaining
        if self.walls_left[self.current_player] <= 0:
            return False

        # 2. Check if within board boundaries 
        # (Wall at r,c covers r,c and r+1,c or c+1,c; so max index is BOARD_SIZE - 2)
        if not (0 <= r < BOARD_SIZE - 1 and 0 <= c < BOARD_SIZE - 1):
            return False

        if orientation == 'h':
            # --- Horizontal Wall Overlap Checks ---
            
            # Exact overlap: already a wall at (r, c)
            if (r, c) in self.h_walls:
                return False

            # Partial overlap (Left): A wall starting one unit to the left
            if (r, c - 1) in self.h_walls:
                return False

            # Partial overlap (Right): A wall starting one unit to the right
            if (r, c + 1) in self.h_walls:
                return False

            # Crossing: Vertical wall at same intersection blocks horizontal
            if (r, c) in self.v_walls:
                return False

            # BFS Path check (Temporary placement)
            self.h_walls.add((r, c))
            valid = self._both_have_path()
            self.h_walls.remove((r, c))
            return valid

        elif orientation == 'v':
            # --- Vertical Wall Overlap Checks ---
            
            # Exact overlap: already a wall at (r, c)
            if (r, c) in self.v_walls:
                return False

            # Partial overlap (Above): A wall starting one unit up
            if (r - 1, c) in self.v_walls:
                return False

            # Partial overlap (Below): A wall starting one unit down
            if (r + 1, c) in self.v_walls:
                return False

            # Crossing: Horizontal wall at same intersection blocks vertical
            if (r, c) in self.h_walls:
                return False

            # BFS Path check (Temporary placement)
            self.v_walls.add((r, c))
            valid = self._both_have_path()
            self.v_walls.remove((r, c))
            return valid

        return False
    def _both_have_path(self):
        return self._has_path(1) and self._has_path(2)

    def _has_path(self, player):
        """BFS check if player can reach their goal row."""
        goal_row = 0 if player == 1 else BOARD_SIZE - 1
        start = self.positions[player]
        visited = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            if r == goal_row:
                return True
            for nr, nc in self.neighbors(r, c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

    def shortest_path_length(self, player):
        """Return BFS shortest path length to goal for player (for AI heuristic)."""
        goal_row = 0 if player == 1 else BOARD_SIZE - 1
        start = self.positions[player]
        visited = {start}
        queue = deque([(start, 0)])
        while queue:
            (r, c), dist = queue.popleft()
            if r == goal_row:
                return dist
            for nr, nc in self.neighbors(r, c):
                if (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist + 1))
        return float('inf')

    # ------------------------------------------------------------------ #
    #  Apply Moves
    # ------------------------------------------------------------------ #

    def move_pawn(self, r, c):
        """Move current player's pawn to (r, c). Returns True if ok."""
        valid = self.get_valid_pawn_moves()
        if (r, c) not in valid:
            return False
        old_pos = self.positions[self.current_player]
        self.move_history.append(('pawn', self.current_player, old_pos))
        self.positions[self.current_player] = (r, c)
        self._check_win()
        if not self.winner:
            self._switch_player()
        return True

    def place_wall(self, orientation, r, c):
        """Place wall for current player. Returns True if ok."""
        if not self.is_valid_wall(orientation, r, c):
            return False
        self.move_history.append(('wall', self.current_player, orientation, r, c))
        if orientation == 'h':
            self.h_walls.add((r, c))
        else:
            self.v_walls.add((r, c))
        self.walls_left[self.current_player] -= 1
        self._switch_player()
        return True

    def undo(self):
        """Undo the last move."""
        if not self.move_history:
            return False
        last = self.move_history.pop()
        self.winner = None
        if last[0] == 'pawn':
            _, player, old_pos = last
            self.positions[player] = old_pos
            self.current_player = player
        elif last[0] == 'wall':
            _, player, orientation, r, c = last
            if orientation == 'h':
                self.h_walls.discard((r, c))
            else:
                self.v_walls.discard((r, c))
            self.walls_left[player] += 1
            self.current_player = player
        return True

    def _switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def _check_win(self):
        r1, _ = self.positions[1]
        r2, _ = self.positions[2]
        if r1 == 0:
            self.winner = 1
        elif r2 == BOARD_SIZE - 1:
            self.winner = 2

    # ------------------------------------------------------------------ #
    #  Serialization for save/load
    # ------------------------------------------------------------------ #

    def to_dict(self):
        return {
            'positions': {str(k): list(v) for k, v in self.positions.items()},
            'walls_left': {str(k): v for k, v in self.walls_left.items()},
            'h_walls': [list(w) for w in self.h_walls],
            'v_walls': [list(w) for w in self.v_walls],
            'current_player': self.current_player,
            'winner': self.winner,
        }

    def from_dict(self, d):
        self.positions = {int(k): tuple(v) for k, v in d['positions'].items()}
        self.walls_left = {int(k): v for k, v in d['walls_left'].items()}
        self.h_walls = set(tuple(w) for w in d['h_walls'])
        self.v_walls = set(tuple(w) for w in d['v_walls'])
        self.current_player = d['current_player']
        self.winner = d['winner']
        self.move_history = []
