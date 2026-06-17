#!/usr/bin/env python3
"""
Engine de replicacao de METAS (Goals) do ClickUp (Exos) - API-first.

Cria o "ambiente de metas" de um projeto novo espelhando uma meta-modelo:
  - 1 key result AUTOMATICO por fase do projeto (unit=tasks), linkado aos
    task_ids dos MARCOS (custom_item_id==1) daquela fase no destino.
  - meta dentro de uma pasta de Goals do cliente (cria se nao existir; senao
    cai na raiz do time e avisa).

Reaproveita o mesmo config_*.json da duplicacao de projeto:
  workspace, target.suffix, phase_map (fase -> {dst: list_id}) + um bloco "goal".

Fluxo em 2 fases (igual ao duplicar_projeto.py):
  discover : le os marcos do destino e gera plano_meta.json (editavel)
  execute  : aplica o plano via API (dry-run por padrao; --apply escreve)

Uso:
  CLICKUP_TOKEN=$(security find-generic-password -s clickup-exos-api -w) \
    python3 duplicar_meta.py discover --config config_dm_lb_pos.json --out plano_meta.json
  python3 duplicar_meta.py execute --plan plano_meta.json            # dry-run
  python3 duplicar_meta.py execute --plan plano_meta.json --apply    # escreve
"""
import os, sys, json, time, argparse, datetime, urllib.request, urllib.error

TOKEN = os.environ.get("CLICKUP_TOKEN", "")
WS = "9013012202"

def api(method, path, body=None, tries=5):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(tries):
        req = urllib.request.Request("https://api.clickup.com" + path, data=data, method=method)
        req.add_header("Authorization", TOKEN); req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t.strip() else {})
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(3*(a+1)); continue
            return e.code, _safe(e.read().decode())
        except Exception:
            time.sleep(2); continue
    return 0, "retry"

def _safe(s):
    try: return json.loads(s)
    except Exception: return s

# ---------- goals helpers ----------
def team_goals():
    """Retorna (folders, goals_top_level) de /team/{WS}/goal."""
    c, b = api("GET", f"/api/v2/team/{WS}/goal?include_completed=true")
    if c != 200 or not isinstance(b, dict):
        c, b = api("GET", f"/api/v2/team/{WS}/goal")
    if c != 200 or not isinstance(b, dict):
        return [], []
    return b.get("folders", []) or [], b.get("goals", []) or []

def resolve_source_goal(ref):
    """Aceita pretty_id (ex '23') ou uuid; devolve o dict da meta-modelo (ou None)."""
    ref = str(ref)
    folders, top = team_goals()
    pool = list(top)
    for f in folders:
        pool += f.get("goals", []) or []
    for g in pool:
        if str(g.get("pretty_id")) == ref or g.get("id") == ref:
            return g
    # fallback: tenta GET direto pelo uuid
    c, b = api("GET", f"/api/v2/goal/{ref}")
    if c == 200 and isinstance(b, dict) and b.get("goal"):
        return b["goal"]
    return None

def find_folder_id(name):
    folders, _ = team_goals()
    for f in folders:
        if (f.get("name") or "").strip() == name.strip():
            return f["id"]
    return None

def create_folder(name):
    """Tenta criar pasta de Goals. Endpoint nao-documentado; se falhar devolve None."""
    c, b = api("POST", f"/api/v2/team/{WS}/goal_folder", {"name": name})
    if c in (200, 201) and isinstance(b, dict):
        fid = (b.get("folder") or {}).get("id") or b.get("id")
        if fid: return fid
    return None

def find_goal_in_scope(folder_id, name):
    """Acha meta por nome (na pasta se folder_id, senao no time todo)."""
    folders, top = team_goals()
    if folder_id:
        for f in folders:
            if f.get("id") == folder_id:
                for g in f.get("goals", []) or []:
                    if (g.get("name") or "").strip() == name.strip():
                        return g.get("id")
        return None
    pool = list(top)
    for f in folders:
        pool += f.get("goals", []) or []
    for g in pool:
        if (g.get("name") or "").strip() == name.strip():
            return g.get("id")
    return None

def goal_detail(goal_id):
    c, b = api("GET", f"/api/v2/goal/{goal_id}")
    return b.get("goal") if (c == 200 and isinstance(b, dict)) else None

def delete_goal(goal_id):
    c, _ = api("DELETE", f"/api/v2/goal/{goal_id}")
    return c in (200, 204)

# ---------- discovery ----------
def list_tasks(list_id):
    out, page = [], 0
    while True:
        c, b = api("GET", f"/api/v2/list/{list_id}/task?archived=false&include_closed=true&subtasks=false&page={page}")
        if c != 200 or not isinstance(b, dict): break
        out += b.get("tasks", [])
        if b.get("last_page", True) or page > 25: break
        page += 1
    return out

def phase_task_ids(list_id, suffix, link):
    """task_ids do destino na fase: marcos (custom_item_id==1) ou todas as tasks com o sufixo."""
    ts = [t for t in list_tasks(list_id) if suffix in (t.get("name") or "")]
    if link == "milestones":
        ts = [t for t in ts if t.get("custom_item_id") == 1]
    return [t["id"] for t in ts]

def iso_to_ms(s):
    if not s: return None
    try:
        d = datetime.datetime.strptime(s, "%Y-%m-%d")
        d = d.replace(hour=23, minute=59, second=59)
        return int(d.timestamp() * 1000)
    except Exception:
        return None

MONTHS = {"JAN":1,"FEV":2,"MAR":3,"ABR":4,"MAI":5,"JUN":6,"JUL":7,"AGO":8,"SET":9,"OUT":10,"NOV":11,"DEZ":12}

def default_due_from_suffix(suffix):
    """Ultimo dia do mes/ano do sufixo [..][..][..][MES][AA]. Devolve ISO ou None."""
    toks = [t.strip("[]") for t in suffix.replace("][", "|").strip("[]").split("|")]
    mes = next((t for t in toks if t in MONTHS), None)
    yy = next((t for t in toks if t.isdigit() and len(t) == 2), None)
    if not (mes and yy): return None
    m = MONTHS[mes]; y = 2000 + int(yy)
    nxt = datetime.date(y + (m == 12), (m % 12) + 1, 1)
    last = nxt - datetime.timedelta(days=1)
    return last.isoformat()

def discover(cfg):
    tgt = cfg["target"]; gc = cfg.get("goal", {})
    suffix = tgt["suffix"]
    link = gc.get("link", "milestones")
    only_pop = gc.get("only_phases_with_tasks", True)

    src_goal = resolve_source_goal(gc["source_goal"])
    src_info = None
    if src_goal:
        src_info = {"id": src_goal.get("id"), "pretty_id": src_goal.get("pretty_id"),
                    "name": src_goal.get("name"),
                    "kr_names": [k.get("name") for k in (goal_detail(src_goal["id"]) or {}).get("key_results", [])]}
        print(f"[modelo] meta {src_info['pretty_id']} '{src_info['name']}' "
              f"({len(src_info['kr_names'])} KRs): {src_info['kr_names']}", file=sys.stderr)
    else:
        print(f"[aviso] meta-modelo '{gc.get('source_goal')}' nao encontrada (sigo com o padrao 1 KR/fase)", file=sys.stderr)

    krs = []
    for phase, m in cfg["phase_map"].items():
        ids = phase_task_ids(m["dst"], suffix, link)
        if only_pop and not ids:
            print(f"[skip] {phase}: 0 marcos", file=sys.stderr); continue
        krs.append({"phase": phase, "name": phase, "task_ids": ids})
        print(f"[kr]   {phase}: {len(ids)} task(s)", file=sys.stderr)

    folder_name = gc.get("folder_name")
    folder_id = find_folder_id(folder_name) if folder_name else None
    due_iso = gc.get("due_date") or default_due_from_suffix(suffix)

    plan = {
        "workspace": WS,
        "source_model": src_info,
        "folder": {"name": folder_name, "id": folder_id},
        "goal": {
            "name": gc.get("name") or suffix,
            "description": gc.get("description", ""),
            "color": gc.get("color", "#757380"),
            "due_date_iso": due_iso,
            "due_date_ms": iso_to_ms(due_iso),
            "owners": gc.get("owners", []),
        },
        "key_results": krs,
    }
    return plan

# ---------- execute ----------
def execute(plan, apply):
    g = plan["goal"]; fld = plan.get("folder") or {}
    folder_id = fld.get("id")
    folder_name = fld.get("name")

    # 1) pasta
    if folder_name and not folder_id:
        existing = find_folder_id(folder_name)
        if existing:
            folder_id = existing
            print(f"[folder] usando pasta existente '{folder_name}' ({folder_id})")
        elif apply:
            folder_id = create_folder(folder_name)
            if folder_id:
                print(f"[folder] criada pasta '{folder_name}' ({folder_id})")
            else:
                print(f"[folder][AVISO] API nao criou a pasta '{folder_name}'. "
                      f"A meta vai pra raiz do time. Crie a pasta no app e rode de novo (idempotente).")
        else:
            print(f"[folder] (dry) criaria pasta '{folder_name}'")

    # 2) meta (idempotente por nome). Se ja existe FORA da pasta-alvo, migra (recria na pasta + apaga a antiga).
    goal_id = find_goal_in_scope(folder_id, g["name"])
    stray_id = None
    if not goal_id and folder_id:
        stray_id = find_goal_in_scope(None, g["name"])
        if stray_id:
            print(f"[goal] '{g['name']}' existe fora da pasta '{folder_name}' ({stray_id}) - "
                  f"{'migrando p/ a pasta' if apply else '(dry) migraria p/ a pasta'}")
    if goal_id:
        print(f"[goal] ja existe '{g['name']}' na pasta ({goal_id}) - nao recria")
    elif apply:
        body = {"name": g["name"], "description": g.get("description", ""),
                "multiple_owners": True, "owners": g.get("owners", []),
                "color": g.get("color", "#757380")}
        if g.get("due_date_ms"): body["due_date"] = g["due_date_ms"]
        if folder_id: body["folder_id"] = folder_id
        c, b = api("POST", f"/api/v2/team/{WS}/goal", body)
        goal_id = (b.get("goal") or {}).get("id") if isinstance(b, dict) else None
        if not goal_id:
            print(f"[goal][ERRO] {c} {b}"); return
        print(f"[goal] criada '{g['name']}' ({goal_id})")
    else:
        print(f"[goal] (dry) criaria '{g['name']}' "
              f"(due {g.get('due_date_iso')}, owners {g.get('owners')}, folder {folder_id or 'RAIZ'})")

    # 3) key results (idempotente por nome)
    existing_kr = {}
    if goal_id:
        det = goal_detail(goal_id) or {}
        existing_kr = {(k.get("name") or "").strip(): k.get("id") for k in det.get("key_results", [])}

    for kr in plan["key_results"]:
        nm = kr["name"].strip()
        if nm in existing_kr:
            print(f"[kr] ja existe '{nm}' - pula"); continue
        if not apply or not goal_id:
            print(f"[kr] (dry) criaria '{nm}' automatic/tasks <- {len(kr['task_ids'])} task(s)"); continue
        body = {"name": kr["name"], "owners": g.get("owners", []), "type": "automatic",
                "steps_start": 0, "steps_end": len(kr["task_ids"]) or 1, "unit": "tasks",
                "task_ids": kr["task_ids"], "list_ids": []}
        c, b = api("POST", f"/api/v2/goal/{goal_id}/key_result", body)
        ok = isinstance(b, dict) and (b.get("key_result") or {}).get("id")
        print(f"[kr] {'criado' if ok else 'ERRO '+str(c)} '{nm}' <- {len(kr['task_ids'])} task(s)" + ("" if ok else f" {b}"))

    # migracao concluida: apaga a meta antiga que estava fora da pasta
    if stray_id and goal_id and apply:
        print(f"[goal] apagando meta antiga fora da pasta ({stray_id}): {'ok' if delete_goal(stray_id) else 'FALHOU'}")

    if goal_id:
        print(f"\nMeta: https://app.clickup.com/{WS}/goals/{goal_detail(goal_id).get('pretty_id','?')}")

# ---------- cli ----------
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover"); d.add_argument("--config", required=True); d.add_argument("--out", default="plano_meta.json")
    e = sub.add_parser("execute"); e.add_argument("--plan", required=True); e.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not TOKEN:
        print("Falta CLICKUP_TOKEN (security find-generic-password -s clickup-exos-api -w)"); sys.exit(1)
    if a.cmd == "discover":
        cfg = json.load(open(a.config))
        plan = discover(cfg)
        json.dump(plan, open(a.out, "w"), ensure_ascii=False, indent=2)
        print(f"\nplano salvo em {a.out}: {len(plan['key_results'])} KR(s)")
    else:
        plan = json.load(open(a.plan))
        if not a.apply: print("== DRY-RUN (use --apply para escrever) ==")
        execute(plan, a.apply)

if __name__ == "__main__":
    main()
