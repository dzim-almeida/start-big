# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/derivacao/cfop.py
# DESCRIÇÃO: Derivação do CFOP e da natureza da operação.
# ---------------------------------------------------------------------------
"""
CFOP derivado da OPERAÇÃO.

O problema conceitual que este módulo resolve: hoje o CFOP é gravado por
PRODUTO (`produto_fiscal.cfop_padrao`) e copiado verbatim para o payload. Mas
CFOP é atributo da operação, não da mercadoria — o mesmo item vendido no
balcão (5102) e entregue em outra UF (6102) tem CFOPs diferentes. Guardar por
produto só funciona hoje porque o motor bloqueia operação interestadual.

DUAS PORTAS DE ENTRADA
- `derivar_cfop(ctx)`: sugestão para o CADASTRO, que não sabe do perfil
  tributário. Numa saída interestadual de item substituído ela se recusa a
  chutar (`DerivacaoAmbiguaError`), a menos que `existe_st_na_regra` chegue.
- `derivar_cfop_operacao(...)`: a EMISSÃO (tax_engine/resolver), que já
  consultou o perfil e sabe se há ST para a UF de destino. Determinística,
  sem ambiguidade. O `idDest` do payload (TASK009) tem que sair da MESMA
  decisão de grupo, senão os dois divergem e a nota é rejeitada.

Regras confirmadas com a contabilidade em 05/09/2026; interestadual em
18/09/2026 (TASK008).
"""
from typing import Optional

from .types import CampoSugerido, Confianca, ContextoDerivacao, Fonte, TipoAtividade

# --- Grupos (1º dígito) ---
GRUPO_INTERNA = 5
GRUPO_INTERESTADUAL = 6

# --- Sufixos (3 últimos dígitos) ---
SUFIXO_PRODUCAO_PROPRIA = 101   # Venda de produção do estabelecimento
SUFIXO_REVENDA = 102            # Venda de mercadoria adquirida de terceiros
SUFIXO_DEVOLUCAO_COMPRA = 202   # Devolução de compra para comercialização
SUFIXO_SUBSTITUIDO = 405        # Venda de merc. sujeita a ST (substituído)
SUFIXO_SERVICO = 933            # Prestação de serviço tributado por ISSQN
# Interestadual (só grupo 6):
SUFIXO_NAO_CONTRIBUINTE_PRODUCAO = 107  # Venda de produção a não contribuinte
SUFIXO_NAO_CONTRIBUINTE_REVENDA = 108   # Venda de merc. de terceiros a não contribuinte
SUFIXO_SUBSTITUTO_PRODUCAO = 403        # Venda de produção com ST retida (substituto)
SUFIXO_SUBSTITUTO_REVENDA = 404         # Venda de merc. de terceiros com ST retida

# indIEDest da NF-e
IND_IE_NAO_CONTRIBUINTE = 9

# CST/CSOSN que indicam mercadoria com ICMS já retido por substituição.
SITUACOES_SUBSTITUIDO = frozenset({"60", "500"})

# Atividades em que a saída é de produção própria — indústria, panificação com
# produção própria, marcenaria, beneficiamento.
#
# MISTO SAIU DAQUI EM 12/09/2026, e o motivo é a etiqueta da tela.
# O cadastro de empresa oferece `MISTO` como **"Misto (Comércio + Serviços)"**
# (`empresa.constants.ts`) — é o que a loja de informática que vende peça e faz
# conserto escolhe, e foi o que aconteceu numa loja real. Com MISTO aqui, a
# sugestão vinha 5101 ("venda de produção do estabelecimento"), que é de quem
# FABRICA. Para revenda o certo é 5102.
#
# Vale a etiqueta que o usuário leu na hora de escolher, não a que o motor
# imaginou. Quem fabrica escolhe "Indústria" e continua recebendo 5101.
ATIVIDADES_PRODUCAO_PROPRIA = frozenset({TipoAtividade.INDUSTRIA})

NATUREZA_POR_CFOP = {
    "5101": "Venda de producao do estabelecimento",
    "5102": "Venda de mercadoria adquirida de terceiros",
    "5202": "Devolucao de compra para comercializacao",
    "5405": "Venda de merc. adq. de terceiros sujeita a ST",
    "5933": "Prestacao de servico",
    "6101": "Venda de producao do estabelecimento",
    "6102": "Venda de mercadoria adquirida de terceiros",
    "6107": "Venda de producao do estabelecimento a nao contribuinte",
    "6108": "Venda de mercadoria adquirida de terceiros a nao contribuinte",
    "6202": "Devolucao de compra para comercializacao",
    "6403": "Venda de producao do estabelecimento sujeita a ST (substituto)",
    "6404": "Venda de merc. adq. de terceiros sujeita a ST (substituto)",
    "6933": "Prestacao de servico",
}

# Naturezas que DESLIGAM o cálculo do vTotTrib na integradora.
# Ver tributos_xml.py: a integradora dispensa o cálculo quando a natureza
# contém uma destas palavras — e o cupom sai sem a linha de tributos
# aproximados, o que infringe a Lei 12.741/2012.
PALAVRAS_QUE_DISPENSAM_TRIBUTOS = ("REMESSA", "EXPORTACAO", "DEVOLUCAO", "LANCAMENTO")

# --- Devolução de venda: CFOP de SAÍDA da nota original -> CFOP de ENTRADA ---
# O primeiro dígito vira 1 (interna) ou 2 (interestadual); o sufixo segue a
# natureza do que foi vendido. Mapa confirmado com a contabilidade para a
# TASK003; o que não estiver aqui cai no genérico "devolução de venda de
# mercadoria adquirida de terceiros" (1202/2202), que evita a Rejeição 327
# sem inventar ST onde não havia.
SUFIXOS_DEVOLUCAO_DE_VENDA = {
    101: 201,   # venda de produção própria      -> devolução de venda de produção
    102: 202,   # venda de mercadoria de terceiros -> devolução de venda de mercadoria
    403: 411,   # venda com ST (substituto)        -> devolução de venda sujeita a ST
    404: 411,
    405: 411,   # venda de mercadoria substituída  -> idem
}
SUFIXO_DEVOLUCAO_PADRAO = 202
GRUPO_ENTRADA_INTERNA = 1
GRUPO_ENTRADA_INTERESTADUAL = 2


def cfop_devolucao(cfop_saida: Optional[str], interestadual: bool) -> str:
    """CFOP de entrada da NF-e de devolução a partir do CFOP de saída original."""
    grupo = GRUPO_ENTRADA_INTERESTADUAL if interestadual else GRUPO_ENTRADA_INTERNA
    sufixo = SUFIXO_DEVOLUCAO_PADRAO
    if cfop_saida and len(cfop_saida) == 4 and cfop_saida.isdigit():
        sufixo = SUFIXOS_DEVOLUCAO_DE_VENDA.get(int(cfop_saida[1:]), SUFIXO_DEVOLUCAO_PADRAO)
    return f"{grupo}{sufixo:03d}"


class DerivacaoAmbiguaError(ValueError):
    """
    A regra reconhece a situação e se recusa a chutar.

    Existe porque, em matéria fiscal, o silêncio é melhor que o palpite: uma
    nota ACEITA e errada custa multa e juros, enquanto uma emissão interrompida
    custa cinco minutos.
    """


def _grupo_por_destino(ctx: ContextoDerivacao) -> int:
    """
    1º dígito do CFOP: para onde a mercadoria vai.

    NFC-e é sempre interna. Venda presencial também: a mercadoria sai pelo
    balcão e não cruza fronteira, mesmo que o comprador more em outra UF —
    é o mesmo raciocínio da trava em `tax_engine/resolver.py`.
    """
    if ctx.modelo_documento == 65:
        return GRUPO_INTERNA
    if ctx.indicador_presenca == 1:
        return GRUPO_INTERNA
    if ctx.uf_destinatario and ctx.uf_destinatario.upper() != ctx.uf_emitente.upper():
        return GRUPO_INTERESTADUAL
    return GRUPO_INTERNA


def _sufixo_interestadual(
    indicador_ie_destinatario: int, existe_st_na_regra: bool, eh_producao_propria: bool,
) -> int:
    """3 últimos dígitos de uma saída interestadual, pela operação."""
    if indicador_ie_destinatario == IND_IE_NAO_CONTRIBUINTE:
        # Consumidor final: não há cadeia seguinte, ST não se aplica (DIFAL sim).
        return SUFIXO_NAO_CONTRIBUINTE_PRODUCAO if eh_producao_propria else SUFIXO_NAO_CONTRIBUINTE_REVENDA
    if existe_st_na_regra:
        return SUFIXO_SUBSTITUTO_PRODUCAO if eh_producao_propria else SUFIXO_SUBSTITUTO_REVENDA
    return SUFIXO_PRODUCAO_PROPRIA if eh_producao_propria else SUFIXO_REVENDA


def derivar_cfop_operacao(
    uf_emitente: str,
    uf_destinatario: Optional[str],
    indicador_presenca: Optional[int],
    indicador_ie_destinatario: int,
    existe_st_na_regra: bool,
    eh_producao_propria: bool = False,
) -> str:
    """
    CFOP de saída de mercadoria decidido pela OPERAÇÃO, sem ambiguidade.

    Quem chama já consultou o perfil tributário: `existe_st_na_regra` é o
    `mva_st` da regra para a UF de destino. Interna (mesma UF, ou presencial,
    ou sem UF) fica no grupo 5; o resto vai para o 6 conforme o destinatário.

    Args:
        indicador_ie_destinatario: indIEDest (1 contribuinte, 2 isento, 9 não).
    """
    interna = (
        indicador_presenca == 1
        or not uf_destinatario
        or uf_destinatario.upper() == uf_emitente.upper()
    )
    if interna:
        if existe_st_na_regra:
            sufixo = SUFIXO_SUBSTITUIDO
        else:
            sufixo = SUFIXO_PRODUCAO_PROPRIA if eh_producao_propria else SUFIXO_REVENDA
        return f"{GRUPO_INTERNA}{sufixo}"

    sufixo = _sufixo_interestadual(indicador_ie_destinatario, existe_st_na_regra, eh_producao_propria)
    return f"{GRUPO_INTERESTADUAL}{sufixo}"


def derivar_cfop(
    ctx: ContextoDerivacao,
    *,
    situacao_tributaria: Optional[str] = None,
    tipo_item: str = "PRODUTO",
    existe_st_na_regra: Optional[bool] = None,
) -> CampoSugerido:
    """
    CFOP de saída para um item.

    Args:
        ctx: Contexto da operação.
        situacao_tributaria: CST (regime normal) ou CSOSN (Simples) do item.
        tipo_item: "PRODUTO" ou "SERVICO".
        existe_st_na_regra: o que o perfil tributário diz da UF de destino.
            None = não se sabe (cadastro), e a saída interestadual de item
            substituído continua ambígua.

    Raises:
        DerivacaoAmbiguaError: numa saída interestadual de item substituído
            SEM a resposta do perfil. Não existe equivalente interestadual
            limpo do 5.405 — confirmado com a contabilidade. Nessa operação o
            remetente costuma assumir o papel de SUBSTITUTO (6.403/6.404) por
            forca de protocolo, e ainda cabe pedido de ressarcimento do ICMS-ST
            pago na compra. Quem decide isso é o contador — pelo perfil.
    """
    grupo = _grupo_por_destino(ctx)
    substituido = (situacao_tributaria or "") in SITUACOES_SUBSTITUIDO
    producao_propria = ctx.tipo_atividade in ATIVIDADES_PRODUCAO_PROPRIA

    if tipo_item == "SERVICO":
        sufixo = SUFIXO_SERVICO
        motivo = "prestacao de servico em documento de mercadoria"
    elif ctx.finalidade_emissao == 4:
        sufixo = SUFIXO_DEVOLUCAO_COMPRA
        motivo = "finalidade de devolucao de compra, em operacao de SAIDA"
    elif substituido and grupo == GRUPO_INTERESTADUAL:
        if existe_st_na_regra is None:
            raise DerivacaoAmbiguaError(
                "Saida interestadual de mercadoria com ICMS-ST retido nao tem "
                "CFOP derivavel: nao existe equivalente limpo do 5.405. "
                "Dependendo do protocolo entre as UFs a operacao vira 6.102 ou "
                "6.403/6.404, com o remetente como substituto. Informe o CFOP "
                "manualmente, com orientacao da contabilidade."
            )
        ind_ie = 1 if ctx.destinatario_pj_com_ie else IND_IE_NAO_CONTRIBUINTE
        sufixo = _sufixo_interestadual(ind_ie, existe_st_na_regra, producao_propria)
        motivo = "saida interestadual decidida pelo perfil tributario"
    elif substituido:
        sufixo = SUFIXO_SUBSTITUIDO
        motivo = f"mercadoria com ICMS retido por ST (situacao {situacao_tributaria})"
    elif producao_propria:
        sufixo = SUFIXO_PRODUCAO_PROPRIA
        motivo = f"saida de producao propria (atividade {ctx.tipo_atividade.value})"
    else:
        sufixo = SUFIXO_REVENDA
        motivo = "revenda de mercadoria adquirida de terceiros"

    cfop = f"{grupo}{sufixo}"
    onde = "interna" if grupo == GRUPO_INTERNA else "interestadual"

    # Produção própria depende do ITEM, não só da empresa: uma padaria vende
    # pão próprio (5101) e refrigerante revendido (5102) na mesma nota. O CNAE
    # decide o default; o produto sobrescreve.
    confianca = (
        Confianca.PROVAVEL
        if sufixo == SUFIXO_PRODUCAO_PROPRIA
        else Confianca.CERTA
    )

    return CampoSugerido(
        campo="cfop_padrao",
        valor=cfop,
        fonte=Fonte.DERIVADO,
        confianca=confianca,
        fundamentacao=f"CFOP {cfop} — operacao {onde}, {motivo}.",
        alternativas=(
            [(f"{grupo}{SUFIXO_REVENDA}", "Revenda de mercadoria de terceiros")]
            if sufixo == SUFIXO_PRODUCAO_PROPRIA
            else []
        ),
    )


def derivar_natureza_operacao(cfop: str) -> CampoSugerido:
    """
    Descrição oficial da operação, a partir do CFOP.

    ⚠️ ARMADILHA: naturezas com REMESSA / EXPORTACAO / DEVOLUCAO / LANCAMENTO
    fazem a integradora DISPENSAR o cálculo do `vTotTrib` (ver tributos_xml.py).
    O cupom sai sem a linha de tributos aproximados — infração à Lei
    12.741/2012. Por isso a devolução vem com `exige_confirmacao`.
    """
    descricao = NATUREZA_POR_CFOP.get(cfop, "Venda de Mercadoria")
    dispensa_tributos = any(
        palavra in descricao.upper() for palavra in PALAVRAS_QUE_DISPENSAM_TRIBUTOS
    )

    fundamentacao = f"Descricao oficial do CFOP {cfop}."
    if dispensa_tributos:
        fundamentacao += (
            " ATENCAO: esta natureza faz a integradora nao calcular os tributos "
            "aproximados (Lei 12.741/2012) — confira a linha no cupom."
        )

    return CampoSugerido(
        campo="natureza_operacao",
        valor=descricao,
        fonte=Fonte.DERIVADO,
        confianca=Confianca.CERTA,
        fundamentacao=fundamentacao,
        exige_confirmacao=dispensa_tributos,
    )
