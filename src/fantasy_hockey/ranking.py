"""Ranking strategies for redraft analysis."""

from abc import ABC, abstractmethod
from enum import Enum

from fantasy_hockey.models import Player

# Default multiplier to de-prioritize goalies (they score more points naturally)
DEFAULT_GOALIE_MULTIPLIER = 0.75


class Position(Enum):
    """Simplified position categories for ranking."""

    FORWARD = "F"
    DEFENSE = "D"
    GOALIE = "G"

    @classmethod
    def from_espn_position(cls, position: str) -> "Position":
        """Convert ESPN position string to Position enum."""
        pos_lower = position.lower()
        if pos_lower == "goalie":
            return cls.GOALIE
        if pos_lower == "defense":
            return cls.DEFENSE
        # Center, Left Wing, Right Wing -> Forward
        return cls.FORWARD


class RankingStrategy(ABC):
    """Abstract base class for player ranking strategies."""

    @abstractmethod
    def rank(self, players: list[Player]) -> list[Player]:
        """Rank players and return them in order from best to worst.

        Args:
            players: List of players to rank.

        Returns:
            Players sorted from best (index 0) to worst.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this ranking strategy."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of how this ranking works."""
        pass


class TotalPointsRanker(RankingStrategy):
    """Rank players by total fantasy points scored this season.

    This is a naive ranking that simply orders by total points.
    It does not account for position scarcity, games played, etc.
    """

    def rank(self, players: list[Player]) -> list[Player]:
        return sorted(players, key=lambda p: p.total_points, reverse=True)

    @property
    def name(self) -> str:
        return "Total Points"

    @property
    def description(self) -> str:
        return "Players ranked by total fantasy points scored this season."


class PositionAdjustedRanker(RankingStrategy):
    """Rank players by total points with position adjustments.

    Applies a multiplier to goalie points to account for their naturally
    higher scoring rate, making comparisons with skaters more fair.
    """

    def __init__(self, goalie_multiplier: float = DEFAULT_GOALIE_MULTIPLIER):
        """Initialize the ranker.

        Args:
            goalie_multiplier: Multiplier applied to goalie points (default 0.75).
        """
        self.goalie_multiplier = goalie_multiplier

    def _adjusted_points(self, player: Player) -> float:
        """Get position-adjusted points for ranking."""
        if player.position.lower() == "goalie":
            return player.total_points * self.goalie_multiplier
        return player.total_points

    def rank(self, players: list[Player]) -> list[Player]:
        return sorted(players, key=self._adjusted_points, reverse=True)

    @property
    def name(self) -> str:
        return f"Position Adjusted (G x{self.goalie_multiplier})"

    @property
    def description(self) -> str:
        return (
            f"Players ranked by total fantasy points, with goalie points "
            f"multiplied by {self.goalie_multiplier} to account for their "
            f"naturally higher scoring rate."
        )


class ValueOverReplacementRanker(RankingStrategy):
    """Rank players by Value Over Replacement (VOR).

    VOR measures how much better a player is compared to a "replacement level"
    player at the same position. This normalizes value across positions since
    different positions have different scoring baselines.

    VOR = Player Points - Replacement Level Points (for their position)
    """

    # Default replacement level values (can be overridden or calculated)
    DEFAULT_REPLACEMENT_LEVELS = {
        Position.FORWARD: 46.1,
        Position.DEFENSE: 45.0,
        Position.GOALIE: 72.6,
    }

    def __init__(
        self,
        replacement_levels: dict[Position, float] | None = None,
    ):
        """Initialize the ranker.

        Args:
            replacement_levels: Dict mapping Position to replacement level points.
                               If None, uses default values.
        """
        self.replacement_levels = (
            replacement_levels or self.DEFAULT_REPLACEMENT_LEVELS.copy()
        )

    def _get_vor(self, player: Player) -> float:
        """Calculate Value Over Replacement for a player."""
        position = Position.from_espn_position(player.position)
        replacement = self.replacement_levels.get(position, 0.0)
        return player.total_points - replacement

    def rank(self, players: list[Player]) -> list[Player]:
        return sorted(players, key=self._get_vor, reverse=True)

    @property
    def name(self) -> str:
        return "Value Over Replacement (VOR)"

    @property
    def description(self) -> str:
        f_repl = self.replacement_levels[Position.FORWARD]
        d_repl = self.replacement_levels[Position.DEFENSE]
        g_repl = self.replacement_levels[Position.GOALIE]
        return (
            f"Players ranked by value over replacement level. "
            f"Replacement levels: F={f_repl:.0f}, D={d_repl:.0f}, G={g_repl:.0f}. "
            f"VOR = Player Points - Replacement Points for their position."
        )

    @classmethod
    def calculate_replacement_levels(
        cls,
        players: list[Player],
        num_teams: int = 12,
        roster_spots: dict[Position, int] | None = None,
    ) -> dict[Position, float]:
        """Calculate replacement levels based on player pool.

        The replacement level is typically defined as the best player available
        after all starters are drafted. This method calculates it based on
        roster construction.

        Args:
            players: All players in the draft pool.
            num_teams: Number of teams in the league.
            roster_spots: Number of starting spots per position per team.
                         Defaults to typical fantasy hockey roster.

        Returns:
            Dict mapping Position to replacement level points.
        """
        if roster_spots is None:
            # Typical fantasy hockey roster spots per team
            roster_spots = {
                Position.FORWARD: 9,  # C, C, LW, LW, RW, RW, F, F, F or similar
                Position.DEFENSE: 4,  # D, D, D, D
                Position.GOALIE: 2,  # G, G
            }

        # Group players by position
        by_position: dict[Position, list[Player]] = {
            Position.FORWARD: [],
            Position.DEFENSE: [],
            Position.GOALIE: [],
        }

        for player in players:
            pos = Position.from_espn_position(player.position)
            by_position[pos].append(player)

        # Sort each position by points
        for pos in by_position:
            by_position[pos].sort(key=lambda p: p.total_points, reverse=True)

        # Calculate replacement level for each position
        replacement_levels = {}
        for pos, pos_players in by_position.items():
            # Number of starters at this position across all teams
            starters_needed = num_teams * roster_spots.get(pos, 0)

            # Replacement level is the first non-starter (or last starter if not enough)
            if len(pos_players) > starters_needed:
                replacement_levels[pos] = pos_players[starters_needed].total_points
            elif pos_players:
                replacement_levels[pos] = pos_players[-1].total_points
            else:
                replacement_levels[pos] = 0.0

        return replacement_levels
