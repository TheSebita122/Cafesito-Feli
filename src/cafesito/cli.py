import argparse
import json
import logging
import sys
from collections.abc import Sequence

from cafesito.config import Settings, get_settings
from cafesito.db.seed import SeedError, database_is_seeded, read_sales_csv, seed_database
from cafesito.db.session import create_db_engine
from cafesito.ml.artifacts import DEMAND_FILE, METRICS_FILE
from cafesito.ml.training import train_all

logger = logging.getLogger("cafesito")


def seed(settings: Settings) -> None:
    engine = create_db_engine(settings.database_url)
    seed_database(engine, read_sales_csv(settings.sales_csv_path))


def train(settings: Settings) -> None:
    engine = create_db_engine(settings.database_url)
    metrics = train_all(engine, settings.models_dir)
    print(json.dumps(metrics["demand"]["accuracy"]))


def bootstrap(settings: Settings) -> None:
    engine = create_db_engine(settings.database_url)
    if not database_is_seeded(engine):
        seed(settings)
    models_ready = (settings.models_dir / DEMAND_FILE).exists() and (
        settings.models_dir / METRICS_FILE
    ).exists()
    if not models_ready:
        train(settings)


def serve(settings: Settings) -> None:
    import uvicorn

    bootstrap(settings)
    uvicorn.run(
        "cafesito.api.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


COMMANDS = {"seed": seed, "train": train, "bootstrap": bootstrap, "serve": serve}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cafesito")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    try:
        COMMANDS[args.command](settings)
    except SeedError as error:
        logger.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
