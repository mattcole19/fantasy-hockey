"""Ranking strategies for redraft analysis."""

from abc import ABC, abstractmethod

from fantasy_hockey.models import Player

# Default multiplier to de-prioritize goalies (they score more points naturally)
DEFAULT_GOALIE_MULTIPLIER = 0.75


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
