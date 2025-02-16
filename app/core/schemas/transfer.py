from pydantic import BaseModel


class SendCoinRequest(BaseModel):
    to_user: str
    amount: int

class TransactionGroup(BaseModel):
    counterparty: str
    total_amount: int