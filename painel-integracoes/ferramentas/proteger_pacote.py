"""Cifra e decifra o pacote do Painel de Gestão · Integrações (documentos, scripts e fontes do painel).

O repositório é público e o pacote contém dados de clientes (demandas recorrentes, documentos de apoio). Por isso o que vai ao
GitHub é UM arquivo cifrado (`painel-integracoes.enc`); quem precisar do conteúdo informa a senha para decifrar.

Segurança
  - AES-256-GCM (autenticado: senha errada ou arquivo alterado são detectados) com chave derivada da senha por scrypt
    (n=2^17, r=8, p=1) e salt/nonce aleatórios por arquivo.
  - A senha é pedida só no terminal (`getpass`, sem eco). Nunca é aceita por argumento, variável de ambiente ou arquivo,
    nunca é gravada e não aparece em log. Ao cifrar, a senha é digitada duas vezes e o arquivo gerado é testado
    (decifrado em memória e comparado) antes de ser gravado.
  - Perder a senha = perder o arquivo cifrado (não há recuperação). Use um gerenciador de senhas.

Uso
  python proteger_pacote.py cifrar  [--saida CAMINHO.enc]
  python proteger_pacote.py decifrar CAMINHO.enc [--destino PASTA]

`cifrar` lê os arquivos da pasta do Painel (OneDrive, na estrutura do VERSIONAMENTO.md); `decifrar` recria a mesma
estrutura de pastas dentro do destino (padrão: ./painel-integracoes-decifrado). Requer o pacote `cryptography`.
"""
import argparse
import getpass
import hashlib
import io
import json
import os
import struct
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"PINT-ENC1"
LOG_N, R, P = 17, 8, 1
MIN_SENHA = 12

AQUI = Path(__file__).resolve().parent
PAINEL = AQUI.parent                      # ...\Inovações\Painel de Gestão\Integrações
INOV = PAINEL.parent.parent               # ...\Inovações


def arquivos_do_pacote():
    """(origem absoluta, nome dentro do pacote). Segue o mapa do VERSIONAMENTO.md; nunca inclui bases, logs ou segredos."""
    out = []

    def add(p, nome):
        if p.is_file():
            out.append((p, nome))

    for f in ("README.md", "MAPA.md", "PLANEJAMENTO.md", "LOG.md", "VERSIONAMENTO.md"):
        add(PAINEL / f, f)
    for p in sorted((PAINEL / "extracao").glob("*.md")):
        add(p, f"extracao/{p.name}")
    add(INOV / "MCP - Fresk" / "freshdesk_mcp" / "scripts" / "extracao_integracoes.py", "extracao/scripts/tickets/extracao_integracoes.py")
    for p in sorted((PAINEL / "automacao").glob("*.ps1")):
        add(p, f"automacao/{p.name}")
    for p in sorted((PAINEL / "ferramentas").glob("*.py")):
        add(p, f"ferramentas/{p.name}")
    for nome in ("montar.sh", "painel_v1.html", "teste_node.js", "teste_aderencia.js"):
        add(PAINEL / "painel" / nome, f"painel/{nome}")
    for p in sorted((PAINEL / "painel" / "partes").glob("*")):
        add(p, f"painel/partes/{p.name}")
    add(INOV / "MAPA_MCPS.md", "extras/MAPA_MCPS.md")
    return out


def chave(senha, salt, log_n=LOG_N, r=R, p=P):
    return Scrypt(salt=salt, length=32, n=2 ** log_n, r=r, p=p).derive(senha.encode("utf-8"))


def empacota():
    buf = io.BytesIO()
    itens = arquivos_do_pacote()
    manifesto = {"gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "arquivos": {n: hashlib.sha256(p.read_bytes()).hexdigest() for p, n in itens}}
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        dados = json.dumps(manifesto, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("MANIFESTO.json")
        info.size = len(dados)
        tar.addfile(info, io.BytesIO(dados))
        for p, n in itens:
            tar.add(p, arcname=n, recursive=False)
    return buf.getvalue(), len(itens)


def cifra(dados, senha):
    salt, nonce = os.urandom(16), os.urandom(12)
    cab = MAGIC + struct.pack(">BBB", LOG_N, R, P) + salt + nonce
    return cab + AESGCM(chave(senha, salt)).encrypt(nonce, dados, cab)


def decifra(blob, senha):
    if not blob.startswith(MAGIC):
        raise ValueError("Arquivo não reconhecido (não é um pacote cifrado deste projeto).")
    n = len(MAGIC)
    log_n, r, p = struct.unpack(">BBB", blob[n:n + 3])
    salt, nonce = blob[n + 3:n + 19], blob[n + 19:n + 31]
    cab = blob[:n + 31]
    try:
        return AESGCM(chave(senha, salt, log_n, r, p)).decrypt(nonce, blob[n + 31:], cab)
    except InvalidTag:
        raise ValueError("Senha incorreta ou arquivo alterado.")


def extrai(dados, destino):
    destino = destino.resolve()
    destino.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as tar:
        for m in tar.getmembers():
            alvo = (destino / m.name).resolve()
            if not m.isfile() or destino not in alvo.parents and alvo != destino:
                raise ValueError(f"Entrada insegura no pacote: {m.name}")
        for m in tar.getmembers():
            alvo = destino / m.name
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_bytes(tar.extractfile(m).read())
    return destino


def pede_senha(confirmar):
    s = getpass.getpass("Senha: ")
    if confirmar:
        if len(s) < MIN_SENHA:
            raise SystemExit(f"A senha deve ter pelo menos {MIN_SENHA} caracteres.")
        if getpass.getpass("Repita a senha: ") != s:
            raise SystemExit("As senhas não conferem. Nada foi gravado.")
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cifrar")
    c.add_argument("--saida", default="painel-integracoes.enc")
    d = sub.add_parser("decifrar")
    d.add_argument("arquivo")
    d.add_argument("--destino", default="painel-integracoes-decifrado")
    a = ap.parse_args()

    if a.cmd == "cifrar":
        dados, n = empacota()
        senha = pede_senha(True)
        blob = cifra(dados, senha)
        if decifra(blob, senha) != dados:            # teste de ida e volta antes de gravar
            raise SystemExit("Falha na verificação do arquivo cifrado. Nada foi gravado.")
        saida = Path(a.saida)
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_bytes(blob)
        print(f"Pacote cifrado: {saida} ({n} arquivos, {len(blob) / 1024:.0f} KB, sha256 {hashlib.sha256(blob).hexdigest()[:16]}...)")
    else:
        blob = Path(a.arquivo).read_bytes()
        try:
            dados = decifra(blob, pede_senha(False))
        except ValueError as e:
            raise SystemExit(str(e))
        dest = extrai(dados, Path(a.destino))
        print(f"Conteúdo decifrado em: {dest}")


if __name__ == "__main__":
    main()
