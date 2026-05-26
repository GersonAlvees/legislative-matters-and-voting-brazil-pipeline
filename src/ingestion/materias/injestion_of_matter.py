import requests, json, boto3
from datetime import datetime, timezone

from src.ingestion.config import (
    STORAGE_SOURCE,
    BRONZE_PATH,
    S3_BUCKET_NAME,
    SENADO_API_BASE_URL,
    INGESTION_YEAR,
    HEADERS,
)

def injetion_of_matter(year: int = INGESTION_YEAR, source: str = STORAGE_SOURCE):
    url = f"{SENADO_API_BASE_URL}/materia/pesquisa/lista?ano={year}"
    r = requests.get(url, headers=HEADERS)
    payload = r.json()

    # Envelope com timestamp de ingestão
    bronze_record = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source_url": url,
        "data": payload,
    }

    # se o save for local
    if source == "local":
        dest = BRONZE_PATH / "materias" / f"{year}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(bronze_record, ensure_ascii=False), encoding="utf-8")
    # se o save for s3
    elif source == "s3":
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"bronze/materias/{year}.json",
            Body=json.dumps(bronze_record, ensure_ascii=False)
        )
