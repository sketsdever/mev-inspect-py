from typing import List

from mev_inspect.aave_liquidations import get_aave_liquidations
from mev_inspect.compound_liquidations import get_compound_liquidations
from mev_inspect.crud.liquidations import fetch_all_ctoken_markets
from mev_inspect.schemas.traces import (
    ClassifiedTrace,
    Classification,
)
from mev_inspect.schemas.liquidations import Liquidation


def has_liquidations(classified_traces: List[ClassifiedTrace]) -> bool:
    liquidations_exist = False
    for classified_trace in classified_traces:
        if classified_trace.classification == Classification.liquidate:
            liquidations_exist = True
    return liquidations_exist


def get_liquidations(
    db_session,
    classified_traces: List[ClassifiedTrace],
) -> List[Liquidation]:
    aave_liquidations = get_aave_liquidations(classified_traces)
    c_token_underlying_markets = fetch_all_ctoken_markets(db_session)
    if (
        c_token_underlying_markets != {}
    ):  # if the underlying markets have been backfilled
        compound_liquidations = get_compound_liquidations(
            classified_traces, c_token_underlying_markets
        )
        return aave_liquidations + compound_liquidations

    return aave_liquidations
