#!/bin/bash

echo "🗑️ Limpando banco de dados corrompido..."

# Parar containers
docker-compose down

# Remover arquivos de banco corrompidos
sudo rm -f ./instance/mikrotik_manager.db*
sudo rm -f ./instance/*.corrupted.*

# Recriar diretório instance
sudo mkdir -p ./instance
sudo chmod 755 ./instance

echo "✅ Banco de dados limpo!"
echo "🚀 Reiniciando aplicação..."

# Reiniciar aplicação
./start-dev.sh
