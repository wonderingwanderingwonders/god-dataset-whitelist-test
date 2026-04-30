"""
Drop-in replacement for miner/endpoints/tuning.py in the G.O.D repo.

This configures the miner to respond with requested_datasets when the
validator asks for the training repo. Point github_repo and commit_hash
to this test repo.

Usage:
    1. On the miner machine, clone G.O.D and checkout feature/miner-dataset-whitelist
    2. Replace miner/endpoints/tuning.py with this file
    3. Update REPO_URL and COMMIT_HASH below
    4. Start the miner: task miner
"""

from fastapi import Depends
from fastapi.routing import APIRouter
from fiber.miner.dependencies import blacklist_low_stake
from fiber.miner.dependencies import verify_get_request

from core.models.payload_models import TrainingRepoResponse
from core.models.tournament_models import TournamentType

# --- CONFIGURE THESE ---
REPO_URL = "https://github.com/wonderingwanderingwonders/god-dataset-whitelist-test"
COMMIT_HASH = "main"
REQUESTED_DATASETS = ["tasksource/Boardgame-QA"]
# -----------------------


async def get_training_repo(task_type: TournamentType) -> TrainingRepoResponse:
    return TrainingRepoResponse(
        github_repo=REPO_URL,
        commit_hash=COMMIT_HASH,
        github_token=None,
        requested_datasets=REQUESTED_DATASETS if task_type == TournamentType.ENVIRONMENT else None,
    )


def factory_router() -> APIRouter:
    router = APIRouter()

    router.add_api_route(
        "/training_repo/{task_type}",
        get_training_repo,
        tags=["Subnet"],
        methods=["GET"],
        response_model=TrainingRepoResponse,
        summary="Get Training Repo",
        description="Retrieve the training repository and commit hash for the tournament.",
        dependencies=[Depends(blacklist_low_stake), Depends(verify_get_request)],
    )

    return router
