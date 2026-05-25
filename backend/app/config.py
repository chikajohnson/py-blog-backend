from urllib.parse import urlparse
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 3001
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Database configuration ──────────────────────────────────────
    # DB_MODE controls how the database connection string is resolved:
    #   "local"     – uses DATABASE_URL directly (any PostgreSQL instance)
    #   "supabase"  – derives connection from SUPABASE_URL + SUPABASE_DB_PASSWORD
    #   "azure"     – derives connection from AZURE_POSTGRES_* variables
    #   "aws"       – derives connection from AWS_RDS_* variables
    #
    # In every mode the DATABASE_URL / DATABASE_URL_SYNC values serve as
    # fallback when the cloud-specific credentials are incomplete.
    DB_MODE: str = "local"

    # Direct connection strings (used when DB_MODE=local, or as fallback)
    DATABASE_URL: str = "postgresql+asyncpg://pyflow_user:changeme@localhost:5432/pyflow"
    DATABASE_URL_SYNC: str = "postgresql://pyflow_user:changeme@localhost:5432/pyflow"

    # ── Supabase ────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_DB_PASSWORD: str = ""

    # ── Azure Database for PostgreSQL ───────────────────────────────
    # Set these along with DB_MODE=azure to connect to Azure Postgres.
    AZURE_POSTGRES_HOST: str = ""
    AZURE_POSTGRES_USER: str = ""
    AZURE_POSTGRES_PASSWORD: str = ""
    AZURE_POSTGRES_DATABASE: str = "pyflow"
    AZURE_POSTGRES_PORT: int = 5432
    # Set to "true" if SSL is required (default for Azure)
    AZURE_POSTGRES_SSL_MODE: str = "require"

    # ── AWS RDS for PostgreSQL ──────────────────────────────────────
    # Set these along with DB_MODE=aws to connect to an RDS instance.
    AWS_RDS_HOST: str = ""
    AWS_RDS_PORT: int = 5432
    AWS_RDS_USER: str = ""
    AWS_RDS_PASSWORD: str = ""
    AWS_RDS_DATABASE: str = "pyflow"
    AWS_RDS_SSL_MODE: str = "require"

    # ── Auth ────────────────────────────────────────────────────────
    JWT_ACCESS_SECRET: str = "changeme-access-secret"
    JWT_REFRESH_SECRET: str = "changeme-refresh-secret"
    JWT_ACCESS_EXPIRY_MINUTES: int = 15
    JWT_REFRESH_EXPIRY_DAYS: int = 7

    # ── AI ──────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── File storage ────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10_485_760
    ALLOWED_MIME_TYPES: str = "image/jpeg,image/png,image/gif,image/webp,image/svg+xml"
    STORAGE_PROVIDER: str = "local"

    # ── S3 (if STORAGE_PROVIDER=s3) ─────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_STORAGE_BUCKET_NAME: str = ""
    AWS_S3_REGION: str = "us-east-1"

    # ── Redis ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Email ───────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@pyflow.dev"

    model_config = {"env_file": [".env", "../.env"], "env_file_encoding": "utf-8", "extra": "ignore"}

    # ── Derived helpers ─────────────────────────────────────────────

    @property
    def allowed_mime_types_list(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_MIME_TYPES.split(",") if t.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def _build_supabase_url(self, scheme: str = "postgresql+asyncpg") -> str | None:
        """Derive a direct Postgres URL from Supabase project credentials.

        Supabase exposes a connection-pooler endpoint at:
            <scheme>://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
        """
        if not self.SUPABASE_URL or not self.SUPABASE_DB_PASSWORD:
            return None
        host = urlparse(self.SUPABASE_URL).hostname or ""
        ref = host.split(".")[0]
        return (
            f"{scheme}://postgres.{ref}:{self.SUPABASE_DB_PASSWORD}"
            f"@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )

    def _build_azure_url(self, scheme: str = "postgresql+asyncpg") -> str | None:
        """Build a connection string for Azure Database for PostgreSQL."""
        if not self.AZURE_POSTGRES_HOST or not self.AZURE_POSTGRES_USER or not self.AZURE_POSTGRES_PASSWORD:
            return None
        ssl = self.AZURE_POSTGRES_SSL_MODE
        return (
            f"{scheme}://{self.AZURE_POSTGRES_USER}:{self.AZURE_POSTGRES_PASSWORD}"
            f"@{self.AZURE_POSTGRES_HOST}:{self.AZURE_POSTGRES_PORT}/{self.AZURE_POSTGRES_DATABASE}"
            f"?sslmode={ssl}"
        )

    def _build_aws_url(self, scheme: str = "postgresql+asyncpg") -> str | None:
        """Build a connection string for AWS RDS PostgreSQL."""
        if not self.AWS_RDS_HOST or not self.AWS_RDS_USER or not self.AWS_RDS_PASSWORD:
            return None
        ssl = self.AWS_RDS_SSL_MODE
        return (
            f"{scheme}://{self.AWS_RDS_USER}:{self.AWS_RDS_PASSWORD}"
            f"@{self.AWS_RDS_HOST}:{self.AWS_RDS_PORT}/{self.AWS_RDS_DATABASE}"
            f"?sslmode={ssl}"
        )

    def _resolve_url(self, scheme_async: str, scheme_sync: str, is_async: bool = True) -> str:
        """Resolve the effective DB URL for the current DB_MODE."""
        scheme = scheme_async if is_async else scheme_sync
        builders = {
            "supabase": self._build_supabase_url,
            "azure": self._build_azure_url,
            "aws": self._build_aws_url,
        }
        builder = builders.get(self.DB_MODE)
        if builder:
            url = builder(scheme)
            if url:
                return url
        return self.DATABASE_URL if is_async else self.DATABASE_URL_SYNC

    @property
    def effective_database_url(self) -> str:
        """Active async database URL based on DB_MODE."""
        return self._resolve_url("postgresql+asyncpg", "postgresql", is_async=True)

    @property
    def effective_database_url_sync(self) -> str:
        """Active sync database URL based on DB_MODE."""
        return self._resolve_url("postgresql+asyncpg", "postgresql", is_async=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
