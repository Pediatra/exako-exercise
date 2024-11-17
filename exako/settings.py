from pathlib import Path

from pydantic import MongoDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    FIEF_CLIENT_ID: str
    FIEF_CLIENT_SCRET: str
    FIEF_DOMAIN: str

    API_DOMAIN: str

    @property
    def DATABASE(self):
        return str(
            MongoDsn.build(
                scheme='mongodb',
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                path=self.DATABASE_NAME,
            )
        )

    class Config:
        env_file = '.env'


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent
