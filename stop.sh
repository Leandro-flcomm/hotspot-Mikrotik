#!/bin/bash

echo "🛑 Parando Hotspot Manager..."

# Parar e remover containers
docker-compose down

echo "✅ Aplicação parada com sucesso!"
