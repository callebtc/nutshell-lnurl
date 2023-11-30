from typing import Optional

from pydantic import BaseModel

from cashu.core.base import Invoice


class PendingInvoice(BaseModel):
    invoice: Invoice
    username: str
    pubkey: str
    amount: int
    created: int
    comment: Optional[str] = None
    paid: bool = False
    forwarded: bool = False
    token: Optional[str] = None


class LnurlpFirstResponse(BaseModel):
    callback: str
    status: str = "OK"
    tag: str = "payRequest"
    minSendable: int = 1000
    maxSendable: int = 1000000
    metadata: str = '[["text/plain", "This is a Cashu-LNURL bridge. A Cashu token will be sent to the recipient\'s nostr pubkey."]]'
    commentAllowed: int = 0


class LnurlpSecondResponse(BaseModel):
    pr: str
    status: str = "OK"
    successAction: dict = {"tag": "message", "message": "Payment forwarded."}
