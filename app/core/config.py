from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    identity_service_url: str = "http://127.0.0.1:8020"
    order_service_url: str = "http://127.0.0.1:8030"
    catalog_service_url: str = ""
    customers_service_url: str = ""
    billing_service_url: str = ""
    audit_service_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
