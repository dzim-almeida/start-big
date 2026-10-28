# ---------------------------------------------------------------------------
# ARQUIVO: scripts/gerar_tabelas_nfse.py
# DESCRIÇÃO: Gera os arquivos de dados da NFS-e (app/data/*.csv.gz) a partir
#            das planilhas oficiais do portal da NFS-e Nacional.
# ---------------------------------------------------------------------------
"""
Ferramenta de desenvolvimento: NÃO roda na loja e não entra no sidecar.

DE ONDE VÊM AS PLANILHAS (gov.br/nfse › Biblioteca › Documentação técnica)
- Anexo A — municípios IBGE:
  documentacao-atual/anexo_a-municipio_ibge-paises_iso2-v1-00-snnfse-20251210.xlsx
- Anexo B — lista de serviços nacional + NBS 2.0:
  documentacao-atual/anexo_b-nbs2-lista_servico_nacional-snnfse-v1-01-20260122.xlsx
- Anexo VIII — correlação item LC 116 × NBS × cClassTrib:
  rtc/anexoviii-correlacaoitemnbsindopcclasstrib_ibscbs_v1-00-00.xlsx

Quando o portal publicar versão nova, baixe a planilha e rode de novo. O boot
seguinte recarrega as tabelas (ver app/core/seed_nfse.py).

USO (o openpyxl é só desta ferramenta, não está no requirements.txt):
    .venv\\Scripts\\pip install openpyxl
    .venv\\Scripts\\python scripts\\gerar_tabelas_nfse.py <anexo_a.xlsx> <anexo_b.xlsx> <anexo_viii.xlsx>
"""

import csv
import gzip
import io
import os
import sys

import openpyxl

DESTINO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")


def _digitos(valor) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


def _linhas(caminho: str, aba: str) -> list[tuple]:
    planilha = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    return list(planilha[aba].iter_rows(values_only=True))[1:]


def _gravar(nome: str, campos: list[str], linhas: list[dict]) -> None:
    caminho = os.path.join(DESTINO, nome)
    # mtime=0: o mesmo conteúdo gera o mesmo arquivo, e o git não vê mudança falsa.
    saida = io.StringIO(newline="")
    escritor = csv.DictWriter(saida, fieldnames=campos, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    with open(caminho, "wb") as bruto, gzip.GzipFile(fileobj=bruto, mode="wb", mtime=0) as gz:
        gz.write(saida.getvalue().encode("utf-8"))
    print(f"{nome}: {len(linhas)} linhas")


# Os 2 primeiros dígitos do código IBGE são a UF. A planilha traz a sigla vazia
# em estados inteiros (o Maranhão, por exemplo), então ela sai daqui.
UF_POR_CODIGO = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def municipios(anexo_a: str) -> list[dict]:
    """Os 5.570 municípios, com a UF tirada do próprio código."""
    resultado = []
    for _uf, _sigla, nome, codigo in _linhas(anexo_a, "TAB.MUN_IBGE"):
        if not codigo:
            continue
        codigo = _digitos(codigo).zfill(7)
        resultado.append({"codigo": codigo, "nome": str(nome).strip(), "uf": UF_POR_CODIGO[codigo[:2]]})
    return resultado


def servicos_nacionais(anexo_b: str) -> list[dict]:
    """Os códigos de tributação nacional (6 dígitos). A descrição completa leva o
    item e o subitem, porque a do desdobro sozinha costuma repetir o subitem."""
    linhas = _linhas(anexo_b, "LISTA.SERV.NAC.")
    descricao_item: dict[str, str] = {}
    resultado = []
    for codigo, item, subitem, desdobro, descricao in linhas:
        descricao = " ".join(str(descricao or "").split())
        if not codigo:
            if str(subitem) == "0":
                descricao_item[str(item)] = descricao
            continue
        codigo = _digitos(codigo).zfill(6)
        pai = descricao_item.get(str(item), "")
        resultado.append({
            "codigo": codigo,
            "descricao": descricao,
            "descricao_completa": f"{pai} / {descricao}" if pai else descricao,
        })
    return resultado


def nbs(anexo_b: str) -> list[dict]:
    """Só os códigos de 9 dígitos vão na nota; os mais curtos são os grupos, e
    entram como a cadeia de ancestrais na descrição completa (como no NCM)."""
    linhas = _linhas(anexo_b, "LISTA.NBS_v2.0")
    grupos = {}
    folhas = []
    for codigo, descricao in linhas:
        digitos = _digitos(codigo)
        if not digitos or not descricao:
            continue
        descricao = " ".join(str(descricao).split())
        if len(digitos) == 9:
            folhas.append((digitos, descricao))
        else:
            grupos[digitos] = descricao
    resultado = []
    for digitos, descricao in folhas:
        ancestrais = [grupos[digitos[:n]] for n in range(5, 9) if digitos[:n] in grupos]
        cadeia = [a for a in ancestrais if a != descricao]
        resultado.append({
            "codigo": digitos,
            "descricao": descricao,
            "descricao_completa": " / ".join(cadeia + [descricao]),
        })
    return resultado


def correlacao_nbs(anexo_viii: str) -> list[dict]:
    """Pares (subitem LC 116 → NBS). A planilha só preenche o item na primeira
    linha de cada grupo; as seguintes herdam."""
    linhas = _linhas(anexo_viii, "tabela geral")
    item_atual = None
    vistos = set()
    resultado = []
    for linha in linhas:
        item, _desc, codigo_nbs = linha[0], linha[1], linha[2]
        if item:
            item_atual = _digitos(item).zfill(4)
        digitos = _digitos(codigo_nbs)
        if not item_atual or len(digitos) != 9 or (item_atual, digitos) in vistos:
            continue
        vistos.add((item_atual, digitos))
        resultado.append({"item_lc116": item_atual, "nbs": digitos})
    return resultado


def main(anexo_a: str, anexo_b: str, anexo_viii: str) -> None:
    _gravar("municipios_ibge.csv.gz", ["codigo", "nome", "uf"], municipios(anexo_a))
    _gravar("nfse_servicos_nacionais.csv.gz", ["codigo", "descricao", "descricao_completa"], servicos_nacionais(anexo_b))
    _gravar("nbs.csv.gz", ["codigo", "descricao", "descricao_completa"], nbs(anexo_b))
    _gravar("nfse_correlacao_nbs.csv.gz", ["item_lc116", "nbs"], correlacao_nbs(anexo_viii))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
