#!/bin/bash

echo "🔄 Reiniciando containers para aplicar correções..."

# Parar containers
echo "⏹️ Parando containers..."
docker-compose down

# Limpar cache do Docker
echo "🧹 Limpando cache..."
docker system prune -f

# Rebuild e restart
echo "🔨 Reconstruindo e iniciando containers..."
docker-compose up --build -d

# Aguardar containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Verificar status
echo "📊 Status dos containers:"
docker-compose ps

# Testar conectividade
echo "🔍 Testando conectividade..."
echo "Backend (localhost:5000):"
curl -s http://localhost:5000/api/health || echo " ❌ Backend não responde"

echo "Frontend (localhost:3000):"
curl -s -I http://localhost:3000 | head -1 || echo " ❌ Frontend não responde"

echo "✅ Reinicialização completa!"
