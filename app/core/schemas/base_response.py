from pydantic import BaseModel
from typing import List, Dict, Union

from core.schemas.transfer import TransactionGroup


class InfoResponse(BaseModel):
    coin_balance: int
    inventory: List[Dict[str, Union[str, int]]]
    transactions_in: List[TransactionGroup]
    transactions_out: List[TransactionGroup]
