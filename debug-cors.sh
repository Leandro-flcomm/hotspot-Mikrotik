#!/bin/bash

echo "🔍 Verificando problemas de CORS entre containers..."

# Verificar se os containers estão rodando
echo "📊 Status dos containers:"
docker-compose ps

# Verificar rede Docker
echo "🌐 Redes Docker:"
docker network ls
echo "🔗 Detalhes da rede hotspot-network:"
docker network inspect hotspot-network

# Testar conectividade entre containers
echo "🧪 Testando conectividade entre containers:"
docker exec hotspot-frontend curl -v http://hotspot-backend:5000/api/health

# Verificar logs do backend para problemas de CORS
echo "📋 Logs do backend (procurando por CORS):"
docker-compose logs backend | grep -i cors

# Verificar logs do frontend para problemas de conexão
echo "📋 Logs do frontend (procurando por erros de conexão):"
docker-compose logs frontend | grep -i error

# Testar API diretamente
echo "🔌 Testando API diretamente:"
curl -v -H "Origin: http://localhost:3000" http://localhost:5000/api/health

echo "✅ Verificação concluída!"
