#!/bin/bash

echo "🔍 Testando conectividade entre containers..."

# Testar se o backend está respondendo
echo "1. Testando backend diretamente..."
curl -f http://localhost:5000/api/health && echo " ✅ Backend OK" || echo " ❌ Backend com problemas"

# Testar conectividade interna entre containers
echo "2. Testando conectividade interna..."
docker-compose exec frontend curl -f http://backend:5000/api/health && echo " ✅ Conectividade interna OK" || echo " ❌ Problema na rede interna"

# Verificar variáveis de ambiente
echo "3. Verificando variáveis de ambiente do frontend..."
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Verificar rede Docker
echo "4. Verificando rede Docker..."
docker network ls | grep hotspot

# Verificar containers na rede
echo "5. Containers na rede hotspot-network:"
docker network inspect hotspotleandro_hotspot-network | grep -A 10 "Containers"

echo ""
echo "📊 Status dos containers:"
docker-compose ps
