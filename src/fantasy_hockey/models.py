"""Pydantic models for Fantasy Hockey data."""

from pydantic import BaseModel, Field


class TeamStanding(BaseModel):
    """A team's standing in the fantasy league."""

    team_id: int = Field(description="Team ID")
    team_name: str = Field(description="Team name")
    owner: str = Field(description="Team owner name")
    wins: int = Field(description="Number of wins")
    losses: int = Field(description="Number of losses")
    ties: int = Field(description="Number of ties")
    standing: int = Field(description="Current standing/rank")

    @property
    def record(self) -> str:
        """Return formatted W-L-T record."""
        return f"{self.wins}-{self.losses}-{self.ties}"


class Player(BaseModel):
    """A player in the fantasy league."""

    player_id: int = Field(description="Player ID")
    player_name: str = Field(description="Player name")
    position: str = Field(default="", description="Player position")
    total_points: float = Field(
        default=0.0, description="Total fantasy points this season"
    )


class DraftPick(BaseModel):
    """A draft pick in the draft order."""

    round_num: int = Field(description="Round number")
    pick_num: int = Field(description="Pick number within the round")
    overall_pick: int = Field(description="Overall pick number")
    team_id: int = Field(description="Team ID making the pick")
    team_name: str = Field(description="Team name making the pick")
    player: Player


class RedraftComparison(BaseModel):
    """Comparison between actual draft pick and ideal redraft position."""

    actual_pick: int = Field(description="Actual overall draft position")
    redraft_pick: int = Field(description="Ideal redraft position based on performance")
    player: Player
    team_name: str = Field(description="Team that drafted this player")

    @property
    def pick_difference(self) -> int:
        """Positive = drafted too early, negative = drafted too late (steal)."""
        return self.actual_pick - self.redraft_pick


class RedraftResult(BaseModel):
    """Result of a redraft analysis."""

    comparisons: list[RedraftComparison] = Field(
        description="Comparison for each actual draft pick"
    )
    ranked_players: list[Player] = Field(
        description="All players ranked by the strategy (best first)"
    )
