import pandas as pd
import pytest
from sqlalchemy import Engine

from cafesito.ml.association import Rule, mine_rules
from cafesito.ml.dataset import load_baskets


@pytest.fixture(scope="module")
def baskets(engine: Engine) -> pd.DataFrame:
    return load_baskets(engine)


def test_baskets_are_boolean_matrix_by_product_type(baskets: pd.DataFrame) -> None:
    assert baskets.dtypes.eq(bool).all()
    assert "Barista Espresso" in baskets.columns
    assert baskets.any(axis=1).all()


def test_mine_rules_finds_the_syrup_espresso_pairing(baskets: pd.DataFrame) -> None:
    rules = mine_rules(baskets, min_support=0.01)
    syrup_rules = [rule for rule in rules if rule.antecedent == ("Regular syrup",)]
    assert syrup_rules
    assert syrup_rules[0].consequent == ("Barista Espresso",)
    assert syrup_rules[0].confidence > 0.9
    assert syrup_rules[0].lift > 1.2


def test_rules_are_sorted_by_lift(baskets: pd.DataFrame) -> None:
    lifts = [rule.lift for rule in mine_rules(baskets, min_support=0.01)]
    assert lifts == sorted(lifts, reverse=True)


def test_mine_rules_returns_empty_when_support_is_unreachable(baskets: pd.DataFrame) -> None:
    assert mine_rules(baskets, min_support=0.99) == []


def test_min_lift_filters_weak_rules(baskets: pd.DataFrame) -> None:
    strong = mine_rules(baskets, min_support=0.01, min_lift=2.0)
    assert strong
    assert all(rule.lift >= 2.0 for rule in strong)


def test_rule_round_trips_through_dict() -> None:
    rule = Rule(antecedent=("a",), consequent=("b",), support=0.1, confidence=0.5, lift=2.0)
    assert Rule.model_validate(rule.model_dump()) == rule
