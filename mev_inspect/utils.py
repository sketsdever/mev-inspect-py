from hexbytes._utils import hexstr_to_bytes
from typing import List
from web3 import Web3
from mev_inspect.abi import get_raw_abi
from mev_inspect.compound_liquidations import fetch_token_symbol
from mev_inspect.schemas.liquidations import CTokenMarket
from mev_inspect.crud.liquidations import write_ctoken_markets

from mev_inspect.schemas.traces import Classification, ClassifiedTrace, Protocol

COMPOUND_COMPTROLLER_ADDRESS = "0x95b4ef2869ebd94beb4eee400a99824bf5dc325b"


def hex_to_int(value: str) -> int:
    return int.from_bytes(hexstr_to_bytes(value), byteorder="big")


def check_for_updates(classified_traces: List[ClassifiedTrace], w3: Web3, db_session):
    # We check if any new lending markets have been added to compound
    # at the beginning of every new block
    markets = []
    for trace in classified_traces:
        if (
            trace.classification == Classification.new_market
            and trace.inputs is not None
            and trace.inputs["cToken"] == COMPOUND_COMPTROLLER_ADDRESS
        ):
            token_abi = get_raw_abi("CToken", Protocol.compound_v2)
            token_instance = w3.eth.contract(
                address=trace.inputs["cToken"], abi=token_abi
            )
            underlying_token_address = token_instance.functions.underlying().call()
            symbol = fetch_token_symbol(w3, trace.inputs["cToken"])
            markets.append(
                CTokenMarket(
                    ctoken_address=trace.inputs["cToken"],
                    ctoken_symbol=symbol,
                    underlying_token_address=underlying_token_address,
                )
            )
    if markets != []:
        write_ctoken_markets(db_session, markets)
