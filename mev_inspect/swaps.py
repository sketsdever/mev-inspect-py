from typing import List, Optional

from mev_inspect.classifiers.specs import get_classifier
from mev_inspect.schemas.classified_traces import (
    ClassifiedTrace,
    Classification,
    DecodedCallTrace,
)
from mev_inspect.schemas.classifiers import SwapClassifier
from mev_inspect.schemas.swaps import Swap
from mev_inspect.schemas.transfers import ERC20Transfer, Transfer
from mev_inspect.traces import (
    get_traces_by_transaction_hash,
    is_child_trace_address,
)
from mev_inspect.transfers import (
    get_transfers_by_transaction_hash,
    filter_transfers,
    remove_child_transfers_of_transfers,
)


def get_swaps(
    traces: List[ClassifiedTrace],
    transfers: List[Transfer],
) -> List[Swap]:
    swaps = []
    traces_by_transaction = get_traces_by_transaction_hash(traces)
    transfers_by_transaction = get_transfers_by_transaction_hash(transfers)

    for hash, transaction_traces in traces_by_transaction.items():
        transaction_transfers = transfers_by_transaction.get(hash, [])
        swaps += _get_swaps_for_transaction(
            transaction_traces,
            transaction_transfers,
        )

    return swaps


def _get_swaps_for_transaction(
    traces: List[ClassifiedTrace],
    transfers: List[Transfer],
) -> List[Swap]:
    ordered_traces = list(sorted(traces, key=lambda t: t.trace_address))

    swaps: List[Swap] = []

    for trace in ordered_traces:
        if (
            isinstance(trace, DecodedCallTrace)
            and trace.classification == Classification.swap
        ):
            prior_transfers = [
                transfer
                for transfer in transfers
                if transfer.trace_address < trace.trace_address
            ]

            child_transfers = [
                transfer
                for transfer in transfers
                if is_child_trace_address(
                    transfer.trace_address,
                    trace.trace_address,
                )
            ]

            swap = _parse_swap(
                trace,
                remove_child_transfers_of_transfers(prior_transfers),
                remove_child_transfers_of_transfers(child_transfers),
            )

            if swap is not None:
                swaps.append(swap)

    return swaps


def _parse_swap(
    trace: DecodedCallTrace,
    prior_transfers: List[Transfer],
    child_transfers: List[Transfer],
) -> Optional[Swap]:
    pool_address = trace.to_address
    recipient_address = _get_recipient_address(trace)

    if recipient_address is None:
        return None

    transfers_to_pool = filter_transfers(prior_transfers, to_address=pool_address)

    if len(transfers_to_pool) == 0:
        transfers_to_pool = filter_transfers(child_transfers, to_address=pool_address)

    if len(transfers_to_pool) == 0:
        return None

    transfers_from_pool_to_recipient = filter_transfers(
        child_transfers, to_address=recipient_address, from_address=pool_address
    )

    if len(transfers_from_pool_to_recipient) != 1:
        return None

    transfer_in = transfers_to_pool[-1]
    transfer_out = transfers_from_pool_to_recipient[0]

    return Swap(
        abi_name=trace.abi_name,
        transaction_hash=trace.transaction_hash,
        block_number=trace.block_number,
        trace_address=trace.trace_address,
        pool_address=pool_address,
        from_address=transfer_in.from_address,
        to_address=transfer_out.to_address,
        token_in_address=_get_token_address_or_none(transfer_in),
        token_in_amount=transfer_in.amount,
        token_out_address=_get_token_address_or_none(transfer_out),
        token_out_amount=transfer_out.amount,
        error=trace.error,
    )


def _get_token_address_or_none(transfer: Transfer) -> Optional[str]:
    if isinstance(transfer, ERC20Transfer):
        return transfer.token_address

    return None


def _get_recipient_address(trace: DecodedCallTrace) -> Optional[str]:
    classifier = get_classifier(trace)
    if classifier is not None and issubclass(classifier, SwapClassifier):
        return classifier.get_swap_recipient(trace)

    return None
