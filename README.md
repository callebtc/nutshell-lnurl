# Nutshell LNURL Cashu bridge

*This is proof of concept software that is meant only for education and experimenting. It likely has bugs and is not meant for production.*

Nutshell-lnurl is a service that creates invoices from a specified Cashu mint and serves them over LNURL endpoints. When the invoice is paid, the service mints Ecash with the mint and sends them to the intended recipient via Nostr DMs.

### Features
- LN addresses for npubs a la `<npub>@my.lnurl-domain.com`
- Pulls npubs from NIP-05 lists for addresses a la `<user>@my.lnurl-domain.com`
- Persists unpaid invoices and picks them up on startup

### Todo
- [ ] Configure nostr relays
- [ ] Fetch nostr relays from user profile
- [ ] Fetch Cashu mint from user profile
- [ ] Host addresses like `user@nip05-host.com@my.lnurl-domain.com`


### Install
- Clone this repository
- Install dependencies using `poetry install`
- Copy settings `cp .env.example .env` and edit `.env` file
- Activate environment using `poetry shell`
- Run server using `uvicorn app:app`

### Configuration
Set the mint the Cashu tokens will be minted from. 
```
MINT_URL=http://cashu.mint.com
```
Publicly exposed hostname of your LNURL server
```
LNURL_HOST=https://my.lnurl-domain.com
```
Optional: Select a [NIP-05](https://github.com/nostr-protocol/nips/blob/master/05.md) host to serve LN addresses with usernames like `user@host.com`
```
NIP05_HOST=https://nip5.host.com
```
