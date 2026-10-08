"""Gera automacao/manifesto_integracoes.json: metadados das duas bases do painel de Integracoes
(caminho, tamanho, sha256, gerado_em, linhas). A tarefa agendada do Claude compara o sha256 com o
`cfg/bases` do painel e so envia o que mudou. Nao imprime nem grava dado de cliente.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

INOV = Path(__file__).resolve().parents[3]
OUT = INOV / "MCP - Fresk" / "freshdesk_mcp" / "scripts" / "output" / "Integrações"
DEST = Path(__file__).resolve().parents[1] / "automacao" / "manifesto_integracoes.json"


def info(path: Path, tipo: str) -> dict:
    j = json.loads(path.read_text(encoding="utf-8"))
    linhas = len(j["tabelas"]["Apontamentos"]["linhas"]) if tipo == "horas" else len(j["linhas"])
    return {"tipo": tipo, "arquivo": path.name, "caminho": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "gerado_em": (j.get("meta") or {}).get("gerado_em", ""), "linhas": linhas}


bases = [info(OUT / "base_integracoes.json", "tickets"), info(OUT / "horas_integracoes_painel.json", "horas")]
manifesto = {"gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "bases": bases}
DEST.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
print("manifesto ok:", [(b["tipo"], b["linhas"]) for b in bases])
