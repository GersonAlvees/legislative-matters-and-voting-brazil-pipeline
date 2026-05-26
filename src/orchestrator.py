import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path,
# permitindo rodar tanto "python src/orchestrator.py" quanto "python -m src.orchestrator"
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.ingestion.config import INGESTION_YEAR
from src.ingestion.senadores.injestion_of_senators import injetion_of_senators
from src.ingestion.materias.injestion_of_matter import injetion_of_matter
from src.ingestion.votos.injestion_of_votes import ingerir_votos_ano

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("orchestrator")

# Etapas disponíveis na ordem de execução
STEPS = ("senadores", "materias", "votos")


def run_bronze(year: int = INGESTION_YEAR, only: str | None = None):
    steps = (only,) if only else STEPS
    start = datetime.now(timezone.utc)

    log.info("=" * 60)
    log.info(f"Início da ingestão bronze | ano={year} | etapas={steps}")
    log.info("=" * 60)

    results: dict[str, str] = {}

    for step in steps:
        log.info(f"▶ Iniciando etapa: {step}")
        step_start = datetime.now(timezone.utc)

        try:
            if step == "senadores":
                injetion_of_senators()

            elif step == "materias":
                injetion_of_matter(year=year)

            elif step == "votos":
                ingerir_votos_ano(ano=year)

            else:
                log.warning(f"Etapa desconhecida: {step}, pulando")
                results[step] = "IGNORADA"
                continue

            elapsed = (datetime.now(timezone.utc) - step_start).total_seconds()
            results[step] = f"OK ({elapsed:.1f}s)"
            log.info(f"✔ {step} concluída em {elapsed:.1f}s")

        except Exception:
            elapsed = (datetime.now(timezone.utc) - step_start).total_seconds()
            results[step] = f"ERRO ({elapsed:.1f}s)"
            log.exception(f"✖ {step} falhou após {elapsed:.1f}s")

    total = (datetime.now(timezone.utc) - start).total_seconds()

    log.info("=" * 60)
    log.info(f"Ingestão bronze finalizada em {total:.1f}s")
    for step, status in results.items():
        log.info(f"  {step}: {status}")
    log.info("=" * 60)

    # Retorna código de saída 1 se alguma etapa falhou
    if any("ERRO" in s for s in results.values()):
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador da ingestão bronze — Senado Federal",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=INGESTION_YEAR,
        help=f"Ano da legislatura para ingestão (default: {INGESTION_YEAR})",
    )
    parser.add_argument(
        "--only",
        choices=STEPS,
        default=None,
        help="Executa apenas uma etapa específica",
    )
    args = parser.parse_args()

    exit_code = run_bronze(year=args.year, only=args.only)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
