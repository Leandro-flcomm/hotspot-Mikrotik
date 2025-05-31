#!/bin/bash

echo "🧪 Testando conexão com IP público..."

# Ler IP público do docker-compose.yml
PUBLIC_IP=$(grep "NEXT_PUBLIC_API_URL" docker-compose.yml | cut -d'=' -f2 | sed 's/http:\/\///' | sed 's/:5000//')

if [ -z "$PUBLIC_IP" ]; then
    echo "❌ IP público não encontrado no docker-compose.yml"
    exit 1
fi

echo "📡 Testando backend em: $PUBLIC_IP:5000"

# Testar endpoints
echo "🔍 Testando /api/health..."
curl -s http://$PUBLIC_IP:5000/api/health | jq .

echo "🔍 Testando /api/test..."
curl -s http://$PUBLIC_IP:5000/api/test | jq .

echo "🔍 Testando /api/profiles..."
curl -s http://$PUBLIC_IP:5000/api/profiles | jq .

echo "🖥️ Testando frontend..."
echo "Acesse: http://localhost:3000"
echo "O frontend deve conseguir se comunicar com: http://$PUBLIC_IP:5000"
