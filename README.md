# replicar-meta-clickup

> Skill para [Claude Code](https://claude.com/claude-code) que cria o **ambiente de Metas (Goals)** de um projeto no ClickUp da Exos — 1 key result automático por fase, linkado aos marcos (milestones), dentro da pasta de Goals do cliente.

[![Skill: Claude Code](https://img.shields.io/badge/Skill-Claude%20Code-cc785c.svg)](https://claude.com/claude-code)
[![Platform: ClickUp](https://img.shields.io/badge/Platform-ClickUp-7B68EE.svg)](https://clickup.com)

## O que faz

Um gestor de projetos sênior especializado na criação de metas (Goals) no ClickUp da Exos, espelhando uma meta-modelo. A skill:

- **Cria 1 key result automático por fase** — `unit=tasks`, linkado aos task_ids dos MARCOS (milestones, `custom_item_id==1`) daquela fase no destino
- **Progresso calculado automaticamente** — pela conclusão dos marcos via ClickUp Goals
- **Nomeia a meta pelo sufixo do projeto** — seguindo a nomenclatura padrão da Exos
- **Pasta de Goals do cliente** — cria a meta dentro da pasta correta; migra da raiz se a pasta for criada depois (idempotente)
- **API-first** — Goals não estão no MCP; tudo via REST API direta
- **Idempotente** — pula meta/KR que já existem pelo nome; dry-run por padrão

## Fluxo de uso

```
1. Informar meta-modelo (pretty_id da URL /goals/NN) + sufixo do projeto
2. Skill descobre os marcos por fase (discover) → gera plano_meta.json editável
3. Dry-run: skill mostra o que será criado — confirmar
4. Execute --apply: cria a meta + KRs automáticos no ClickUp
```

> A skill é invocada normalmente logo após a skill `duplicar-projeto-clickup` — os marcos precisam existir antes de criar os KRs.

## Comandos do engine

```bash
TOKEN=$(security find-generic-password -s clickup-exos-api -w)
SK=~/.claude/skills/replicar-meta-clickup/scripts

# 1) Descoberta (read-only) → gera plano_meta.json
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py discover \
  --config config_<projeto>.json --out plano_meta.json

# 2) Dry-run (não escreve nada)
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py execute \
  --plan plano_meta.json

# 3) Aplicar
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py execute \
  --plan plano_meta.json --apply
```

O token vem do **Keychain macOS** (serviço `clickup-exos-api`) — nunca é hard-coded.

## Bloco `goal` no config

Reutiliza o mesmo `config_<projeto>.json` da skill `duplicar-projeto-clickup`. Basta adicionar o bloco `goal`:

```jsonc
"goal": {
  "enabled": true,
  "source_goal": "23",
  "folder_name": "Daniela Moleiro",
  "name": "[DM][LB][POS][JUL][26]",
  "description": "Planejamento Estratégico: ",
  "color": "#757380",
  "due_date": "2026-07-31",
  "owners": [54927970],
  "link": "milestones",
  "only_phases_with_tasks": true
}
```

## Estrutura do repositório

```
replicar-meta-clickup/
├── SKILL.md                        # Ponto de entrada (Claude Code lê este arquivo)
├── README.md                       # Este arquivo
├── PROMPT.md                       # Prompt-modelo para disparar a skill
├── REFERENCE.md                    # Endpoints de Goals, owners, metas-modelo, pastas
└── scripts/
    ├── duplicar_meta.py            # Engine API-first (discover + execute)
    └── config_meta_exemplo.json    # Config exemplo para [DM][LB][POS][JUL][26]
```

## Instalação

```bash
# Clonar direto na pasta de skills do Claude Code
git clone https://github.com/Exos-Marketing/replicar-meta-clickup.git \
  ~/.claude/skills/replicar-meta-clickup
```

Depois dispare no Claude Code:

```
> Replica a meta 23 para o projeto [DM][LB][POS][JUL][26]
> Cria o ambiente de metas do lançamento da Daniela
> Monta os Goals do [LL][PEP][LIVES][26] usando a meta 25 como modelo
```

## Limitação: pasta de Goals

A API pública do ClickUp **não cria pasta de Goals** (`/goal_folder` dá 404) **nem move meta entre pastas**. Se a pasta do cliente não existir:

1. A meta é criada na raiz do time (com aviso)
2. O usuário cria a pasta no app (10s)
3. Rodar `--apply` de novo — o engine migra a meta para a pasta (idempotente)

## Requisitos

- [Claude Code](https://claude.com/claude-code) (CLI, desktop ou extensão de IDE)
- Token da API do ClickUp guardado no Keychain macOS: `clickup-exos-api`
- Python 3.9+
- Acesso ao workspace ClickUp da Exos (`9013012202`)

## Skill irmã

[duplicar-projeto-clickup](https://github.com/Exos-Marketing/duplicar-projeto-clickup) — cria os marcos que esta skill linka nos key results.

## Maintainer

Desenvolvida pela [Exos Marketing Digital](https://exosmkt.com.br) para uso interno nas operações de lançamento.
