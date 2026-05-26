# Configurações centralizadas para os scripts de ingestão
# Carrega variáveis do arquivo .env na raiz do projeto

import os
from pathlib import Path
from dotenv import load_dotenv

# Localiza o .env a partir da raiz do projeto (3 níveis acima deste arquivo)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"

load_dotenv(_ENV_FILE)

STORAGE_SOURCE: str = os.getenv("STORAGE_SOURCE", "local")
BRONZE_PATH: Path = Path(os.getenv("BRONZE_PATH", "bronze"))
S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "legislative-matters-and-voting-brazil-pipeline")
SENADO_API_BASE_URL: str = os.getenv("SENADO_API_BASE_URL", "https://legis.senado.leg.br/dadosabertos")
INGESTION_YEAR: int = int(os.getenv("INGESTION_YEAR", "2025"))
API_REQUEST_TIMEOUT: int = int(os.getenv("API_REQUEST_TIMEOUT", "30"))
API_RETRY_PAUSE: float = float(os.getenv("API_RETRY_PAUSE", "0.3"))

HEADERS: dict = {"Accept": "application/json"}
