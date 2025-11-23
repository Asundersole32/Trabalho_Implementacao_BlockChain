# Mini Blockchain App com Docker

Uma aplicação completa de blockchain usando Ethereum (Ganache) containerizada com Docker.

## 🚀 Como executar

### Pré-requisitos
- Docker
- Docker Compose

### Execução

```bash
# Clonar ou criar a estrutura de arquivos
mkdir blockchain-app
cd blockchain-app

# Colocar todos os arquivos na pasta

# Executar com Docker Compose
docker-compose up --build

# Ou em segundo plano
docker-compose up -d

### Comandos Úteis

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Executar comandos no container
docker-compose exec blockchain-app python app.py

# Ver volumes
docker volume ls
