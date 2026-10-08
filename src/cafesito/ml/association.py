import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from pydantic import BaseModel, ConfigDict


class Rule(BaseModel):
    model_config = ConfigDict(frozen=True)

    antecedent: tuple[str, ...]
    consequent: tuple[str, ...]
    support: float
    confidence: float
    lift: float


def mine_rules(
    baskets: pd.DataFrame, min_support: float = 0.005, min_lift: float = 1.0
) -> list[Rule]:
    itemsets = apriori(baskets, min_support=min_support, use_colnames=True)
    if itemsets.empty:
        return []
    table = association_rules(
        itemsets, num_itemsets=len(baskets), metric="lift", min_threshold=min_lift
    )
    rules = [
        Rule(
            antecedent=tuple(sorted(row.antecedents)),
            consequent=tuple(sorted(row.consequents)),
            support=float(row.support),
            confidence=float(row.confidence),
            lift=float(row.lift),
        )
        for row in table.itertuples()
    ]
    return sorted(rules, key=lambda rule: rule.lift, reverse=True)
