FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .
COPY .env .

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 blockchain-user
USER blockchain-user

# Comando para executar a aplicação
CMD ["python", "app.py"]