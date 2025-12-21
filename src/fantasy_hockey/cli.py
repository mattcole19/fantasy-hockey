"""Command-line interface for Fantasy Hockey."""

import sys

from fantasy_hockey.client import FantasyHockeyClient

DEFAULT_ROUNDS = 1


def print_standings(client: FantasyHockeyClient) -> None:
    """Print league standings."""
    standings = client.get_standings()

    print("\nFantasy Hockey League Standings")
    print("=" * 50)
    print(f"{'Rank':<6}{'Team':<30}{'Record':<12}")
    print("-" * 50)

    for team in standings:
        print(f"{team.standing:<6}{team.team_name[:29]:<30}{team.record:<12}")

    print()


def get_position_abbrev(position: str) -> str:
    """Get single-letter position abbreviation."""
    if not position:
        return "?"
    pos_lower = position.lower()
    if pos_lower == "goalie":
        return "G"
    if pos_lower == "defense":
        return "D"
    if pos_lower in ("center", "left wing", "right wing"):
        return "F"
    # Fallback to first letter
    return position[0].upper()


def print_draft_order(client: FantasyHockeyClient, rounds: int | None = None) -> None:
    """Print draft order."""
    picks = client.get_draft_order()

    if rounds is not None:
        picks = [p for p in picks if p.round_num <= rounds]

    if not picks:
        print("\nNo draft data available.")
        return

    title = f"Draft Order (Round{'s 1-' + str(rounds) if rounds and rounds > 1 else ' 1' if rounds == 1 else 's'})"
    print(f"\n{title}")
    print("=" * 85)
    print(f"{'Pick':<6}{'Player':<28}{'Pos':<5}{'Points':<10}{'Team':<35}")
    print("-" * 85)

    for pick in picks:
        pos = get_position_abbrev(pick.player.position)
        print(
            f"{pick.overall_pick:<6}"
            f"{pick.player.player_name[:27]:<28}"
            f"{pos:<5}"
            f"{pick.player.total_points:<10.1f}"
            f"{pick.team_name[:34]:<35}"
        )

    print()


def print_redraft(
    client: FantasyHockeyClient,
    rounds: int = DEFAULT_ROUNDS,
    strategy=None,
) -> None:
    """Print redraft comparison for specified rounds."""
    print("\nLoading data (this may take a moment)...")
    result = client.get_redraft(rounds=rounds, strategy=strategy)

    comparisons = result.comparisons
    ranked_players = result.ranked_players

    round_label = f"Round{'s 1-' + str(rounds) if rounds > 1 else ' 1'}"
    print(f"\n{'=' * 80}")
    print(f"REDRAFT ANALYSIS - {round_label}")
    print(f"{'=' * 80}")
    print(f"Algorithm: {result.strategy_name}")
    print(f"Description: {result.strategy_description}")
    print(f"{'=' * 80}\n")

    print(
        f"{'Pick':<5}{'Actual Pick':<21}{'Pos':<4}{'Pts':<7}{'Team':<22}"
        f"{'Redraft Pick':<21}{'Pos':<4}{'Pts':<7}"
    )
    print("-" * 91)

    for i, actual in enumerate(comparisons):
        # The ideal pick at this slot is the i-th ranked player
        ideal = ranked_players[i]
        actual_pos = get_position_abbrev(actual.player.position)
        ideal_pos = get_position_abbrev(ideal.position)
        team_short = actual.team_name[:21]
        print(
            f"{i + 1:<5}"
            f"{actual.player.player_name[:20]:<21}"
            f"{actual_pos:<4}"
            f"{actual.player.total_points:<7.1f}"
            f"{team_short:<22}"
            f"{ideal.player_name[:20]:<21}"
            f"{ideal_pos:<4}"
            f"{ideal.total_points:<7.1f}"
        )

    print()

    # Summary stats - only for players actually picked in these rounds
    biggest_steals = sorted(comparisons, key=lambda c: c.pick_difference, reverse=True)[
        :5
    ]
    biggest_busts = sorted(comparisons, key=lambda c: c.pick_difference)[:5]

    print("BIGGEST STEALS (outperformed draft position):")
    for comp in biggest_steals:
        if comp.pick_difference > 0:
            print(
                f"  {comp.player.player_name} ({comp.team_name}): "
                f"picked {comp.actual_pick}, should have been {comp.redraft_pick} "
                f"({comp.pick_difference:+d})"
            )

    print("\nBIGGEST BUSTS (underperformed draft position):")
    for comp in biggest_busts:
        if comp.pick_difference < 0:
            print(
                f"  {comp.player.player_name} ({comp.team_name}): "
                f"picked {comp.actual_pick}, should have been {comp.redraft_pick} "
                f"({comp.pick_difference:+d})"
            )

    print()


def print_redraft_csv(
    client: FantasyHockeyClient,
    rounds: int = DEFAULT_ROUNDS,
    strategy=None,
) -> None:
    """Print redraft comparison as CSV."""
    result = client.get_redraft(rounds=rounds, strategy=strategy)
    comparisons = result.comparisons
    ranked_players = result.ranked_players

    print("Pick,Actual Player,Pos,Pts,Team,Redraft Player,Pos,Pts,Diff")
    for i, actual in enumerate(comparisons):
        ideal = ranked_players[i]
        actual_pos = get_position_abbrev(actual.player.position)
        ideal_pos = get_position_abbrev(ideal.position)
        diff = actual.pick_difference
        # Escape commas in names
        actual_name = actual.player.player_name.replace(",", "")
        ideal_name = ideal.player_name.replace(",", "")
        team = actual.team_name.replace(",", "")
        print(
            f"{i + 1},{actual_name},{actual_pos},{actual.player.total_points:.1f},"
            f"{team},{ideal_name},{ideal_pos},{ideal.total_points:.1f},{diff:+d}"
        )


def parse_rounds_arg(args: list[str]) -> int | None:
    """Parse --rounds N from command line args."""
    for i, arg in enumerate(args):
        if arg == "--rounds" and i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                return None
        if arg.startswith("--rounds="):
            try:
                return int(arg.split("=")[1])
            except ValueError:
                return None
    return None


def parse_format_arg(args: list[str]) -> str:
    """Parse --format from command line args."""
    for i, arg in enumerate(args):
        if arg == "--format" and i + 1 < len(args):
            return args[i + 1].lower()
        if arg.startswith("--format="):
            return arg.split("=")[1].lower()
    return "table"


def parse_strategy_arg(args: list[str]) -> str:
    """Parse --strategy from command line args."""
    for i, arg in enumerate(args):
        if arg == "--strategy" and i + 1 < len(args):
            return args[i + 1].lower()
        if arg.startswith("--strategy="):
            return arg.split("=")[1].lower()
    return "vor"  # Default to VOR


def get_strategy(strategy_name: str):
    """Get ranking strategy by name."""
    from fantasy_hockey.ranking import (
        PositionAdjustedRanker,
        TotalPointsRanker,
        ValueOverReplacementRanker,
    )

    strategies = {
        "vor": ValueOverReplacementRanker,
        "total": TotalPointsRanker,
        "adjusted": PositionAdjustedRanker,
    }

    strategy_class = strategies.get(strategy_name)
    if strategy_class is None:
        return None
    return strategy_class()


def main() -> int:
    """Main entry point for CLI."""
    try:
        client = FantasyHockeyClient()

        command = sys.argv[1] if len(sys.argv) > 1 else "redraft"
        rounds = parse_rounds_arg(sys.argv)
        fmt = parse_format_arg(sys.argv)
        strategy_name = parse_strategy_arg(sys.argv)

        match command:
            case "standings":
                print_standings(client)
            case "draft":
                print_draft_order(client, rounds=rounds)
            case "redraft":
                strategy = get_strategy(strategy_name)
                if strategy is None:
                    print(f"Unknown strategy: {strategy_name}", file=sys.stderr)
                    print("Available strategies: vor, total, adjusted", file=sys.stderr)
                    return 1

                if fmt == "csv":
                    print_redraft_csv(
                        client, rounds=rounds or DEFAULT_ROUNDS, strategy=strategy
                    )
                else:
                    print_redraft(
                        client, rounds=rounds or DEFAULT_ROUNDS, strategy=strategy
                    )
            case _:
                print(f"Unknown command: {command}", file=sys.stderr)
                print("Available commands: standings, draft, redraft", file=sys.stderr)
                print("Options:", file=sys.stderr)
                print("  --rounds N        Limit to first N rounds", file=sys.stderr)
                print(
                    "  --format csv      Output as CSV (for Google Sheets)",
                    file=sys.stderr,
                )
                print(
                    "  --strategy NAME   Ranking strategy: vor, total, adjusted",
                    file=sys.stderr,
                )
                return 1

        return 0

    except KeyError as e:
        print(f"Error: Missing environment variable {e}", file=sys.stderr)
        print(
            "Make sure .env contains ESPN_LEAGUE_ID, ESPN_SWID, and ESPN_S2",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
