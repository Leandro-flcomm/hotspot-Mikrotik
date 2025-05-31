#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Configurando componentes UI para o projeto...${NC}"

# Verificar se o npm está instalado
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm não está instalado. Por favor, instale o Node.js e npm primeiro.${NC}"
    exit 1
fi

# Criar diretórios necessários
echo -e "${GREEN}📁 Criando diretórios...${NC}"
mkdir -p components/ui
mkdir -p lib

# Instalar dependências
echo -e "${GREEN}📦 Instalando dependências...${NC}"
npm install @radix-ui/react-icons lucide-react tailwindcss-animate class-variance-authority clsx tailwind-merge
npm install @radix-ui/react-alert-dialog @radix-ui/react-avatar @radix-ui/react-checkbox @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-label @radix-ui/react-popover @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-slot @radix-ui/react-tabs @radix-ui/react-toast

# Copiar componentes UI
echo -e "${GREEN}📄 Configurando componentes UI...${NC}"

# Criar utils.ts
cat > lib/utils.ts << 'EOL'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
 
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOL

echo -e "${GREEN}✅ Configuração concluída com sucesso!${NC}"
echo -e "${YELLOW}ℹ️ Agora você pode executar o Docker novamente.${NC}"
