#!/bin/bash

echo "🔧 Corrigindo problemas de rede entre containers..."

# Parar todos os containers
echo "🛑 Parando containers..."
docker-compose down

# Limpar redes Docker órfãs
echo "🧹 Limpando redes Docker órfãs..."
docker network prune -f

# Remover banco de dados corrompido
echo "🗑️ Removendo banco de dados corrompido (se existir)..."
sudo rm -f ./instance/mikrotik_manager.db*

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p logs instance static/css static/js templates
chmod -R 755 logs instance static

# Reconstruir containers
echo "🔨 Reconstruindo containers..."
docker-compose build --no-cache

# Iniciar containers
echo "🚀 Iniciando containers..."
docker-compose up -d

# Aguardar inicialização
echo "⏳ Aguardando inicialização dos containers..."
sleep 30

# Verificar status
echo "📊 Status dos containers:"
docker-compose ps

# Testar conectividade
echo "🔍 Testando conectividade..."
echo "Backend (localhost:5000):"
if curl -s -f http://localhost:5000/api/health > /dev/null; then
    echo " ✅ Backend respondendo"
else
    echo " ❌ Backend com problemas"
fi

echo "Frontend (localhost:3000):"
if curl -s -f http://localhost:3000 > /dev/null; then
    echo " ✅ Frontend respondendo"
else
    echo " ❌ Frontend com problemas"
fi

echo "🔗 Testando comunicação interna entre containers..."
docker exec hotspot-frontend curl -s http://hotspot-backend:5000/api/health || echo " ❌ Problema na comunicação interna"

echo "📋 Logs do frontend:"
docker-compose logs --tail=10 frontend

echo "📋 Logs do backend:"
docker-compose logs --tail=10 backend

echo ""
echo "🎉 Processo concluído!"
echo "Se ainda houver problemas, execute: ./test-containers.sh"
