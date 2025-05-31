#!/bin/bash

echo "🔍 Script de Debug - Hotspot Manager"
echo "=================================="

echo "📊 Status dos containers:"
docker-compose ps

echo ""
echo "📋 Logs do Backend (últimas 50 linhas):"
docker-compose logs backend --tail=50

echo ""
echo "📋 Logs do Frontend (últimas 50 linhas):"
docker-compose logs frontend --tail=50

echo ""
echo "🔍 Testando conectividade:"
echo "Backend Health Check:"
curl -v http://localhost:5000/api/health 2>&1 || echo "❌ Backend não acessível"

echo ""
echo "Frontend:"
curl -I http://localhost:3000 2>&1 || echo "❌ Frontend não acessível"

echo ""
echo "🐳 Informações dos containers:"
docker inspect hotspot-backend --format='{{.State.Status}}' 2>/dev/null && echo "Backend: Rodando" || echo "Backend: Parado"
docker inspect hotspot-frontend --format='{{.State.Status}}' 2>/dev/null && echo "Frontend: Rodando" || echo "Frontend: Parado"

echo ""
echo "📁 Estrutura de diretórios:"
ls -la logs/ instance/ 2>/dev/null || echo "Diretórios não encontrados"
