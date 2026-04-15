import json
from dataclasses import dataclass, field
from typing import Optional, Dict

import pandas as pd
from openai import OpenAI


@dataclass
class LeagueSettings:
    league_format: str = "points_leader"   # "points_leader" or "head_to_head"
    league_size: int = 8
    salary_cap: Optional[int] = None
    weekly_reset: bool = True
    lineup_slots: Dict[str, int] = field(default_factory=lambda: {
        "Attack": 2,
        "Midfield": 2,
        "Faceoff": 1,
        "Defense": 1,
        "Goalie": 1
    })
    scoring: Dict[str, float] = field(default_factory=lambda: {
        "goal_1pt": 10,
        "goal_2pt": 20,
        "assist": 10,
        "ground_ball": 1,
        "caused_turnover": 10,
        "turnover": -3,
        "goal_against_1pt": -1,
        "goal_against_2pt": -2,
        "save": 3,
        "faceoff_won": 0.8,
        "faceoff_lost": -0.5,
        "bonus_3plus_goals": 5,
        "bonus_3plus_assists": 5,
        "bonus_15plus_saves": 5,
    })

    def __post_init__(self):
        if self.league_format not in {"points_leader", "head_to_head"}:
            raise ValueError("league_format must be 'points_leader' or 'head_to_head'")

        if self.league_format == "head_to_head" and not 4 <= self.league_size <= 12:
            raise ValueError("PLL head-to-head leagues require 4 to 12 members")


class FantasyAssistant:
    """
    A lightweight PLL fantasy question-answering helper.

    This class:
    1. Loads 2025 PLL player data from 3 CSV files
    2. Normalizes and scores the data
    3. Formats player context for the model
    4. Sends the question to the OpenAI Responses API
    5. Returns a clean answer
    """

    def __init__(self, api_key: str, model: str = "gpt-5.4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.df = pd.DataFrame()

    def load_data(self) -> pd.DataFrame:
        """
        Load all 2025 PLL player data from:
        - regular season
        - postseason
        - champ series
        """
        regular = pd.read_csv("pll-player-stats-regular.csv")
        regular["Stage"] = "Regular Season"
        regular["Year"] = 2025

        post = pd.read_csv("pll-player-stats-post.csv")
        post["Stage"] = "Postseason"
        post["Year"] = 2025

        champ = pd.read_csv("pll-player-stats-champ.csv")
        champ["Stage"] = "Champ Series"
        champ["Year"] = 2025

        self.df = pd.concat([regular, post, champ], ignore_index=True)
        self.df.columns = [col.strip() for col in self.df.columns]

        # builds a full player name
        if "First Name" in self.df.columns and "Last Name" in self.df.columns:
            self.df["Player"] = (
                self.df["First Name"].fillna("").astype(str).str.strip()
                + " "
                + self.df["Last Name"].fillna("").astype(str).str.strip()
            ).str.strip()

        return self.df

    def _normalize_dataframe(self, league_settings: LeagueSettings) -> pd.DataFrame:
        """
        Standardize PLL column names and compute a rough fantasy score.
        """
        if self.df.empty:
            raise ValueError("No data loaded. Call load_data() first.")

        df = self.df.copy()

        rename_map = {
            "player": "Player",
            "firstname": "First Name",
            "lastname": "Last Name",
            "position": "Position",
            "team": "Team",
            "gamesplayed": "GamesPlayed",
            "points": "Points",
            "scoringpoints": "ScoringPoints",
            "goals": "Goals",
            "onepointgoals": "OnePointGoals",
            "twopointgoals": "TwoPointGoals",
            "assists": "Assists",
            "shots": "Shots",
            "shotsongoal": "ShotsOnGoal",
            "turnovers": "Turnovers",
            "causedturnovers": "CausedTurnovers",
            "groundballs": "GroundBalls",
            "faceoffswon": "FaceoffsWon",
            "faceoffslost": "FaceoffsLost",
            "faceoffs": "Faceoffs",
            "faceoffpct": "FaceoffPct",
            "saves": "Saves",
            "savepct": "SavePct",
            "scoresagainst": "ScoresAgainst",
            "twopointgoalsagainst": "TwoPointGoalsAgainst",
            "stage": "Stage",
            "year": "Year",
        }

        corrected_columns = {}
        for col in df.columns:
            key = col.lower().replace(" ", "").replace("_", "")
            if key in rename_map:
                corrected_columns[col] = rename_map[key]

        df = df.rename(columns=corrected_columns)

        # Build Player if needed
        if "Player" not in df.columns and "First Name" in df.columns and "Last Name" in df.columns:
            df["Player"] = (
                df["First Name"].fillna("").astype(str).str.strip()
                + " "
                + df["Last Name"].fillna("").astype(str).str.strip()
            ).str.strip()

        defaults = {
            "Player": "",
            "Position": "",
            "Team": "",
            "GamesPlayed": 0,
            "Points": 0,
            "ScoringPoints": 0,
            "Goals": 0,
            "OnePointGoals": 0,
            "TwoPointGoals": 0,
            "Assists": 0,
            "Shots": 0,
            "ShotsOnGoal": 0,
            "Turnovers": 0,
            "CausedTurnovers": 0,
            "GroundBalls": 0,
            "FaceoffsWon": 0,
            "FaceoffsLost": 0,
            "Faceoffs": 0,
            "Saves": 0,
            "ScoresAgainst": 0,
            "TwoPointGoalsAgainst": 0,
            "Stage": "",
            "Year": 2025,
        }

        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default

        numeric_cols = [
            "GamesPlayed", "Points", "ScoringPoints", "Goals", "OnePointGoals",
            "TwoPointGoals", "Assists", "Shots", "ShotsOnGoal", "Turnovers",
            "CausedTurnovers", "GroundBalls", "FaceoffsWon", "FaceoffsLost",
            "Faceoffs", "Saves", "ScoresAgainst", "TwoPointGoalsAgainst", "Year"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        for col in ["Player", "Position", "Team", "Stage"]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        scoring = league_settings.scoring

        # Estimate fantasy points from raw stats
        df["ProjectedPoints"] = (
            df["OnePointGoals"] * scoring["goal_1pt"]
            + df["TwoPointGoals"] * scoring["goal_2pt"]
            + df["Assists"] * scoring["assist"]
            + df["GroundBalls"] * scoring["ground_ball"]
            + df["CausedTurnovers"] * scoring["caused_turnover"]
            + df["Turnovers"] * scoring["turnover"]
            + df["Saves"] * scoring["save"]
            + df["FaceoffsWon"] * scoring["faceoff_won"]
            + df["FaceoffsLost"] * scoring["faceoff_lost"]
            + (df["ScoresAgainst"] - df["TwoPointGoalsAgainst"]) * scoring["goal_against_1pt"]
            + df["TwoPointGoalsAgainst"] * scoring["goal_against_2pt"]
        )

        # Basic bonuses
        df["ProjectedPoints"] += (df["Goals"] >= 3).astype(int) * scoring["bonus_3plus_goals"]
        df["ProjectedPoints"] += (df["Assists"] >= 3).astype(int) * scoring["bonus_3plus_assists"]
        df["ProjectedPoints"] += (df["Saves"] >= 15).astype(int) * scoring["bonus_15plus_saves"]

        # Stage weighting for fantasy relevance
        stage_weights = {
            "Regular Season": 1.0,
            "Postseason": 0.35,
            "Champ Series": 0.20,
        }
        df["StageWeight"] = df["Stage"].map(stage_weights).fillna(0.5)
        df["WeightedFantasyScore"] = df["ProjectedPoints"] * df["StageWeight"]

        # Per-game helps compare players fairly
        df["FantasyPointsPerGame"] = df["ProjectedPoints"] / df["GamesPlayed"].replace(0, 1)
        df["WeightedFantasyPerGame"] = df["WeightedFantasyScore"] / df["GamesPlayed"].replace(0, 1)

        return df.reset_index(drop=True)

    def _build_player_context(self, league_settings: LeagueSettings, top_n: Optional[int] = None) -> str:
        """
        Build a compact player summary grouped across the 3 competition stages.
        """
        df = self._normalize_dataframe(league_settings)

        summary = (
            df.groupby(["Player", "Position", "Team"], dropna=False)
            .agg(
                GamesPlayed=("GamesPlayed", "sum"),
                Goals=("Goals", "sum"),
                OnePointGoals=("OnePointGoals", "sum"),
                TwoPointGoals=("TwoPointGoals", "sum"),
                Assists=("Assists", "sum"),
                GroundBalls=("GroundBalls", "sum"),
                CausedTurnovers=("CausedTurnovers", "sum"),
                Turnovers=("Turnovers", "sum"),
                FaceoffsWon=("FaceoffsWon", "sum"),
                FaceoffsLost=("FaceoffsLost", "sum"),
                Saves=("Saves", "sum"),
                ScoresAgainst=("ScoresAgainst", "sum"),
                TwoPointGoalsAgainst=("TwoPointGoalsAgainst", "sum"),
                ProjectedPoints=("ProjectedPoints", "sum"),
                WeightedFantasyScore=("WeightedFantasyScore", "sum"),
            )
            .reset_index()
        )

        summary["FantasyPointsPerGame"] = (
            summary["ProjectedPoints"] / summary["GamesPlayed"].replace(0, 1)
        )
        summary["WeightedFantasyPerGame"] = (
            summary["WeightedFantasyScore"] / summary["GamesPlayed"].replace(0, 1)
        )

        summary = summary.sort_values("WeightedFantasyScore", ascending=False)

        if top_n is not None:
            summary = summary.head(top_n)

        lines = []
        for _, row in summary.iterrows():
            player_name = row["Player"] if row["Player"] else "Unknown Player"
            lines.append(
                f"{player_name} | "
                f"Pos={row['Position']} | "
                f"Team={row['Team']} | "
                f"Games={int(row['GamesPlayed'])} | "
                f"Goals={int(row['Goals'])} | "
                f"1PtGoals={int(row['OnePointGoals'])} | "
                f"2PtGoals={int(row['TwoPointGoals'])} | "
                f"Assists={int(row['Assists'])} | "
                f"GB={int(row['GroundBalls'])} | "
                f"CT={int(row['CausedTurnovers'])} | "
                f"TO={int(row['Turnovers'])} | "
                f"FO_Wins={int(row['FaceoffsWon'])} | "
                f"FO_Losses={int(row['FaceoffsLost'])} | "
                f"Saves={int(row['Saves'])} | "
                f"ProjFantasy={round(float(row['ProjectedPoints']), 2)} | "
                f"WeightedFantasy={round(float(row['WeightedFantasyScore']), 2)} | "
                f"FantasyPPG={round(float(row['FantasyPointsPerGame']), 2)} | "
                f"WeightedPPG={round(float(row['WeightedFantasyPerGame']), 2)}"
            )

        return "\n".join(lines)

    def ask_question(self, question: str, league_settings: LeagueSettings) -> str:
        """
        Send the PLL fantasy question to the model and return the answer.
        """
        if self.df.empty:
            raise ValueError("No data loaded. Call load_data() first.")

        player_context = self._build_player_context(league_settings)

        system_prompt = (
            "You are a sharp PLL fantasy assistant. "
            "Use only the provided 2025 player data and league settings. "
            "Regular Season data should matter the most for fantasy advice. "
            "Postseason data is supporting evidence. "
            "Champ Series data is extra context and should be weighted the least. "
            "Give actionable, concise advice for start/sit decisions, rankings, and player comparisons. "
            "Do not invent stats. If the data is limited, say so clearly."
        )

        user_prompt = f"""
League settings:
{json.dumps(league_settings.__dict__, indent=2)}

Player data:
{player_context}

User question:
{question}

Instructions:
- Answer specifically for PLL fantasy.
- If asked for rankings, provide a ranked list.
- If asked for comparison, clearly pick a side and explain why.
- If asked start/sit, prioritize regular season production and role.
- Use postseason and champ series as supporting context only.
- Keep the answer readable and useful.
"""

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.output_text