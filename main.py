import asyncio
import json
import pickle
import time
import urllib.parse
from typing import Dict

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from loguru import logger

from base import LnurlpFirstResponse, LnurlpSecondResponse, PendingInvoice
from cashu.core.helpers import sum_proofs
from cashu.core.settings import settings as cashu_settings
from cashu.nostr.client.client import NostrClient
from cashu.nostr.key import PublicKey
from cashu.wallet.wallet import Wallet
from settings import settings

# HOST_URL = "http://localhost:8000"
# MINT_URL = "http://localhost:3338"
# USERS_HOST = "https://cashu.me"
# INVOICES_DB = "invoices.pickle"
router: APIRouter = APIRouter()
wallet = Wallet(url=settings.mint_url, db=settings.cashu_db_path)
cashu_settings.tor = False

invoices: Dict[str, PendingInvoice] = {}
users: Dict[str, str] = {}


def store_invoices():
    pickle.dump(invoices, open(settings.invoices_db, "wb+"))


async def startup_server():
    global users
    global invoices
    # get https://cashu.me/.well-known/nostr.json and get key "names" and store it as users dict
    try:
        if settings.nip05_host:
            res = httpx.get(
                urllib.parse.urljoin(settings.nip05_host, "/.well-known/nostr.json"),
                timeout=5,
            ).raise_for_status()
            nip05 = json.loads(res.text)["names"]
            users.update(nip05)
            logger.info(f"Loaded {len(nip05)} users from {settings.nip05_host}")
    except Exception as e:
        logger.warning(f"Could not fetch users from {settings.nip05_host}: {str(e)}")
    logger.info(f"{len(users)} users loaded")

    try:
        invoices = pickle.load(open(settings.invoices_db, "rb"))
        logger.info(f"Loaded {len(invoices)} invoices from file")
    except Exception:
        logger.info("No invoices.pickle file found")
    for invoice in invoices.values():
        asyncio.create_task(invoice_checker(invoice))


async def start_wallet():
    global wallet
    wallet = await Wallet.with_db(
        url=settings.mint_url,
        db=settings.cashu_db_path,
    )
    await wallet.load_mint()


asyncio.create_task(start_wallet())


async def invoice_checker(invoice: PendingInvoice):
    logger.info(
        f"Created task for user '{invoice.username}' amount: {invoice.amount} sat invoice: {invoice.invoice.id}"
    )
    paid = False
    proofs = []
    while not paid:
        if time.time() - invoice.created > 60 * 60:
            del invoices[invoice.invoice.id]
            store_invoices()
            logger.warning(
                f"Invoice {invoice.invoice.id} has exceeded timeout. Deleting."
            )
            return
        if time.time() - invoice.created > 60:
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(5)

        try:
            proofs = await wallet.mint(invoice.amount, id=invoice.invoice.id)
            logger.success(f"Invoice {invoice.invoice.id} paid!")
            paid = True
        except Exception as e:
            logger.debug(f"Invoice {invoice.invoice.id} not paid yet: {str(e)}")
            if "already issued" in str(e):
                logger.warning(f"Already issued! Deleting invoice {invoice.invoice.id}")
                del invoices[invoice.invoice.id]
                store_invoices()
                return
    if not proofs:
        return
    pubkey_to = (
        PublicKey().from_npub(invoice.pubkey)
        if invoice.pubkey.startswith("npub")
        else PublicKey(bytes.fromhex(invoice.pubkey))
    )
    logger.info(f"Sending {sum_proofs(proofs)} sat token to {pubkey_to.bech32()}")
    nostr = NostrClient()
    nostr.dm(await wallet.serialize_proofs(proofs), pubkey_to)
    await asyncio.sleep(5)
    nostr.close()
    if invoice.invoice.id in invoices:
        del invoices[invoice.invoice.id]
    store_invoices()


@router.get("/.well-known/lnurlp/{username}")
async def lnurlp(username: str, amount: int = Query(None), comment: str = Query(None)):
    global users
    username = username.lower()
    if amount:
        amount = amount // 1000

    if not username.startswith("npub") and username.lower() not in [
        u.lower() for u in users.keys()
    ]:
        raise Exception("user not found")

    if amount is None:
        return LnurlpFirstResponse(
            callback=urllib.parse.urljoin(
                settings.lnurl_host, f"/.well-known/lnurlp/{username}"
            )
        )
    if len(invoices) > 100:
        return
    invoice = await wallet.request_mint(amount)
    pubkey = users[username] if not username.startswith("npub") else username
    pending_invoice = PendingInvoice(
        invoice=invoice,
        username=username,
        pubkey=pubkey,
        amount=amount,
        comment=comment,
        created=int(time.time()),
    )
    invoices[pending_invoice.invoice.id] = pending_invoice
    store_invoices()
    asyncio.create_task(invoice_checker(pending_invoice))
    return LnurlpSecondResponse(
        pr=invoice.bolt11,
        successAction={
            "tag": "message",
            "message": f"Payment forwarded to {username}'s nostr pubkey.",
        },
    )
