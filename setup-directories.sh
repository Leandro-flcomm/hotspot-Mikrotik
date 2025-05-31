#!/bin/bash

echo "📁 Criando estrutura de diretórios necessária..."

# Criar diretórios principais
mkdir -p logs instance static/css static/js templates

# Criar arquivos .keep para garantir que os diretórios existam
touch static/css/.keep
touch static/js/.keep
touch templates/.keep
touch logs/.keep
touch instance/.keep

# Definir permissões
chmod -R 755 logs instance static templates

echo "✅ Diretórios criados com sucesso!"
