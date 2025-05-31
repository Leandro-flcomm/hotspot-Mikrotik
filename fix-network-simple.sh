#!/bin/bash

echo "🔧 Corrigindo problemas de rede entre containers..."

# Parar todos os containers
echo "🛑 Parando containers..."
docker-compose down

# Limpar redes Docker órfãs
echo "🧹 Limpando redes Docker..."
docker network prune -f

# Iniciar containers
echo "🚀 Iniciando containers..."
docker-compose up -d

# Aguardar containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Verificar status
echo "📊 Status dos containers:"
docker-compose ps

echo "🎉 Correção de rede concluída!"
echo ""
echo "📱 URLs de acesso:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "Health Check: http://localhost:5000/api/health"
