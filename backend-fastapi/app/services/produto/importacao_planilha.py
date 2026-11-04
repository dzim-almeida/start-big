# ---------------------------------------------------------------------------
# ARQUIVO: services/produto/importacao_planilha.py
# DESCRICAO: Importa produtos de uma planilha Excel (.xlsx).
#
# O que não pode errar:
#   - a prévia não grava nada;
#   - só CRIA produto: código que já existe fica como está, então importar o
#     mesmo arquivo duas vezes não duplica estoque nem muda preço;
#   - a gravação é tudo ou nada (a transação é do endpoint);
#   - linha com erro não entra, e as demais seguem;
#   - cada produto passa pelo mesmo `create_produto` da tela de cadastro, então
#     o estoque inicial entra no livro de movimentações como qualquer outro.
# ---------------------------------------------------------------------------

import io
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Optional

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.produto import Produto
from app.schemas.fiscal.produto import ProdutoFiscalUpdate
from app.schemas.produto.cadastro import ProdutoCreateComFiscal
from app.schemas.produto.estoque import EstoqueCreate
from app.schemas.produto.importacao import (
    LinhaImportacao,
    PreviaImportacao,
    ResultadoImportacaoPlanilha,
)
from app.services.produto.cadastro import create_produto
from app.services.produto.embalagem import codigo_de_produto_livre

TAMANHO_MAXIMO = 10 * 1024 * 1024
MAXIMO_LINHAS = 5000
ABA_PREFERIDA = "PRODUTOS"

_SINONIMOS = {
    "IMPORTAR": "importar",
    "CODIGO": "codigo", "CODIGO_PRODUTO": "codigo", "SKU": "codigo",
    "NOME": "nome", "DESCRICAO": "nome",
    "UNIDADE": "unidade", "UNID": "unidade", "UND": "unidade",
    "CODIGO_BARRAS": "codigo_barras", "CODIGO_DE_BARRAS": "codigo_barras", "GTIN": "codigo_barras", "EAN": "codigo_barras",
    "CATEGORIA": "categoria", "GRUPO": "categoria",
    "NCM": "ncm",
    "CFOP": "cfop",
    "CSOSN": "csosn",
    "CUSTO": "custo", "VALOR_CUSTO": "custo",
    "PRECO": "preco", "PRECO_VENDA": "preco", "PRECO_DE_VENDA": "preco", "VALOR_VENDA": "preco",
    "ESTOQUE": "estoque", "QUANTIDADE": "estoque", "QTDE": "estoque",
}
_OBRIGATORIAS = {"codigo": "CODIGO", "nome": "NOME", "preco": "PRECO_VENDA"}
_NAO_IMPORTAR = {"NAO", "N", "FALSE", "0"}


@dataclass
class _Analise:
    linha: LinhaImportacao
    produto: Optional[ProdutoCreateComFiscal] = None


def _erro_arquivo(mensagem: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=mensagem)


def _normalizar(texto: Any) -> str:
    sem_acento = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", "_", sem_acento.upper()).strip("_")


def _texto(valor: Any) -> str:
    """Texto da célula. O Excel guarda código numérico como 123.0: vira '123'."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def _numero(valor: Any) -> Optional[Decimal]:
    """Aceita número do Excel e texto brasileiro ('1.234,56'). Vazio vira None."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        raise ValueError
    if isinstance(valor, (int, float)):
        numero = Decimal(str(valor))
    else:
        texto = str(valor).replace("R$", "").replace(" ", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        if not texto:
            return None
        try:
            numero = Decimal(texto)
        except InvalidOperation as erro:
            raise ValueError from erro
    if not numero.is_finite():
        raise ValueError
    return numero


def _centavos(valor: Decimal) -> int:
    return int((valor * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _ler_planilha(conteudo: bytes) -> list[tuple[int, dict[str, Any]]]:
    """(número da linha, células por coluna conhecida). Recusa o que não dá para ler."""
    from openpyxl import load_workbook
    from openpyxl.utils.exceptions import InvalidFileException

    if len(conteudo) > TAMANHO_MAXIMO:
        raise _erro_arquivo("Arquivo grande demais: o limite é 10 MB.")
    try:
        livro = load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    except (zipfile.BadZipFile, InvalidFileException, KeyError, ValueError, OSError) as erro:
        raise _erro_arquivo("Não consegui ler o arquivo. Ele precisa ser uma planilha Excel .xlsx.") from erro

    try:
        aba = next((a for a in livro.worksheets if _normalizar(a.title) == ABA_PREFERIDA), livro.worksheets[0])
        linhas = aba.iter_rows(values_only=True)
        cabecalho = next(linhas, None)
        if cabecalho is None:
            raise _erro_arquivo("A planilha está vazia.")
        colunas = {i: _SINONIMOS[n] for i, n in ((i, _normalizar(c)) for i, c in enumerate(cabecalho)) if n in _SINONIMOS}
        faltando = [rotulo for campo, rotulo in _OBRIGATORIAS.items() if campo not in colunas.values()]
        if faltando:
            raise _erro_arquivo(f"Faltam as colunas {', '.join(faltando)} na primeira linha da planilha.")

        resultado: list[tuple[int, dict[str, Any]]] = []
        for numero, celulas in enumerate(linhas, start=2):
            dados = {campo: celulas[i] for i, campo in colunas.items() if i < len(celulas)}
            if all(v is None or str(v).strip() == "" for v in dados.values()):
                continue
            resultado.append((numero, dados))
            if len(resultado) > MAXIMO_LINHAS:
                raise _erro_arquivo(f"A planilha passa de {MAXIMO_LINHAS} produtos: divida em arquivos menores.")
        return resultado
    finally:
        livro.close()


def _ncm_da_celula(valor: Any) -> str:
    """O Excel come o zero à esquerda de NCM numérico (01012100 vira 1012100)."""
    ncm = _texto(valor)
    return ncm.zfill(8) if ncm.isdigit() and len(ncm) == 7 else ncm


def _fiscal_da_linha(dados: dict[str, Any], mensagens: list[str]) -> tuple[Optional[ProdutoFiscalUpdate], Optional[str]]:
    """(dados fiscais prontos ou None, NCM para mostrar). Formato ruim vira erro na linha."""
    ncm = _ncm_da_celula(dados.get("ncm"))
    campos = {
        chave: valor
        for chave, valor in (("ncm", ncm), ("cfop_padrao", _texto(dados.get("cfop"))), ("csosn", _texto(dados.get("csosn"))))
        if valor
    }
    if not campos:
        return None, None
    try:
        return ProdutoFiscalUpdate(**campos), ncm or None
    except ValidationError as erro:
        for detalhe in erro.errors():
            mensagens.append(f"Fiscal: {detalhe['msg'].removeprefix('Value error, ')}")
        return None, ncm or None


def _analisar_linha(
    db: Session,
    numero: int,
    dados: dict[str, Any],
    usar_fiscal: bool,
    codigos: set[str],
    barras: set[str],
    nomes: set[str],
) -> _Analise:
    codigo = _texto(dados.get("codigo"))
    nome = _texto(dados.get("nome"))
    unidade = _texto(dados.get("unidade")) or None
    linha = LinhaImportacao(linha=numero, codigo=codigo, nome=nome, unidade=unidade, situacao="erro")

    if _normalizar(dados.get("importar")) in _NAO_IMPORTAR:
        linha.situacao = "ignorado"
        return _Analise(linha)

    erros: list[str] = []
    avisos: list[str] = []
    if not codigo:
        erros.append("Sem código.")
    elif len(codigo) > 100:
        erros.append("Código com mais de 100 caracteres.")
    if not nome:
        erros.append("Sem nome.")
    elif len(nome) > 255:
        erros.append("Nome com mais de 255 caracteres.")
    if unidade and len(unidade) > 10:
        erros.append("Unidade com mais de 10 caracteres.")

    preco = custo = estoque = None
    try:
        preco = _numero(dados.get("preco"))
        if preco is None or preco <= 0:
            erros.append("Sem preço de venda.")
    except ValueError:
        erros.append("Preço de venda inválido.")
    try:
        custo = _numero(dados.get("custo"))
        if custo is not None and custo < 0:
            erros.append("Custo negativo.")
    except ValueError:
        erros.append("Custo inválido.")
    try:
        estoque = _numero(dados.get("estoque"))
    except ValueError:
        erros.append("Estoque inválido.")
    if estoque is not None and estoque < 0:
        avisos.append(f"Estoque negativo ({estoque.normalize():f}) entra como zero.")
        estoque = Decimal(0)

    linha.preco = _centavos(preco) if preco is not None and preco > 0 else None
    linha.custo = _centavos(custo) if custo is not None and custo >= 0 else None
    linha.estoque = float(estoque or 0)

    fiscal, linha.ncm = _fiscal_da_linha(dados, erros)
    if not linha.ncm:
        avisos.append("Sem NCM: preencha antes de emitir nota deste produto.")

    # Código já cadastrado (ou repetido na planilha) nunca sobrescreve.
    if codigo in codigos:
        linha.situacao = "existe"
        linha.mensagens = ["Este código já está cadastrado: nada muda neste produto."]
        return _Analise(linha)

    codigo_barras = _texto(dados.get("codigo_barras"))
    if not codigo_barras.isdigit():
        codigo_barras = ""  # "SEM GTIN" e afins: o produto só fica sem código de barras.
    if codigo_barras and codigo_barras in barras:
        erros.append(f"Código de barras {codigo_barras} já usado em outro produto.")

    for valor, rotulo in ((codigo, "Código"), (codigo_barras, "Código de barras")):
        if valor:
            try:
                codigo_de_produto_livre(db, valor)
            except HTTPException:
                erros.append(f"{rotulo} {valor} já usado em uma embalagem.")

    nome_normalizado = nome.upper()
    if nome_normalizado in nomes:
        avisos.append("Já existe produto com este nome: confira se não é o mesmo.")

    if erros:
        linha.mensagens = erros + avisos
        return _Analise(linha)

    codigos.add(codigo)
    nomes.add(nome_normalizado)
    if codigo_barras:
        barras.add(codigo_barras)

    linha.situacao = "novo"
    linha.mensagens = avisos
    return _Analise(linha, ProdutoCreateComFiscal(
        nome=nome,
        codigo_produto=codigo,
        codigo_barras=codigo_barras or None,
        unidade_medida=unidade,
        categoria=_texto(dados.get("categoria"))[:100] or None,
        estoque=EstoqueCreate(valor_varejo=linha.preco, valor_entrada=linha.custo, quantidade=linha.estoque),
        fiscal=fiscal if usar_fiscal else None,
    ))


def _fiscal_disponivel(db: Session, usuario_token: dict) -> bool:
    """A mesma porta do cadastro: licença com NF-e e fiscal configurado."""
    from app.core.depends import requer_modulo_fiscal

    try:
        requer_modulo_fiscal(usuario_token=usuario_token, db=db)
    except HTTPException:
        return False
    return True


def _analisar(db: Session, conteudo: bytes, usuario_token: dict) -> tuple[list[_Analise], bool, bool]:
    linhas = _ler_planilha(conteudo)
    disponivel = _fiscal_disponivel(db, usuario_token)
    ativos = db.execute(
        select(Produto.codigo_produto, Produto.codigo_barras, Produto.nome).where(Produto.ativo.is_(True))
    ).all()
    codigos = {c for c, _, _ in ativos if c}
    barras = {b for _, b, _ in ativos if b}
    nomes = {n.upper() for _, _, n in ativos if n}
    analises = [_analisar_linha(db, n, d, disponivel, codigos, barras, nomes) for n, d in linhas]
    tem_fiscal = any(d.get(c) not in (None, "") for _, d in linhas for c in ("ncm", "cfop", "csosn"))
    return analises, disponivel, tem_fiscal


def _contar(analises: list[_Analise], situacao: str) -> int:
    return sum(a.linha.situacao == situacao for a in analises)


def ler(db: Session, conteudo: bytes, usuario_token: dict) -> PreviaImportacao:
    """Confere a planilha. Não grava nada."""
    analises, disponivel, tem_fiscal = _analisar(db, conteudo, usuario_token)
    return PreviaImportacao(
        novos=_contar(analises, "novo"),
        ja_existem=_contar(analises, "existe"),
        ignorados=_contar(analises, "ignorado"),
        com_erro=_contar(analises, "erro"),
        fiscal_disponivel=disponivel,
        planilha_tem_fiscal=tem_fiscal,
        linhas=[a.linha for a in analises],
    )


def importar(db: Session, conteudo: bytes, usuario_token: dict) -> ResultadoImportacaoPlanilha:
    """Cria os produtos novos. Relê o arquivo: não confia em nada da tela."""
    analises, _, _ = _analisar(db, conteudo, usuario_token)
    criados = 0
    for analise in analises:
        if analise.produto is not None:
            create_produto(db, analise.produto, usuario_token)
            criados += 1
    return ResultadoImportacaoPlanilha(
        criados=criados,
        ja_existiam=_contar(analises, "existe"),
        ignorados=_contar(analises, "ignorado"),
        com_erro=_contar(analises, "erro"),
    )
