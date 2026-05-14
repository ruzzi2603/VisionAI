# Política de Segurança

## Reportando vulnerabilidades
Se você encontrar uma vulnerabilidade, por favor reporte-a com segurança para os mantenedores do projeto.

### Recomendações
- Não abra uma issue pública para vulnerabilidades graves.
- Use o canal privado definido pelo repositório, ou envie e-mail para o mantenedor se disponível.
- Inclua detalhes básicos sobre o problema, impacto e passos para reproduzir.

## Segurança de dependências
- Monitore dependências do `backend/requirements.txt` e `frontend/package.json`.
- Atualize bibliotecas críticas de segurança assim que possível.
- Valide pacotes antes de publicar ou adicionar novas dependências.

## Boas práticas do projeto
- Não armazene chaves secretas em código-fonte.
- Use variáveis de ambiente em `.env` para tokens e senhas.
- Proteja endpoints sensíveis com autenticação e permissões.

## Contato
Caso não exista um canal privado configurado, abra uma issue com a tag `security` e marque os mantenedores.
