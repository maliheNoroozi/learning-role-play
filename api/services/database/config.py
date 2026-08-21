from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_db: str = "roleplay"
    mongodb_user: str = ""
    mongodb_password: str = ""


mongodb_config = MongoDBConfig()
