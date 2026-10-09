# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_calculo.py
# DESCRICAO: Traducao banco <-> motor da Spec 05 (Spec 06A, secao 7.2).
# ---------------------------------------------------------------------------
"""
Este arquivo NAO calcula nada: monta a entrada do motor
(`app/services/marcenaria/calculo.py`) a partir do que esta no banco e
devolve o resultado. A conta mora num lugar so (C8).

Os valores calculados nunca sao gravados como fonte da verdade (D5): a cada
leitura o motor recalcula. So o RESUMO do cabecalho (para a lista) e
atualizado a cada escrita.
"""

from typing import Optional

from app.db.models.marcenaria.ambiente import MarcenariaMovel
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
from app.services.marcenaria import erros
from app.services.marcenaria.calculo import (
    AjusteCalc,
    AmbienteCalc,
    InsumoCalc,
    MovelCalc,
    OrcamentoCalc,
    OrcamentoResultado,
    calcular_orcamento,
)

# Troca de preco de um insumo (sem gravar): {insumo_id: (custo, origem, sofre_perda)}.
Trocas = dict[int, tuple[int, str, bool]]


def movel_para_calc(movel: MarcenariaMovel, trocas: Optional[Trocas] = None) -> MovelCalc:
    """Um movel do banco na forma que o motor entende.

    `trocas` (opcional) poe o custo de HOJE em alguns insumos, para a previa
    de "precos desatualizados" sem gravar nada.
    """
    trocas = trocas or {}
    insumos = []
    for insumo in movel.insumos:
        custo, perda = insumo.custo_unit_centavos, insumo.sofre_perda
        if insumo.id in trocas:                             # previa com o preco de hoje
            custo, _origem, perda = trocas[insumo.id]
        insumos.append(InsumoCalc(
            quantidade_milesimos=insumo.quantidade_milesimos,
            custo_unit_centavos=custo,
            sofre_perda=perda,
        ))
    return MovelCalc(
        id=str(movel.id),
        quantidade=movel.quantidade,
        insumos=tuple(insumos),
        mao_obra_modo=movel.mao_obra_modo,
        mao_obra_centavos=movel.mao_obra_centavos,
        mao_obra_horas_centesimos=movel.mao_obra_horas_centesimos,
        terceirizado_centavos=movel.terceirizado_centavos,
    )


def soma_rt_bp(orc: MarcenariaOrcamento) -> int:
    """O motor recebe a SOMA dos percentuais dos arquitetos (D7)."""
    return sum(rt.rt_bp for rt in orc.rts)


def montar_entrada_motor(
    orc: MarcenariaOrcamento,
    so_aprovados: bool = False,
    trocas: Optional[Trocas] = None,
) -> OrcamentoCalc:
    """Converte o orcamento do banco na entrada da Spec 05.

    so_aprovados=True e usado pela Spec 08A (aprovacao parcial, O4): so
    entram os moveis com aprovado=True. Aqui (06A) e sempre False.
    """
    ambientes = tuple(
        AmbienteCalc(
            id=str(amb.id),
            moveis=tuple(
                movel_para_calc(m, trocas)
                for m in sorted(amb.moveis, key=lambda m: (m.ordem, m.id))
                if not so_aprovados or m.aprovado
            ),
        )
        for amb in sorted(orc.ambientes, key=lambda a: (a.ordem, a.id))
    )
    return OrcamentoCalc(
        ambientes=ambientes,
        markup_bp=orc.markup_bp,
        perda_bp=orc.perda_bp,
        custo_hora_centavos=orc.custo_hora_centavos,
        rt_bp=soma_rt_bp(orc),
        rt_modo=orc.rt_modo,
        instalacao_custo_centavos=orc.instalacao_custo_centavos,
        desconto=AjusteCalc(orc.desconto_modo, orc.desconto_valor),
        sinal=AjusteCalc(orc.sinal_modo, orc.sinal_valor),
    )


def _campo_do_erro(entrada: OrcamentoCalc, mensagem: str) -> Optional[str]:
    """Qual campo da tela a mensagem do motor aponta (secao 6.9, Revisao 1).

    O motor devolve so a frase; aqui se descobre o campo pela validacao que
    falhou, olhando a propria entrada. Sem campo claro, None (erro geral).
    """
    texto = mensagem.lower()
    if "desconto" in texto and "sinal" not in texto:
        return "desconto"
    if "sinal" in texto and "desconto" not in texto:
        return "sinal"
    if "markup" in texto:
        return "markup"
    if "perda" in texto:
        return "perda"
    # Frases genericas: decide pelo valor que esta fora da regra.
    for campo, ajuste in (("desconto", entrada.desconto), ("sinal", entrada.sinal)):
        fora = ajuste.valor < 0 or (ajuste.modo == "PERCENTUAL" and ajuste.valor > 10_000)
        if fora or ajuste.modo not in ("PERCENTUAL", "VALOR"):
            return campo
    if "negativ" in texto:
        if entrada.custo_hora_centavos < 0:
            return "custo_hora"
        if entrada.markup_bp < 0:
            return "markup"
        if entrada.perda_bp < 0:
            return "perda"
    return None


def calcular(entrada: OrcamentoCalc) -> OrcamentoResultado:
    """Chama o motor. Erro de validacao vira 422 CALCULO_INVALIDO com `campo`.

    Quem chama dentro de uma escrita desfaz a transacao (o endpoint faz o
    rollback ao ver a HTTPException): nada fica gravado (secao 7.2).
    """
    try:
        return calcular_orcamento(entrada)
    except ValueError as erro:
        erros.calculo_invalido(str(erro), _campo_do_erro(entrada, str(erro)))


def calcular_orcamento_do_banco(orc: MarcenariaOrcamento, trocas: Optional[Trocas] = None) -> OrcamentoResultado:
    """Atalho: monta a entrada do orcamento e calcula."""
    return calcular(montar_entrada_motor(orc, trocas=trocas))


def atualizar_resumo(orc: MarcenariaOrcamento, resultado: OrcamentoResultado) -> None:
    """Grava o resumo da LISTA no cabecalho (D5). O detalhe nunca usa o resumo."""
    orc.resumo_bruto_centavos = resultado.bruto_centavos
    orc.resumo_total_centavos = resultado.total_centavos
    orc.resumo_margem_bp = resultado.margem_liquida_bp
    orc.resumo_qtd_moveis = sum(len(amb.moveis) for amb in resultado.ambientes)
