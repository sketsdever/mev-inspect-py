from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from .traces import Classification, DecodedCallTrace, Protocol
from .transfers import Transfer


class Classifier(ABC):
    @staticmethod
    @abstractmethod
    def get_classification() -> Classification:
        raise NotImplementedError()


class TransferClassifier(Classifier):
    @staticmethod
    def get_classification() -> Classification:
        return Classification.transfer

    @staticmethod
    @abstractmethod
    def get_transfer(trace: DecodedCallTrace) -> Transfer:
        raise NotImplementedError()


class SwapClassifier(Classifier):
    @staticmethod
    def get_classification() -> Classification:
        return Classification.swap

    @staticmethod
    @abstractmethod
    def get_swap_recipient(trace: DecodedCallTrace) -> str:
        raise NotImplementedError()


class LiquidationClassifier(Classifier):
    @staticmethod
    def get_classification() -> Classification:
        return Classification.liquidate


class NewMarketClassifier(Classifier):
    @staticmethod
    def get_classification() -> Classification:
        return Classification.new_market


class SeizeClassifier(Classifier):
    @staticmethod
    def get_classification() -> Classification:
        return Classification.seize


class ClassifierSpec(BaseModel):
    abi_name: str
    protocol: Optional[Protocol] = None
    valid_contract_addresses: Optional[List[str]] = None
    classifiers: Dict[str, Type[Classifier]] = {}
