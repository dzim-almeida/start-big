# ---------------------------------------------------------------------------
# ARQUIVO: app/services/regras_preco.py
# MÓDULO: Service — Regras de preço por quantidade (plano de embalagens, §6.1)
# ---------------------------------------------------------------------------
"""
Duas partes:

1. O cadastro das regras do produto (R2 faixas, R3 leve-pague), replace-all.
2. `aplicar_na_venda`: recalcula as regras do carrinho inteiro. Roda a cada
   mudança nos itens (`venda._recalc_total_sale`) e na conversão do orçamento.
   NÃO roda na finalização: o que o caixa viu na tela é o que ele cobra.

O que a aplicação garante:
- Só mexe em linha de UNIDADE de produto cadastrado (fator 1). Fardo vendido
  como fardo já tem o preço dele; avulso não tem regra; linha com preço trocado
  pelo gerente (`MANUAL`) fica como o gerente deixou.
- Chave desligada = a regra sai das linhas em aberto (volta o preço cheio). Com
  as três desligadas, a venda fica exatamente como antes (B8).
- O desconto do OPERADOR nunca passa do que sobra depois da regra, e é zerado
  na linha com regra quando a loja liga `bloquear_desconto_com_regra`.
"""

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import regras_preco as calc
from app.core.embalagem import preco_da_embalagem
from app.core.enum import TipoProdutoVenda
from app.db.models.produto import Produto
from app.db.models.produto_regra_preco import ProdutoRegraPreco
from app.schemas.produto_regra_preco import RegrasPrecoSalvar
from app.schemas.quantidade import normalizar_quantidade
from app.services.quantidade_venda import eh_fracionavel, subtotal_da_linha

CAMPOS = ("tipo", "quantidade", "preco", "pague", "inicio", "fim", "ativo")
MANUAL = "MANUAL"


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------

def _produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return produto


def listar(db: Session, produto_id: int) -> list[ProdutoRegraPreco]:
    return list(_produto(db, produto_id).regras_preco)


def salvar(db: Session, produto_id: int, dados: RegrasPrecoSalvar) -> list[ProdutoRegraPreco]:
    """Replace-all: atualiza as que vieram com id, cria as sem id, apaga as que não vieram."""
    produto = _produto(db, produto_id)
    existentes = {r.id: r for r in produto.regras_preco}

    for item in dados.regras:
        if item.id is not None and item.id not in existentes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A regra {item.id} não é deste produto.",
            )

    manter = {r.id for r in dados.regras if r.id is not None}
    for regra_id, regra in existentes.items():
        if regra_id not in manter:
            produto.regras_preco.remove(regra)
    db.flush()

    for item in dados.regras:
        regra = existentes[item.id] if item.id is not None else ProdutoRegraPreco(produto_id=produto.id)
        for campo in CAMPOS:
            setattr(regra, campo, getattr(item, campo))
        if item.id is None:
            produto.regras_preco.append(regra)
    db.flush()
    db.refresh(produto)
    return list(produto.regras_preco)


# ---------------------------------------------------------------------------
# Aplicação na venda
# ---------------------------------------------------------------------------

def _estado(linha) -> tuple:
    return (linha.valor_unitario, linha.subtotal, linha.desconto, linha.desconto_regra, linha.regra_preco)


def _limpar(linha) -> None:
    """Tira a regra da linha e devolve o preço cheio (o R2 guardou em `valor_unitario_tabela`)."""
    if linha.regra_preco not in calc.REGRAS:
        return
    if linha.regra_preco == "R2" and linha.valor_unitario_tabela is not None:
        linha.valor_unitario = linha.valor_unitario_tabela
    linha.regra_preco = None
    linha.regra_descricao = None
    linha.valor_unitario_tabela = None
    linha.desconto_regra = 0
    linha.subtotal = subtotal_da_linha(linha.quantidade or 0, linha.valor_unitario or 0)


def _participa(linha) -> bool:
    return (
        linha.tipo_produto == TipoProdutoVenda.CADASTRADO
        and linha.produto_id is not None
        and linha.produto is not None
        and (linha.fator_embalagem or 1) == 1
        and linha.regra_preco != MANUAL
    )


def _ratear(total: int, linhas: list) -> list[int]:
    """Divide `total` pelas linhas na proporção do subtotal; a última leva o resto."""
    base = sum(l.subtotal for l in linhas) or 1
    partes, restante = [], total
    for i, linha in enumerate(linhas):
        parte = restante if i == len(linhas) - 1 else (total * linha.subtotal) // base
        partes.append(parte)
        restante -= parte
    return partes


def _entradas(produto: Produto, r1: bool, r2: bool, r3: bool, hoje: date) -> dict:
    embalagens, faixas, leve_pague = [], [], []
    if r1:
        preco_unidade = produto.estoque.valor_varejo if produto.estoque else 0
        embalagens = [
            calc.EmbalagemR1(e.sigla, e.fator, preco_da_embalagem(e.fator, e.preco, e.desconto_bp, preco_unidade))
            for e in produto.embalagens
            if e.ativo and e.vende_no_pdv and e.aplica_as_avulsas and e.fator >= 2
        ]
    if r2 or r3:
        for regra in produto.regras_preco:
            if not regra.vigente_em(hoje):
                continue
            if r2 and regra.tipo == "FAIXA" and regra.preco is not None:
                faixas.append(calc.FaixaR2(regra.quantidade, regra.preco))
            elif r3 and regra.tipo == "LEVE_PAGUE" and regra.pague is not None:
                leve_pague.append(calc.LevePagueR3(regra.quantidade, regra.pague))
    return {"embalagens": embalagens, "faixas": faixas, "leve_pague": leve_pague}


def aplicar_na_venda(db: Session, venda, hoje: Optional[date] = None) -> set[int]:
    """Recalcula as regras de preço do carrinho. Devolve os ids das linhas que
    mudaram (a tela precisa trocar as outras linhas do mesmo produto também)."""
    from app.db.crud import configuracao_vendas as config_vendas_crud
    from app.services.produto_embalagem import embalagens_ligadas

    itens = list(venda.itens)
    if not itens:
        return set()
    antes = {l.id: _estado(l) for l in itens}

    empresa_id = venda.funcionario.empresa_id if venda.funcionario else None
    config = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id) if empresa_id else None
    r1 = bool(config and config.regra_embalagem_avulsas) and embalagens_ligadas(db, empresa_id)
    r2 = bool(config and config.regra_faixas_quantidade)
    r3 = bool(config and config.regra_leve_pague)

    # B8: loja sem regra ligada e carrinho sem regra antiga — não toca em nada.
    if not (r1 or r2 or r3) and not any(l.regra_preco in calc.REGRAS for l in itens):
        return set()

    for linha in itens:
        _limpar(linha)

    if r1 or r2 or r3:
        hoje = hoje or date.today()
        ordem = (config.regra_ordem or "").split(",")
        grupos: dict[tuple[int, int], list] = {}
        for linha in itens:
            if _participa(linha):
                grupos.setdefault((linha.produto_id, linha.valor_unitario or 0), []).append(linha)

        for (_, preco_unidade), linhas in grupos.items():
            # A coluna é Float desde a venda fracionada: 17 latas chegam 17.0, e
            # a descrição sairia "Preço de 1.0 FD". Inteiro volta a ser inteiro.
            unidades = normalizar_quantidade(sum(l.quantidade or 0 for l in linhas))
            # Produto fracionado (3,5 kg) só entra na FAIXA "a partir de X":
            # fardo e leve-pague contam unidades inteiras (venda fracionada D5).
            fracionado = eh_fracionavel(linhas[0].produto)
            resultado = calc.calcular(
                unidades,
                preco_unidade,
                conflito=config.regra_conflito,
                ordem=ordem,
                **_entradas(linhas[0].produto, r1 and not fracionado, r2, r3 and not fracionado, hoje),
            )
            if resultado is None:
                continue
            for linha, parte in zip(linhas, _ratear(resultado.desconto, linhas)):
                linha.regra_preco = resultado.regra
                linha.regra_descricao = resultado.descricao
                if resultado.preco_unitario is not None:
                    linha.valor_unitario_tabela = linha.valor_unitario
                    linha.valor_unitario = resultado.preco_unitario
                    linha.subtotal = subtotal_da_linha(linha.quantidade or 0, resultado.preco_unitario)
                else:
                    linha.desconto_regra = parte

    bloquear = bool(config and config.bloquear_desconto_com_regra)
    for linha in itens:
        if bloquear and linha.regra_preco in calc.REGRAS:
            linha.desconto = 0
        livre = max(0, (linha.subtotal or 0) - (linha.desconto_regra or 0))
        if (linha.desconto or 0) > livre:
            linha.desconto = livre

    return {l.id for l in itens if _estado(l) != antes[l.id]}
