from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from cafesito.api.app import create_app
from cafesito.config import Settings
from cafesito.db.seed import seed_database
from cafesito.db.session import create_db_engine, create_session_factory
from cafesito.ml.training import TrainingConfig, train_all
from tests.factories import build_sales_frame

TEST_TRAINING = TrainingConfig(min_support=0.01)


@pytest.fixture(scope="session")
def sales_frame() -> pd.DataFrame:
    return build_sales_frame()


@pytest.fixture(scope="session")
def database_path(tmp_path_factory: pytest.TempPathFactory, sales_frame: pd.DataFrame) -> Path:
    path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_db_engine(f"sqlite:///{path.as_posix()}")
    seed_database(engine, sales_frame)
    engine.dispose()
    return path


@pytest.fixture(scope="session")
def engine(database_path: Path) -> Iterator[Engine]:
    db_engine = create_db_engine(f"sqlite:///{database_path.as_posix()}")
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    factory = create_session_factory(engine)
    with factory() as db_session:
        yield db_session


@pytest.fixture(scope="session")
def models_dir(tmp_path_factory: pytest.TempPathFactory, engine: Engine) -> Path:
    path = tmp_path_factory.mktemp("models")
    train_all(engine, path, TEST_TRAINING)
    return path


@pytest.fixture(scope="session")
def client(database_path: Path, models_dir: Path) -> Iterator[TestClient]:
    settings = Settings(database_path=database_path, models_dir=models_dir)
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def untrained_client(database_path: Path, tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(database_path=database_path, models_dir=tmp_path / "empty")
    with TestClient(create_app(settings)) as test_client:
        yield test_client
