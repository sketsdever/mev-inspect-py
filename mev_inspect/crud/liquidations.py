import json
from typing import List, Dict

from mev_inspect.models.liquidations import LiquidationModel, CTokenModel
from mev_inspect.schemas.liquidations import Liquidation, CTokenMarket


def delete_liquidations_for_block(
    db_session,
    block_number: int,
) -> None:
    (
        db_session.query(LiquidationModel)
        .filter(LiquidationModel.block_number == block_number)
        .delete()
    )

    db_session.commit()


def write_liquidations(
    db_session,
    liquidations: List[Liquidation],
) -> None:
    models = [
        LiquidationModel(**json.loads(liquidation.json()))
        for liquidation in liquidations
    ]

    db_session.bulk_save_objects(models)
    db_session.commit()


def fetch_all_ctoken_markets(db_session) -> Dict[str, str]:
    result = db_session.query(CTokenModel).all()
    markets: Dict[str, str] = {}
    if result == []:
        return markets
    else:
        for market in result:
            markets[market.ctoken_address] = market.underlying_token_address
        return markets


def write_ctoken_markets(
    db_session,
    markets: List[CTokenMarket],
) -> None:
    models = [CTokenModel(**json.loads(market.json())) for market in markets]

    db_session.bulk_save_objects(models)
    db_session.commit()
