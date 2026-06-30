from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TeamOut(BaseModel):
    id: int
    group_name: str | None = None
    name: str
    fifa_code: str
    confederation: str
    flag_url: str | None = None
    fifa_ranking: int | None = None
    fifa_ranking_points: float | None = None
    elo_rating: float | None = None
    gdp_per_capita: float | None = None
    population: int | None = None
    football_popularity_score: float | None = None
    host_advantage_score: float | None = None
    historical_world_cup_score: float | None = None


class PlayerOut(BaseModel):
    id: int
    team_id: int
    name: str
    position: str
    shirt_number: int | None = None
    age: int | None = None
    club: str | None = None
    caps: int | None = None
    goals: int | None = None
    tournament_goals: int = 0
    rating: float | None = None


class MatchOut(BaseModel):
    id: int
    tournament_year: int
    stage: str
    group_name: str | None = None
    home_team_id: int
    away_team_id: int
    kickoff_at: datetime
    kickoff_timezone: str = "Europe/Oslo"
    stadium: str
    city: str
    status: str
    home_score: int | None = None
    away_score: int | None = None
    home_team: TeamOut | None = None
    away_team: TeamOut | None = None


class MatchEventOut(BaseModel):
    id: int
    match_id: int
    minute: int
    second: int | None = None
    event_type: str
    team_id: int | None = None
    player_id: int | None = None
    assist_player_id: int | None = None
    description: str


class LineupPlayerOut(BaseModel):
    id: int
    lineup_id: int
    player_id: int
    position_x: float
    position_y: float
    is_starter: bool
    player: PlayerOut | None = None


class LineupOut(BaseModel):
    id: int
    match_id: int
    team_id: int
    formation: str
    players: list[LineupPlayerOut] = Field(default_factory=list)


class BroadcastOut(BaseModel):
    id: int
    match_id: int
    country_code: str
    broadcaster: str
    channel: str
    stream_url: str | None = None
    replay_url: str | None = None
    requires_login: bool
    source_url: str
    last_checked_at: datetime | None = None


class PredictionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    match_id: int = Field(ge=1)
    user_name: str = Field(default="portfolio_guest", min_length=1, max_length=80)
    predicted_home_score: int = Field(ge=0, le=30)
    predicted_away_score: int = Field(ge=0, le=30)
    predicted_winner_team_id: int | None = Field(default=None, ge=1)
    first_goalscorer_player_id: int | None = Field(default=None, ge=1)
    group_winners_json: dict[str, int] | None = Field(default=None, max_length=16)
    tournament_winner_team_id: int | None = Field(default=None, ge=1)
    tournament_top_scorer_player_id: int | None = Field(default=None, ge=1)


class PredictionScoreOut(BaseModel):
    total_points: int
    breakdown: dict[str, int]


class UserPredictionOut(PredictionIn):
    id: int
    points: int = 0
    created_at: datetime
    scoring: PredictionScoreOut | None = None


class ModelPredictionOut(BaseModel):
    id: int | None = None
    match_id: int
    model_version: str
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    expected_home_goals: float
    expected_away_goals: float
    predicted_score: str
    explanation_json: dict[str, Any]
    created_at: datetime


class LiveSnapshotOut(BaseModel):
    id: int
    match_id: int
    minute: int
    second: int | None = None
    home_score: int
    away_score: int
    home_xg: float
    away_xg: float
    home_shots: int
    away_shots: int
    home_shots_on_target: int
    away_shots_on_target: int
    home_possession: float
    away_possession: float
    home_corners: int
    away_corners: int
    home_yellow_cards: int
    away_yellow_cards: int
    home_red_cards: int
    away_red_cards: int
    home_dangerous_attacks: int
    away_dangerous_attacks: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    model_version: str
    created_at: datetime


class ProbabilityEventOut(BaseModel):
    id: int
    match_id: int
    snapshot_id: int | None = None
    minute: int
    score_state: str
    event_type: str
    previous_home_win_probability: float
    current_home_win_probability: float
    probability_delta: float
    explanation: str
    factors_json: dict[str, Any]
    created_at: datetime
