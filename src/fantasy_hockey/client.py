"""ESPN Fantasy Hockey API client wrapper."""

from collections import defaultdict

from espn_api.hockey import League

from fantasy_hockey.config import ESPNConfig, load_config
from fantasy_hockey.models import (
    DraftPick,
    Player,
    RedraftComparison,
    RedraftResult,
    TeamStanding,
)
from fantasy_hockey.ranking import PositionAdjustedRanker, RankingStrategy


class FantasyHockeyClient:
    """Client for accessing ESPN Fantasy Hockey data."""

    def __init__(self, config: ESPNConfig | None = None):
        """Initialize the client.

        Args:
            config: ESPN configuration. If None, loads from environment.
        """
        self.config = config or load_config()
        self._league: League | None = None
        self._player_points_cache: dict[int, float] | None = None
        self._player_positions_cache: dict[int, str] | None = None

    @property
    def league(self) -> League:
        """Get the ESPN League instance, creating it if needed."""
        if self._league is None:
            self._league = League(
                league_id=self.config.league_id,
                espn_s2=self.config.espn_s2,
                swid=self.config.swid,
                year=self.config.year,
            )
        return self._league

    def get_standings(self) -> list[TeamStanding]:
        """Get current league standings.

        Returns:
            List of team standings sorted by rank.
        """
        standings = []
        for team in self.league.teams:
            standing = TeamStanding(
                team_id=team.team_id,
                team_name=team.team_name,
                owner=team.owner,
                wins=team.wins,
                losses=team.losses,
                ties=team.ties,
                standing=team.standing,
            )
            standings.append(standing)

        return sorted(standings, key=lambda t: t.standing)

    def get_draft_order(self) -> list[DraftPick]:
        """Get the draft order for the league.

        Returns:
            List of draft picks in order.
        """
        team_lookup = {team.team_id: team.team_name for team in self.league.teams}
        player_points = self._get_player_points()
        player_positions = self._get_player_positions()

        picks = []
        for i, pick in enumerate(self.league.draft):
            player_picked = Player(
                player_id=pick.playerId,
                player_name=pick.playerName,
                position=player_positions.get(pick.playerId, ""),
                total_points=player_points.get(pick.playerId, 0.0),
            )
            overall = i + 1
            draft_pick = DraftPick(
                round_num=pick.round_num,
                pick_num=pick.round_pick,
                overall_pick=overall,
                team_id=pick.team.team_id,
                team_name=team_lookup.get(pick.team.team_id, "Unknown"),
                player=player_picked,
            )
            picks.append(draft_pick)

        return picks

    def get_redraft(
        self,
        strategy: RankingStrategy | None = None,
        rounds: int | None = None,
    ) -> RedraftResult:
        """Compare actual draft to ideal redraft based on current performance.

        Args:
            strategy: Ranking strategy to use. Defaults to PositionAdjustedRanker.
            rounds: Limit output to first N rounds. Ranking considers ALL players.

        Returns:
            RedraftResult with comparisons and ranked player list.
        """
        if strategy is None:
            strategy = PositionAdjustedRanker()

        all_picks = self.get_draft_order()

        # Rank ALL players to get true redraft positions
        all_players = [pick.player for pick in all_picks]
        ranked_players = strategy.rank(all_players)

        # Build redraft position lookup from ALL players
        redraft_position = {p.player_id: i + 1 for i, p in enumerate(ranked_players)}

        # Filter to requested rounds for output
        display_picks = all_picks
        if rounds is not None:
            display_picks = [p for p in all_picks if p.round_num <= rounds]

        # Build comparison for each actual draft pick
        comparisons = []
        for pick in display_picks:
            comparison = RedraftComparison(
                actual_pick=pick.overall_pick,
                redraft_pick=redraft_position[pick.player.player_id],
                player=pick.player,
                team_name=pick.team_name,
            )
            comparisons.append(comparison)

        return RedraftResult(comparisons=comparisons, ranked_players=ranked_players)

    def _get_player_points(self) -> dict[int, float]:
        """Get total fantasy points for all players across the season.

        Returns:
            Dict mapping player_id to total fantasy points.
        """
        if self._player_points_cache is not None:
            return self._player_points_cache

        player_points: dict[int, float] = defaultdict(float)
        player_positions: dict[int, str] = {}
        current_period = self.league.currentMatchupPeriod

        for period in range(1, current_period + 1):
            scores = self.league.box_scores(matchup_period=period)
            for score in scores:
                for player in score.home_lineup + score.away_lineup:
                    if player.points:
                        player_points[player.playerId] += player.points
                    if player.playerId not in player_positions:
                        player_positions[player.playerId] = player.position

        self._player_points_cache = dict(player_points)
        # Also cache positions from box scores
        if self._player_positions_cache is None:
            self._player_positions_cache = player_positions
        else:
            self._player_positions_cache.update(player_positions)

        return self._player_points_cache

    def _get_player_positions(self) -> dict[int, str]:
        """Get player positions from roster and box score data.

        Returns:
            Dict mapping player_id to position string.
        """
        if self._player_positions_cache is not None:
            return self._player_positions_cache

        positions: dict[int, str] = {}

        # Get from current rosters
        for team in self.league.teams:
            for player in team.roster:
                positions[player.playerId] = player.position

        self._player_positions_cache = positions

        # Calling _get_player_points will also populate positions from box scores
        self._get_player_points()

        return self._player_positions_cache
