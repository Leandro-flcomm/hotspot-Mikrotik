#!/bin/bash

echo "🌐 Configurando IP público para comunicação..."

# Solicitar o IP público do usuário
read -p "Digite o IP público do backend: " PUBLIC_IP

if [ -z "$PUBLIC_IP" ]; then
    echo "❌ IP público não fornecido!"
    exit 1
fi

echo "📝 Configurando docker-compose.yml com IP público: $PUBLIC_IP"

# Backup do docker-compose.yml atual
cp docker-compose.yml docker-compose.yml.backup

# Substituir a variável de ambiente no docker-compose.yml
sed -i "s/SEU_IP_PUBLICO/$PUBLIC_IP/g" docker-compose.yml

echo "✅ Configuração atualizada!"
echo "🔄 Reiniciando containers..."

# Parar containers
docker-compose down

# Reconstruir e iniciar
docker-compose up -d --build

echo "⏳ Aguardando containers iniciarem..."
sleep 10

echo "🧪 Testando comunicação..."

# Testar backend diretamente
echo "📡 Testando backend em $PUBLIC_IP:5000..."
curl -s http://$PUBLIC_IP:5000/api/health | jq . || echo "❌ Backend não acessível via IP público"

# Testar frontend
echo "🖥️ Testando frontend em localhost:3000..."
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend acessível" || echo "❌ Frontend com problemas"

echo "🎉 Configuração concluída!"
echo "📋 Resumo:"
echo "   - Backend: http://$PUBLIC_IP:5000"
echo "   - Frontend: http://localhost:3000"
echo "   - Frontend configurado para usar: http://$PUBLIC_IP:5000"
