# Configuração Docker para HotspotLeandro

## Requisitos

- Docker
- Docker Compose

## Arquivos de Configuração

- `Dockerfile.backend`: Configuração para o container do backend Flask
- `Dockerfile.frontend`: Configuração para o container do frontend Next.js
- `docker-compose.yml`: Orquestração dos serviços
- `.env`: Variáveis de ambiente (credenciais MikroTik, etc.)

## Scripts Utilitários

- `start.sh`: Inicia todos os serviços
- `stop.sh`: Para todos os serviços
- `fix-docker-permissions.sh`: Corrige permissões do Docker
- `troubleshoot.sh`: Diagnóstico de problemas
- `generate-lock.sh`: Gera package-lock.json (se necessário)

## Instruções de Uso

### Primeira Execução

1. Configure as variáveis de ambiente:
   \`\`\`bash
   cp .env.example .env
   nano .env  # Edite com suas credenciais
   \`\`\`

2. Corrija as permissões do Docker (se necessário):
   \`\`\`bash
   chmod +x *.sh
   ./fix-docker-permissions.sh
   # Faça logout e login novamente
   \`\`\`

3. Inicie os serviços:
   \`\`\`bash
   ./start.sh
   \`\`\`

### Comandos Úteis

- **Ver logs em tempo real**:
  \`\`\`bash
  docker-compose logs -f
  \`\`\`

- **Reiniciar serviços**:
  \`\`\`bash
  docker-compose restart
  \`\`\`

- **Parar todos os serviços**:
  \`\`\`bash
  ./stop.sh
  \`\`\`

- **Diagnóstico de problemas**:
  \`\`\`bash
  ./troubleshoot.sh
  \`\`\`

## Acessando a Aplicação

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Credenciais padrão**: admin/admin

## Solução de Problemas

Se encontrar problemas com permissões do Docker:

\`\`\`bash
./fix-docker-permissions.sh
# Faça logout e login novamente
\`\`\`

Se precisar gerar um package-lock.json:

\`\`\`bash
./generate-lock.sh
