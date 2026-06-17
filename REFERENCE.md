# REFERENCE — Replicar Meta (Goals) ClickUp (Exos)

Workspace (team) ID: **9013012202**. Confirme IDs reais via API antes de escrever.

## 1. Endpoints de Goals usados (API v2)
| Ação | Método | Path |
|---|---|---|
| Listar metas + pastas | GET | `/api/v2/team/{WS}/goal?include_completed=true` |
| Detalhe da meta (+ key_results) | GET | `/api/v2/goal/{goal_id}` |
| Criar meta | POST | `/api/v2/team/{WS}/goal` |
| Apagar meta | DELETE | `/api/v2/goal/{goal_id}` |
| Criar key result | POST | `/api/v2/goal/{goal_id}/key_result` |

**Criar meta (body):** `name`, `description`, `multiple_owners:true`, `owners:[user_id]`, `color`,
`due_date` (ms epoch, opcional), `folder_id` (opcional — só de pasta **existente**).

**Criar key result (body):** `name` (= nome da fase), `owners:[...]`, `type:"automatic"`,
`steps_start:0`, `steps_end:<nº de tasks>`, `unit:"tasks"`, `task_ids:[...]`, `list_ids:[]`.
Em `automatic`, o ClickUp recalcula o progresso pela conclusão das tasks linkadas.

> **NÃO existe** endpoint público para **criar pasta de Goals** (`/goal_folder` → 404) nem para
> **mover** meta entre pastas (Update Goal ignora `folder_id`). Ver "Limitação" no SKILL.md.

## 2. Regra de marco
**Marco = milestone = `custom_item_id == 1`.** O KR de cada fase linka os `task_ids` dos marcos
daquela fase (não as atividades). `link:"all_tasks"` no config inclui todas as tasks com o sufixo.

## 3. Mapeamento fase → lista (reaproveitado do projeto)
O engine lê o `phase_map` do `config_<projeto>.json` (mesmo da skill `duplicar-projeto-clickup`).
Listas de fase do **Lançamento Base** (origem dos marcos da DM):

| Fase | Lista |
|---|---|
| Concepção | 901302376636 |
| Setup | 901302376637 |
| Captação | 901302378944 |
| Aquecimento | 901302378939 |
| Evento | 901302376639 |
| Lançamento | 901302376640 |
| Pós Venda | 901302376641 |
| Downsell | 901310974062 |

## 4. Pastas de Goals existentes (criar via app quando faltar)
`Debora Heller` · `Pessoal` · `Automa Eu` · `Agencia Eu` · `L&P` · `SPTF - Benflex` ·
`Nathalia Abrantes` · `Kleber Meireles` · `Leo Muniz` · `Bruna Lavinas` · `Leticia Lang` ·
`Elen Tolentino`. (Daniela Moleiro **não existia** — criada manualmente quando necessário.)

## 5. Metas-modelo úteis (pretty_id da URL `/goals/NN`)
| pretty_id | Nome | Pasta | Padrão |
|---|---|---|---|
| 23 | `[ET][RS][POS][FEV][26]` | Elen Tolentino | 6 KR automáticos, 1/fase, linkados a marcos — **modelo de referência** |
| 25 | `[LL][LM][POS][ABR][26]` | Leticia Lang | 4 KR |
| 24 | `[KM][RS][TIC][MAR][26]` | Kleber Meireles | 1 KR |

## 6. Owners (papel → user_id)
| Pessoa | user_id |
|---|---|
| Cleber de Lima (Gestor) | 54927970 |

Resolver outros via MCP `clickup_get_workspace_members` / `clickup_find_member_by_name`.

## 7. Token
Keychain, serviço `clickup-exos-api`: `TOKEN=$(security find-generic-password -s clickup-exos-api -w)`.
Nunca hard-codar nem imprimir o valor. Engine lê de `CLICKUP_TOKEN`.
