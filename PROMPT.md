# Prompt-modelo — Replicar Meta (Goal) de projeto no ClickUp

Cole um dos blocos abaixo no chat. A skill **replicar-meta-clickup** assume a partir daí.

---

## 🟢 Prompt curto (1 linha — o jeito do dia a dia)

```
Replica a meta <MODELO> para o projeto <SUFIXO_DO_PROJETO>.
```

Exemplos:
```
Replica a meta 23 para o projeto [DM][LB][POS][JUL][26].
Cria o ambiente de metas do [LL][PEP][LIVES][26] espelhando a meta 23.
Monta a meta do novo lançamento da Elen usando a meta 25 como modelo.
```

- `<MODELO>` = o **pretty_id** da meta-modelo (o número da URL `app.clickup.com/9013012202/goals/NN`)
  ou o nome dela. Modelo padrão de lançamento: **23** (`[ET][RS][POS][FEV][26]`).
- `<SUFIXO_DO_PROJETO>` = `[SIGLA][TIPO][PRODUTO][MÊS][ANO]` do projeto que já tem os marcos criados.

---

## 🔵 Prompt completo (quando quiser controlar os detalhes)

```
Replicar ambiente de Metas (Goals) no ClickUp.

- Meta-modelo: <pretty_id ou nome>            (ex.: 23)
- Projeto-destino (sufixo): <[SIGLA][TIPO][PRODUTO][MÊS][ANO]>
- Cliente / pasta de Goals: <Nome do cliente> (ex.: Daniela Moleiro)
- Nome da meta: <default = o próprio sufixo>
- Due date: <AAAA-MM-DD ou "fim do mês do sufixo">
- Owner(s): <default = Cleber 54927970>
- Key results: <só fases com marcos (padrão) | todas as 8 fases>
- Linkar: <marcos/milestones (padrão) | todas as tasks>

Use a skill replicar-meta-clickup: ajuste o bloco "goal" no config_<projeto>.json,
rode discover → me mostre o dry-run → e só aplique (--apply) após eu confirmar.
```

---

## O que o assistente vai fazer (não precisa pedir, é o fluxo da skill)
1. Confirmar meta-modelo + projeto-destino e localizar os marcos por fase.
2. `discover` → gerar `plano_meta.json` (1 key result automático por fase com marcos).
3. Mostrar o **dry-run** (pasta, meta, KRs e contagem de tasks) e **pedir confirmação**.
4. `execute --apply` → criar a meta + KRs (idempotente; não duplica).
5. Avisar se a **pasta de Goals do cliente não existir** — nesse caso você cria a pasta no app
   e arrasta a meta (ou re-roda que ele migra). Ver "Limitação" no [SKILL.md](SKILL.md).

> Lembrete: a meta só faz sentido depois que os **marcos do projeto já existem** — normalmente
> logo após rodar a skill `duplicar-projeto-clickup`.
