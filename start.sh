#!/bin/bash

echo "🚀 Iniciando aplicação Hotspot Manager..."

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Verificar se docker-compose está disponível
if command -v docker-compose > /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker > /dev/null 2>&1 && docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose."
    exit 1
fi

# Criar diretórios necessários no host
echo "📁 Criando diretórios necessários..."
mkdir -p logs instance static/css static/js templates

# Definir permissões corretas
echo "🔐 Configurando permissões..."
chmod 755 logs instance static
chmod -R 755 static 2>/dev/null || true

# Parar containers existentes
echo "🛑 Parando containers existentes..."
$COMPOSE_CMD down

# Construir e iniciar containers
echo "🔨 Construindo e iniciando containers..."
$COMPOSE_CMD up --build -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Verificar status dos containers
echo "📊 Status dos containers:"
$COMPOSE_CMD ps

# Verificar logs do backend
echo "📋 Logs do backend (últimas 20 linhas):"
$COMPOSE_CMD logs --tail=20 backend

# Verificar logs do frontend
echo "📋 Logs do frontend (últimas 10 linhas):"
$COMPOSE_CMD logs --tail=10 frontend

# Verificar health check
echo "🏥 Verificando health check..."
sleep 5
curl -f http://localhost:5000/api/health 2>/dev/null && echo "✅ Backend está saudável" || echo "❌ Backend não está respondendo"

echo ""
echo "🎉 Aplicação iniciada!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:5000"
echo "🏥 Health Check: http://localhost:5000/api/health"
echo ""
echo "👤 Login padrão:"
echo "   Usuário: admin"
echo "   Senha: admin"
echo ""
echo "📝 Para ver logs em tempo real:"
echo "   $COMPOSE_CMD logs -f"
echo ""
echo "🛑 Para parar a aplicação:"
echo "   $COMPOSE_CMD down"
