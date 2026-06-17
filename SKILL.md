---
name: replicar-meta-clickup
description: Cria o "ambiente de Metas (Goals)" de um projeto novo no ClickUp da Exos, espelhando uma meta-modelo, com o engine API-first duplicar_meta.py. Cria 1 key result AUTOMÁTICO por fase do projeto (unit=tasks), linkado aos task_ids dos MARCOS (milestones) daquela fase, dentro de uma pasta de Goals do cliente — seguindo a nomenclatura [SIGLA][TIPO][PRODUTO][MÊS][ANO]. Idempotente, dry-run por padrão. Use quando o usuário pedir para replicar/criar a meta de um projeto, ou disser "replica a meta de X", "cria a meta do projeto novo", "monta o ambiente de metas", "goal do lançamento", "replica a meta 23 pra Daniela", ou logo após duplicar um projeto com a skill duplicar-projeto-clickup.
---

# Replicar Meta (Goal) de Projeto no ClickUp (Exos)

Cria o **ambiente de metas** de um projeto espelhando uma **meta-modelo**: **1 key result automático
por fase** do funil (`unit=tasks`), **linkado aos task_ids dos MARCOS** (milestones, `custom_item_id==1`)
daquela fase no destino. O progresso da meta passa a ser calculado **automaticamente** pela conclusão
dos marcos. Nome da meta = sufixo do projeto `[SIGLA][TIPO][PRODUTO][MÊS][ANO]`.

**Arquitetura API-first.** Goals **não estão no MCP** — tudo via **API REST** com o engine
**`duplicar_meta.py`**. Token no Keychain: `TOKEN=$(security find-generic-password -s clickup-exos-api -w)`
(nunca imprima o valor). Reaproveita o **mesmo `config_<projeto>.json`** da skill
[duplicar-projeto-clickup](../duplicar-projeto-clickup/SKILL.md) — só precisa do bloco `goal` (abaixo).

## Como a meta espelha o projeto
- 1 fase do `phase_map` → 1 key result com o **nome da fase**.
- KR é `type: "automatic"`, `unit: "tasks"`, `task_ids` = os marcos da fase no destino.
- Por padrão **pula fases sem marcos** (`only_phases_with_tasks`) — KR só onde já há tarefa.
- A meta-modelo serve como **referência do padrão** (1 KR automático/fase), não dos nomes — os nomes
  das fases vêm do próprio projeto (`phase_map`).

## Bloco `goal` no config
```jsonc
"goal": {
  "enabled": true,
  "source_goal": "23",                 // pretty_id (da URL /goals/NN) OU uuid da meta-modelo
  "folder_name": "Daniela Moleiro",    // pasta de Goals do cliente (ver limitação abaixo)
  "name": "[DM][LB][POS][JUL][26]",    // default = target.suffix
  "description": "Planejamento Estratégico: ",
  "color": "#757380",
  "due_date": "2026-07-31",            // ISO; default = último dia do mês do sufixo
  "owners": [54927970],                // Cleber de Lima
  "link": "milestones",                // milestones (marcos) | all_tasks
  "only_phases_with_tasks": true
}
```

## Fluxo (2 fases: discover → execute)
1. **Confirmar** a **meta-modelo** (pretty_id da URL `app.clickup.com/9013012202/goals/NN`) e o
   **projeto-destino** (sufixo). Reusar o `config_<projeto>.json` já existente; adicionar o bloco `goal`.
2. **`discover`** (read-only) → gera `plano_meta.json` editável (1 KR por fase com marcos + os task_ids).
   Confira os KRs/contagens. Dá pra editar o plano antes de aplicar.
3. **Dry-run** `execute --plan plano_meta.json` → **mostre ao usuário** o que será criado. **Confirme.**
4. **`execute --plan plano_meta.json --apply`** → garante a pasta, cria a meta e os KRs automáticos.
   **Idempotente** (pula meta/KR que já existem por nome).

### Engine — comandos
```
TOKEN=$(security find-generic-password -s clickup-exos-api -w)
SK=~/.claude/skills/replicar-meta-clickup/scripts          # cópia canônica do engine + config exemplo
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py discover --config config_X.json --out plano_meta.json
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py execute  --plan plano_meta.json            # dry-run
CLICKUP_TOKEN=$TOKEN python3 $SK/duplicar_meta.py execute  --plan plano_meta.json --apply    # escreve
```

## ⚠️ Limitação: pasta de Goals
A **API pública do ClickUp NÃO cria pasta de Goals** (`/goal_folder` dá 404) **nem move meta entre
pastas** (Update Goal não aceita `folder_id`). Uma meta só entra numa pasta sendo **criada com o
`folder_id` de uma pasta que já existe**. Fluxo recomendado:
1. Se a pasta do cliente **não existe**, o engine cria a meta **na raiz do time** e avisa.
2. O usuário **cria a pasta** (ex.: "Daniela Moleiro") em **Goals** no app (10s).
3. **Re-rodar `--apply`**: o engine **migra** a meta — recria dentro da pasta e **apaga a da raiz**
   (idempotente; sem duplicar). Se a pasta já existe de início, a meta nasce direto nela.

## Guardrails
- Engine é **dry-run por padrão**; `--apply` é explícito. **Sempre** mostre o dry-run e confirme.
- **Idempotência por nome** (meta e KR): não duplica o que já existe.
- **Nunca** apagar/alterar uma meta existente sem confirmação — exceto a migração de pasta descrita acima
  (apaga só a meta-irmã recém-criada na raiz, de mesmo nome).
- KR `automatic` linkado a marcos: não setar progresso manual — quem move é a conclusão das tasks.

## Referências
- [PROMPT.md](PROMPT.md) — prompt-modelo (curto e completo) pra disparar a replicação de meta.
- [REFERENCE.md](REFERENCE.md) — endpoints de Goals, schema do bloco `goal`, pastas/owners/IDs úteis.
- Engine + exemplo: `scripts/duplicar_meta.py`, `scripts/config_meta_exemplo.json`.
- Skill irmã: [duplicar-projeto-clickup](../duplicar-projeto-clickup/SKILL.md) (cria os marcos que os KRs linkam).
