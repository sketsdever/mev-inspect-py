import os
from web3 import Web3
from mev_inspect.compound_liquidations import fetch_all_underlying_markets, fetch_token_symbol
from mev_inspect.crud.liquidations import write_ctoken_markets
from mev_inspect.schemas.liquidations import CTokenMarket
from mev_inspect.schemas.traces import Protocol
from mev_inspect.db import get_inspect_session

def store_markets():
    rpc = os.getenv("RPC_URL")
    if rpc is None:
        raise RuntimeError("Missing env variable RPC_URL, required for lending markets backfilling")
    
    w3 = Web3(Web3.HTTPProvider(rpc))
    print("Fetching COMP markets...")
    comp_markets = fetch_all_underlying_markets(w3, Protocol.compound_v2)
    print("Fetching CREAM markets...")
    cream_markets = fetch_all_underlying_markets(w3, Protocol.cream)

    markets = []

    for key in comp_markets:
        symbol = fetch_token_symbol(w3, key)
        print('Inserting {} market'.format(symbol))
        markets.append(
            CTokenMarket(
                ctoken_address=key,
                ctoken_symbol=symbol,
                underlying_token_address=comp_markets[key]
            )
        )

    for key in cream_markets:
        symbol = fetch_token_symbol(w3, key)
        print('Inserting {} market'.format(symbol))
        markets.append(
            CTokenMarket(
                ctoken_address=key,
                ctoken_symbol=symbol,
                underlying_token_address=cream_markets[key]
            )
        )
    inspect_db_session = get_inspect_session()
    write_ctoken_markets(inspect_db_session, markets)
    print("Done!")


if __name__ == "__main__":
    store_markets()