from __future__ import annotations

import math
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import get_connection, initialize_database


app = FastAPI(title="World Leader Smash API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VotePayload(BaseModel):
    winner_id: int
    loser_id: int


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/matchup")
def get_matchup() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        leaders = connection.execute(
            "SELECT id, name, country, photo_url, elo, wins, losses FROM leaders ORDER BY RANDOM() LIMIT 2"
        ).fetchall()

    if len(leaders) < 2:
        raise HTTPException(status_code=400, detail="At least two leaders are required.")

    return {"leaders": [dict(leader) for leader in leaders]}


@app.get("/leaderboard")
def get_leaderboard() -> dict[str, list[dict[str, object]]]:
    with get_connection() as connection:
        leaders = connection.execute(
            """
            SELECT id, name, country, photo_url, elo, wins, losses
            FROM leaders
            ORDER BY elo DESC, wins DESC, name ASC
            """
        ).fetchall()

    return {"leaders": [dict(leader) for leader in leaders]}


@app.post("/vote")
def record_vote(payload: VotePayload) -> dict[str, object]:
    if payload.winner_id == payload.loser_id:
        raise HTTPException(status_code=400, detail="Winner and loser must be different.")

    with get_connection() as connection:
        winner = connection.execute(
            "SELECT id, elo, wins, losses FROM leaders WHERE id = %s",
            (payload.winner_id,),
        ).fetchone()
        loser = connection.execute(
            "SELECT id, elo, wins, losses FROM leaders WHERE id = %s",
            (payload.loser_id,),
        ).fetchone()

        if winner is None or loser is None:
            raise HTTPException(status_code=404, detail="Leader not found.")

        winner_new_elo, loser_new_elo = calculate_elo(winner["elo"], loser["elo"])

        connection.execute(
            "UPDATE leaders SET elo = %s, wins = wins + 1 WHERE id = %s",
            (winner_new_elo, payload.winner_id),
        )
        connection.execute(
            "UPDATE leaders SET elo = %s, losses = losses + 1 WHERE id = %s",
            (loser_new_elo, payload.loser_id),
        )
        connection.execute(
            "INSERT INTO votes (winner_id, loser_id) VALUES (%s, %s)",
            (payload.winner_id, payload.loser_id),
        )
        connection.commit()

    return {
        "success": True,
        "winner_id": payload.winner_id,
        "loser_id": payload.loser_id,
        "next_hint": random.randint(1000, 9999),
    }


def calculate_elo(winner_elo: int, loser_elo: int, k_factor: int = 32) -> tuple[int, int]:
    winner_expected = 1 / (1 + math.pow(10, (loser_elo - winner_elo) / 400))
    loser_expected = 1 / (1 + math.pow(10, (winner_elo - loser_elo) / 400))

    winner_new = round(winner_elo + k_factor * (1 - winner_expected))
    loser_new = round(loser_elo + k_factor * (0 - loser_expected))
    return winner_new, loser_new
