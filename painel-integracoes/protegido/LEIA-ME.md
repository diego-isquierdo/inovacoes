# Painel de Gestão · Integrações — pacote cifrado

O conteúdo deste projeto (documentos, scripts, fontes do painel e testes) está no arquivo cifrado
[`painel-integracoes.enc`](painel-integracoes.enc), porque inclui dados de clientes e este repositório é público.
Os arquivos em texto puro de `painel-integracoes/` nos commits `68d4694` e `61ba945` são versões antigas e não são mais atualizados.

## Como abrir

Pré-requisitos: Python 3 e `pip install cryptography`. A senha é do Diego Isquierdo (peça a ele; ela não está no repositório).

```bash
python painel-integracoes/ferramentas/proteger_pacote.py decifrar painel-integracoes/protegido/painel-integracoes.enc --destino painel-integracoes-decifrado
```

O script pede a senha no terminal (sem eco) e recria as pastas dentro do destino. O arquivo `MANIFESTO.json` lista o sha256 de cada arquivo.
Senha errada ou arquivo alterado são recusados.

## Técnica

AES-256-GCM, chave derivada da senha por scrypt (n=2^17, r=8, p=1), salt e nonce aleatórios. Não há recuperação sem a senha.

## Para quem mantém

Veja a seção "Pacote cifrado" do `VERSIONAMENTO.md` (dentro do pacote). Resumo: atualizar os arquivos de origem, rodar `proteger_pacote.py cifrar --saida ...` e commitar só o `.enc`.
