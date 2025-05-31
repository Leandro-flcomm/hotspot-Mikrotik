#!/bin/bash

echo "🚀 Iniciando Hotspot Manager em modo desenvolvimento..."

# Executar script para criar diretórios
echo "📁 Configurando diretórios..."
chmod +x setup-directories.sh
./setup-directories.sh

# Configurar permissões
echo "🔐 Configurando permissões..."
chmod 755 logs instance
chmod +x start.sh test-connection.sh

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Limpar cache do Docker para forçar reconstrução
echo "🧹 Limpando cache do Docker..."
docker system prune -f
docker-compose rm -f

# Construir e iniciar containers
echo "🔨 Construindo e iniciando containers..."
docker-compose build --no-cache
docker-compose up -d

# Aguardar containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 20

# Verificar status
echo "📊 Verificando status dos containers..."
docker-compose ps

# Verificar se os containers estão rodando
if [ "$(docker-compose ps -q)" ]; then
    echo "✅ Containers estão rodando!"
    
    # Verificar logs do backend
    echo "📋 Logs do backend:"
    docker-compose logs backend --tail=20
    
    # Verificar logs do frontend
    echo "📋 Logs do frontend:"
    docker-compose logs frontend --tail=20
    
    # Verificar conectividade
    echo "🔍 Testando conectividade..."
    sleep 5
    
    echo "Backend: http://localhost:5000/api/health"
    curl -f http://localhost:5000/api/health 2>/dev/null && echo " ✅ Backend OK" || echo " ❌ Backend com problemas"
    
    echo "Frontend: http://localhost:3000"
    curl -f http://localhost:3000 2>/dev/null && echo " ✅ Frontend OK" || echo " ❌ Frontend com problemas"
else
    echo "❌ Erro: Containers não estão rodando!"
    echo "📋 Logs de erro:"
    docker-compose logs
fi

echo ""
echo "🎉 Processo de inicialização concluído!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo "📊 Health Check: http://localhost:5000/api/health"
echo ""
echo "Para ver logs em tempo real:"
echo "docker-compose logs -f backend"
echo "docker-compose logs -f frontend"
echo ""
echo "Para parar a aplicação:"
echo "docker-compose down"
