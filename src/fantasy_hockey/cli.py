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


def print_redraft(client: FantasyHockeyClient, rounds: int = DEFAULT_ROUNDS) -> None:
    """Print redraft comparison for specified rounds."""
    print("\nLoading data (this may take a moment)...")
    result = client.get_redraft(rounds=rounds)

    comparisons = result.comparisons
    ranked_players = result.ranked_players

    num_picks = len(comparisons)
    round_label = f"Round{'s 1-' + str(rounds) if rounds > 1 else ' 1'}"
    print(f"\nRedraft Analysis - {round_label}")
    print("Ranking uses position-adjusted points (goalies x0.75)")
    print("=" * 95)
    print(
        f"{'Pick':<6}{'Actual Pick':<26}{'Pos':<4}{'Pts':<8}"
        f"{'Redraft Pick':<26}{'Pos':<4}{'Pts':<8}"
    )
    print("-" * 95)

    for i, actual in enumerate(comparisons):
        # The ideal pick at this slot is the i-th ranked player
        ideal = ranked_players[i]
        actual_pos = get_position_abbrev(actual.player.position)
        ideal_pos = get_position_abbrev(ideal.position)
        print(
            f"{i + 1:<6}"
            f"{actual.player.player_name[:25]:<26}"
            f"{actual_pos:<4}"
            f"{actual.player.total_points:<8.1f}"
            f"{ideal.player_name[:25]:<26}"
            f"{ideal_pos:<4}"
            f"{ideal.total_points:<8.1f}"
        )

    print()

    # Summary stats - only for players actually picked in these rounds
    biggest_steals = sorted(comparisons, key=lambda c: c.pick_difference, reverse=True)[
        :5
    ]
    biggest_busts = sorted(comparisons, key=lambda c: c.pick_difference)[:5]

    print("Biggest Steals (outperformed draft position):")
    for comp in biggest_steals:
        if comp.pick_difference > 0:
            print(
                f"  {comp.player.player_name}: picked {comp.actual_pick}, "
                f"should have been {comp.redraft_pick} ({comp.pick_difference:+d})"
            )

    print("\nBiggest Busts (underperformed draft position):")
    for comp in biggest_busts:
        if comp.pick_difference < 0:
            print(
                f"  {comp.player.player_name}: picked {comp.actual_pick}, "
                f"should have been {comp.redraft_pick} ({comp.pick_difference:+d})"
            )

    print()


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


def main() -> int:
    """Main entry point for CLI."""
    try:
        client = FantasyHockeyClient()

        command = sys.argv[1] if len(sys.argv) > 1 else "redraft"
        rounds = parse_rounds_arg(sys.argv)

        match command:
            case "standings":
                print_standings(client)
            case "draft":
                print_draft_order(client, rounds=rounds)
            case "redraft":
                print_redraft(client, rounds=rounds or DEFAULT_ROUNDS)
            case _:
                print(f"Unknown command: {command}", file=sys.stderr)
                print("Available commands: standings, draft, redraft", file=sys.stderr)
                print("Options: --rounds N (limit to first N rounds)", file=sys.stderr)
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
