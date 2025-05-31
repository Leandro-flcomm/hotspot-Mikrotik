# Configuração para Desenvolvimento Local

## Pré-requisitos

1. **Python 3.8+** instalado
2. **Node.js 18+** instalado
3. **MikroTik RouterOS** configurado

## Configuração do Backend (Flask)

1. **Instalar dependências:**
   \`\`\`bash
   cd backend
   pip install -r requirements.txt
   \`\`\`

2. **Configurar variáveis de ambiente:**
   \`\`\`bash
   export MIKROTIK_HOST=10.10.0.2
   export MIKROTIK_USER=API1
   export MIKROTIK_PASSWORD=Blocked@@99
   \`\`\`

3. **Executar o backend:**
   \`\`\`bash
   python app.py
   \`\`\`
   
   O backend estará disponível em: `http://localhost:5000`

## Configuração do Frontend (Next.js)

1. **Instalar dependências:**
   \`\`\`bash
   npm install
   \`\`\`

2. **Criar arquivo .env.local:**
   \`\`\`env
   NEXT_PUBLIC_API_URL=http://localhost:5000
   \`\`\`

3. **Executar o frontend:**
   \`\`\`bash
   npm run dev
   \`\`\`
   
   O frontend estará disponível em: `http://localhost:3000`

## Login Padrão

- **Usuário:** admin
- **Senha:** admin

## Estrutura de Desenvolvimento

\`\`\`
projeto/
├── backend/           # API Flask
│   ├── app.py        # Aplicação principal
│   ├── logger.py     # Sistema de logs
│   └── instance/     # Banco de dados
├── frontend/         # Interface Next.js
│   ├── app/          # Páginas da aplicação
│   └── components/   # Componentes React
└── docker-compose.yml # Configuração Docker
\`\`\`

## Comandos Úteis

### Backend
\`\`\`bash
# Executar em modo debug
python app.py --debug

# Ver logs
tail -f logs/debug.log
\`\`\`

### Frontend
\`\`\`bash
# Executar em modo desenvolvimento
npm run dev

# Build para produção
npm run build
\`\`\`

## Troubleshooting

### API não conecta
- Verifique se o backend está rodando na porta 5000
- Confirme se a variável `NEXT_PUBLIC_API_URL` está configurada
- Verifique os logs do backend em `logs/debug.log`

### MikroTik não conecta
- Confirme as credenciais do MikroTik
- Verifique se a API está habilitada no RouterOS
- Teste a conectividade de rede
