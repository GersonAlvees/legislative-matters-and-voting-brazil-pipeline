FROM python:3.12-slim

# Evita geração de .pyc e habilita logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências primeiro (aproveita cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do projeto
COPY src/ src/

# Cria diretório bronze para armazenamento local
RUN mkdir -p bronze/materias bronze/senadores bronze/votos

CMD ["python", "-m", "src.ingestion"]
