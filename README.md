# Fantasy Hockey CLI

A small pet project that wraps ESPN Fantasy Hockey data so you can inspect your league, review draft history, and instantly generate a redraft using different ranking strategies.

## Setup
1. Install dependencies with [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```
2. Create a `.env` file in the project root (or export these variables) so the CLI can authenticate against ESPN:
   ```env
   ESPN_LEAGUE_ID=<your_league_id>
   ESPN_SWID=<your_swid_cookie>
   ESPN_S2=<your_s2_cookie>
   ESPN_YEAR=2026        # optional, defaults to 2026
   ```

## Running with uv
Use uv to execute the CLI directly without activating the virtual environment:
```bash
uv run fantasy redraft --rounds 3 --strategy vor
```

## CLI Commands
- `fantasy standings` – Print the current ESPN league standings (rank, team name, record).
- `fantasy draft [--rounds N]` – Show the historical draft order, optionally limited to the first `N` rounds.
- `fantasy redraft [--rounds N] [--strategy vor|total|adjusted] [--format table|csv]` – Run a redraft analysis comparing the original picks with the recommended order; supports table or CSV output.

Each command can be invoked via `uv run fantasy <command>`.
