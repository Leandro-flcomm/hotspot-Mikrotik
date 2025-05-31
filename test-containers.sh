#!/bin/bash

echo "🧪 Testando comunicação entre containers..."

# Verificar se containers estão rodando
echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "🌐 Testando resolução DNS entre containers..."

# Testar se frontend consegue resolver backend
echo "Frontend -> Backend DNS:"
docker exec hotspot-frontend sh -c "nslookup hotspot-backend" || echo " ❌ Problema de DNS"

echo ""
echo "🔗 Testando conectividade HTTP..."

# Testar conectividade HTTP do frontend para backend
echo "Frontend -> Backend HTTP:"
docker exec hotspot-frontend sh -c "curl -v http://hotspot-backend:5000/api/health" || echo " ❌ Problema de conectividade HTTP"

echo ""
echo "📋 Logs recentes do backend:"
docker-compose logs --tail=20 backend

echo ""
echo "📋 Logs recentes do frontend:"
docker-compose logs --tail=20 frontend

echo ""
echo "🔍 Informações da rede Docker:"
docker network ls
docker network inspect hotspot_hotspot-network

echo ""
echo "🔧 Variáveis de ambiente no frontend:"
docker exec hotspot-frontend sh -c "env | grep NEXT_PUBLIC"

echo ""
echo "🔧 Variáveis de ambiente no backend:"
docker exec hotspot-backend sh -c "env | grep FLASK"
