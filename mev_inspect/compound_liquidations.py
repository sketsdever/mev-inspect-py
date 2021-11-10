from typing import Dict, List, Optional
from web3 import Web3

from mev_inspect.traces import get_child_traces
from mev_inspect.schemas.traces import (
    ClassifiedTrace,
    Classification,
    Protocol,
)

from mev_inspect.schemas.liquidations import Liquidation
from mev_inspect.abi import get_raw_abi
from mev_inspect.transfers import ETH_TOKEN_ADDRESS

V2_COMPTROLLER_ADDRESS = "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"
V2_C_ETHER = "0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5"
CREAM_COMPTROLLER_ADDRESS = "0x3d5BC3c8d13dcB8bF317092d84783c2697AE9258"
CREAM_CR_ETHER = "0xD06527D5e56A3495252A528C4987003b712860eE"

# helper, only queried once in the beginning (inspect_block)
def fetch_all_underlying_markets(w3: Web3, protocol: Protocol) -> Dict[str, str]:
    if protocol == Protocol.compound_v2:
        c_ether = V2_C_ETHER
        address = V2_COMPTROLLER_ADDRESS
    elif protocol == Protocol.cream:
        c_ether = CREAM_CR_ETHER
        address = CREAM_COMPTROLLER_ADDRESS
    else:
        raise ValueError(f"No Comptroller found for {protocol}")
    token_mapping = {}
    comptroller_abi = get_raw_abi("Comptroller", Protocol.compound_v2)
    comptroller_instance = w3.eth.contract(address=address, abi=comptroller_abi)
    markets = comptroller_instance.functions.getAllMarkets().call()
    token_abi = get_raw_abi("CToken", Protocol.compound_v2)
    for token in markets:
        # make an exception for cETH (as it has no .underlying())
        if token != c_ether:
            token_instance = w3.eth.contract(address=token, abi=token_abi)
            underlying_token = token_instance.functions.underlying().call()
            token_mapping[
                token.lower()
            ] = underlying_token.lower()  # make k:v lowercase for consistancy
    return token_mapping


def fetch_token_symbol(w3: Web3, token_address: str) -> str:
    erc20_abi = get_raw_abi("ERC20", None)
    token_instance = w3.eth.contract(
        address=Web3.toChecksumAddress(token_address), abi=erc20_abi
    )
    symbol = token_instance.functions.symbol().call()
    return symbol


def get_compound_liquidations(
    traces: List[ClassifiedTrace], c_token_underlying_markets: Dict[str, str]
) -> List[Liquidation]:

    """Inspect list of classified traces and identify liquidation"""
    liquidations: List[Liquidation] = []

    for trace in traces:
        if (
            trace.classification == Classification.liquidate
            and (
                trace.protocol == Protocol.compound_v2
                or trace.protocol == Protocol.cream
            )
            and trace.inputs is not None
            and trace.to_address is not None
        ):
            # First, we look for cEther liquidations (position paid back via tx.value)
            child_traces = get_child_traces(
                trace.transaction_hash, trace.trace_address, traces
            )
            seize_trace = _get_seize_call(child_traces)

            if (
                seize_trace is not None
                and seize_trace.inputs is not None
                and len(c_token_underlying_markets) != 0
            ):
                c_token_collateral = trace.inputs["cTokenCollateral"]
                if trace.abi_name == "CEther":
                    liquidations.append(
                        Liquidation(
                            liquidated_user=trace.inputs["borrower"],
                            collateral_token_address=ETH_TOKEN_ADDRESS,  # WETH since all cEther liquidations provide Ether
                            debt_token_address=c_token_collateral,
                            liquidator_user=seize_trace.inputs["liquidator"],
                            debt_purchase_amount=trace.value,
                            protocol=trace.protocol,
                            received_amount=seize_trace.inputs["seizeTokens"],
                            transaction_hash=trace.transaction_hash,
                            trace_address=trace.trace_address,
                            block_number=trace.block_number,
                        )
                    )
                elif (
                    trace.abi_name == "CToken"
                ):  # cToken liquidations where liquidator pays back via token transfer
                    c_token_address = trace.to_address
                    liquidations.append(
                        Liquidation(
                            liquidated_user=trace.inputs["borrower"],
                            collateral_token_address=c_token_underlying_markets[
                                c_token_address
                            ],
                            debt_token_address=c_token_collateral,
                            liquidator_user=seize_trace.inputs["liquidator"],
                            debt_purchase_amount=trace.inputs["repayAmount"],
                            protocol=trace.protocol,
                            received_amount=seize_trace.inputs["seizeTokens"],
                            transaction_hash=trace.transaction_hash,
                            trace_address=trace.trace_address,
                            block_number=trace.block_number,
                        )
                    )
    return liquidations


def _get_seize_call(traces: List[ClassifiedTrace]) -> Optional[ClassifiedTrace]:
    """Find the call to `seize` in the child traces (successful liquidation)"""
    for trace in traces:
        if trace.classification == Classification.seize:
            return trace
    return None
