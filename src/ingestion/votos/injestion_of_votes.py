import requests, json, time, logging
from datetime import datetime, timezone

from src.ingestion.config import (
    SENADO_API_BASE_URL,
    BRONZE_PATH,
    HEADERS,
    API_REQUEST_TIMEOUT,
    API_RETRY_PAUSE,
    INGESTION_YEAR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _get(endpoint: str, params: dict = None) -> dict:
    # GET com retry simples (3 tentativas, backoff 2s)
    url = SENADO_API_BASE_URL + endpoint
    for tentativa in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=API_REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning(f"Tentativa {tentativa + 1}/3 falhou: {e}")
            if tentativa < 2:
                time.sleep(2 ** tentativa)
    raise RuntimeError(f"Endpoint indisponível após 3 tentativas: {url}")


def ingerir_ids_materias(ano: int) -> list[str]:
    # Busca todos os IDs de matérias do ano, sendo o ponto de entrada para os votos
    log.info(f"Buscando matérias de {ano}...")
    payload = _get("/materia/pesquisa/lista", params={"ano": ano, "v": 7})

    materias = (
        payload
        .get("PesquisaBasicaMateria", {})
        .get("Materias", {})
        .get("Materia", [])
    )
    if isinstance(materias, dict):
        materias = [materias]

    ids = [m["CodigoMateria"] for m in materias if "CodigoMateria" in m]
    log.info(f"{len(ids)} matérias encontradas em {ano}")
    return ids


def ingerir_votos_materia(id_materia: str) -> bool:
    # Salva o JSON bruto de votações de uma matéria
    # Retorna True se salvou, False se a matéria não tem votações nominais
    destino = BRONZE_PATH / "votos" / f"{id_materia}.json"

    # pula se já foi baixado
    if destino.exists():
        log.debug(f"[{id_materia}] já existe, pulando")
        return True

    try:
        payload = _get(f"/votacao/materia/{id_materia}")
    except RuntimeError:
        log.error(f"[{id_materia}] falhou, registrando em erros")
        _registrar_erro(id_materia)
        return False

    # Matérias sem votações nominais retornam payload vazio
    votacoes = (
        payload
        .get("VotacaoMateria", {})
        .get("Materia", {})
        .get("Votacoes", {})
        .get("Votacao")
    )
    if not votacoes:
        log.debug(f"[{id_materia}] sem votações nominais, ignorando")
        return False

    # Envelope com timestamp de ingestão
    bronze_record = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "source_url": f"{SENADO_API_BASE_URL}/votacao/materia/{id_materia}",
        "data": payload,
    }

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(bronze_record, ensure_ascii=False), encoding="utf-8")
    return True


def _registrar_erro(id_materia: str):
    # Mantém um arquivo de IDs que falharam para reprocessar depois
    erros = BRONZE_PATH / "votos" / "_erros.txt"
    erros.parent.mkdir(parents=True, exist_ok=True)
    with erros.open("a") as f:
        f.write(f"{id_materia}\n")


def ingerir_votos_ano(ano: int = INGESTION_YEAR, pausa_segundos: float = API_RETRY_PAUSE):
    # Orquestra a ingestão completa de votos de um ano
    # A pausa evita sobrecarga na API pública do Senado
    ids = ingerir_ids_materias(ano)

    salvos   = 0
    sem_voto = 0
    erros    = 0

    for i, id_materia in enumerate(ids, 1):
        ok = ingerir_votos_materia(id_materia)
        if ok:
            salvos += 1
        else:
            sem_voto += 1

        if i % 50 == 0:
            log.info(f"Progresso: {i}/{len(ids)} | salvos={salvos} sem_voto={sem_voto}")

        time.sleep(pausa_segundos)

    log.info(
        f"Ingestão {ano} concluída — "
        f"salvos={salvos}, sem_voto_nominal={sem_voto}, erros={erros}"
    )
