from itertools import groupby
from typing import Dict, List, Optional, Sequence

from mev_inspect.classifiers.specs import get_classifier
from mev_inspect.schemas.classifiers import TransferClassifier
from mev_inspect.schemas.classified_traces import (
    ClassifiedTrace,
    DecodedCallTrace,
)
from mev_inspect.schemas.transfers import (
    ERC20Transfer,
    EthTransfer,
    Transfer,
    TransferGeneric,
)
from mev_inspect.traces import is_child_trace_address


def get_transfers(traces: List[ClassifiedTrace]) -> List[Transfer]:
    transfers: List[Transfer] = []

    for trace in traces:
        if trace.value is not None and trace.value > 0:
            transfers.append(EthTransfer.from_trace(trace))

        if isinstance(trace, DecodedCallTrace):
            transfer = _get_erc20_transfer(trace)
            if transfer is not None:
                transfers.append(transfer)

    return transfers


def get_eth_transfers(traces: List[ClassifiedTrace]) -> List[EthTransfer]:
    transfers = []

    for trace in traces:
        if trace.value is not None and trace.value > 0:
            transfers.append(EthTransfer.from_trace(trace))

    return transfers


def _get_erc20_transfer(trace: DecodedCallTrace) -> Optional[ERC20Transfer]:
    if not isinstance(trace, DecodedCallTrace):
        return None

    classifier = get_classifier(trace)
    if classifier is not None and issubclass(classifier, TransferClassifier):
        return classifier.get_transfer(trace)

    return None


def filter_transfers(
    transfers: Sequence[TransferGeneric],
    to_address: Optional[str] = None,
    from_address: Optional[str] = None,
) -> List[TransferGeneric]:
    filtered_transfers = []

    for transfer in transfers:
        if to_address is not None and transfer.to_address != to_address:
            continue

        if from_address is not None and transfer.from_address != from_address:
            continue

        filtered_transfers.append(transfer)

    return filtered_transfers


def remove_child_transfers_of_transfers(
    transfers: List[Transfer],
) -> List[Transfer]:
    updated_transfers = []
    transfer_addresses_by_transaction: Dict[str, List[List[int]]] = {}

    sorted_transfers = sorted(transfers, key=lambda t: t.trace_address)

    for transfer in sorted_transfers:
        existing_addresses = transfer_addresses_by_transaction.get(
            transfer.transaction_hash, []
        )

        if not any(
            is_child_trace_address(transfer.trace_address, parent_address)
            for parent_address in existing_addresses
        ):
            updated_transfers.append(transfer)

        transfer_addresses_by_transaction[
            transfer.transaction_hash
        ] = existing_addresses + [transfer.trace_address]

    return updated_transfers


def get_transfers_by_transaction_hash(
    transfers: List[Transfer],
) -> Dict[str, List[Transfer]]:
    get_transaction_hash = lambda transfer: transfer.transaction_hash
    return {
        transaction_hash: list(transfers)
        for transaction_hash, transfers in groupby(
            sorted(transfers, key=get_transaction_hash),
            key=get_transaction_hash,
        )
    }
