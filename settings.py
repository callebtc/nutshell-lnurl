from environs import Env
from pydantic import BaseSettings, Field

env = Env()


class ServerSettings(BaseSettings):
    lnurl_host: str = Field(default="http://localhost:8000")
    mint_url: str = Field(default="http://localhost:3338")
    nip05_host: str = Field(default="https://cashu.me")
    invoices_db: str = Field(default="invoices.pickle")
    cashu_db_path: str = Field(default="./cashu")


settings = ServerSettings()
