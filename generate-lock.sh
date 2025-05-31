#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 Gerando package-lock.json...${NC}"

# Verificar se package.json existe
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Arquivo package.json não encontrado!${NC}"
    exit 1
fi

# Instalar dependências para gerar package-lock.json
npm install --package-lock-only

if [ -f "package-lock.json" ]; then
    echo -e "${GREEN}✅ package-lock.json gerado com sucesso!${NC}"
else
    echo -e "${RED}❌ Falha ao gerar package-lock.json${NC}"
    exit 1
fi

echo -e "${YELLOW}ℹ️ Agora você pode usar 'npm ci' no Dockerfile${NC}"