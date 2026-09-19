# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/tax_engine/resolver.py
# DESCRIÇÃO: Ponte entre o banco de dados e os DTOs puros do tax_engine.
#            ÚNICO arquivo do tax_engine que importa modelos ORM.
#
# Responsabilidades:
#   - Resolver alíquotas: override do produto > default da UF
#   - Converter centavos (int) → Decimal reais
#   - Operação interestadual: DIFAL para não contribuinte (TASK007), ICMS-ST
#     para contribuinte (TASK008), CFOP/CST da operação — tudo pelo perfil
#     tributário do produto
#   - Montar ItemEntrada e DadosNota para o engine
# ---------------------------------------------------------------------------

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models.aliquota_uf import AliquotaUF
from app.db.models.cliente import ClientePJ
from app.db.models.produto_fiscal import ProdutoFiscal
from app.services.fiscal.derivacao.cfop import (
    IND_IE_NAO_CONTRIBUINTE,
    SUFIXO_PRODUCAO_PROPRIA,
    derivar_cfop_operacao,
)
from app.services.fiscal.derivacao.situacao import derivar_situacao_operacao
from app.services.fiscal.tributacao import fiscal_efetivo
from app.db.models.venda import Venda

from .constants import (
    COFINS_CUMULATIVO,
    COFINS_NAO_CUMULATIVO,
    CST_PIS_COFINS_SIMPLES,
    PIS_CUMULATIVO,
    PIS_NAO_CUMULATIVO,
)
from .exceptions import (
    AliquotaNaoEncontradaError,
    DadosFiscaisAusentesError,
    OperacaoInterestadualError,
)
from .perfil_resolver import resolver_regra_perfil
from .types import DadosNota, ItemEntrada


ZERO = Decimal("0")
IND_IE_CONTRIBUINTE = 1


def _centesimos_para_decimal(valor: Optional[int], padrao: Decimal) -> Decimal:
    """
    Converte centésimos de ponto percentual (int, ex: 1800) para Decimal (18.00).
    Se valor for None, retorna o padrão.
    """
    if valor is None:
        return padrao
    return Decimal(valor) / Decimal("100")


def _centavos_para_reais(centavos: int) -> Decimal:
    """Converte centavos (int) para Decimal em reais."""
    return Decimal(centavos) / Decimal("100")


# indPres da NF-e: 1 = operação presencial. Os demais (2=internet,
# 3=teleatendimento, 4=NFC-e entrega, 9=outros não presenciais) implicam
# circulação da mercadoria e podem ser interestaduais de verdade.
INDPRES_PRESENCIAL = 1


def _operacao_presencial(venda: Venda) -> bool:
    """
    Se a venda é de balcão.

    Sem dados fiscais preenchidos assume presencial — é o caso do PDV, que é
    o uso dominante do sistema.
    """
    nota_fiscal = getattr(venda, "nota_fiscal", None)
    if not nota_fiscal or nota_fiscal.indicador_presenca is None:
        return True
    return nota_fiscal.indicador_presenca == INDPRES_PRESENCIAL


def _obter_uf_cliente(venda: Venda) -> Optional[str]:
    """Obtém a UF do primeiro endereço do cliente da venda, se existir."""
    if not venda.cliente:
        return None

    enderecos = venda.cliente.endereco
    if not enderecos:
        return None

    estado = enderecos[0].estado
    if hasattr(estado, "value"):
        return str(estado.value)
    return str(estado) if estado else None


def _cliente_nao_contribuinte(venda: Venda) -> bool:
    """
    Mesma régua do payload builder para o indIEDest: PF, PJ sem IE e venda
    sem cliente são não contribuintes (9); só PJ com IE é contribuinte (1).

    Decide a rota interestadual: DIFAL para não contribuinte (TASK007),
    ICMS-ST para contribuinte (TASK008).
    """
    cliente = venda.cliente
    if cliente is None or not isinstance(cliente, ClientePJ):
        return True
    return not bool(cliente.ie)


@dataclass(frozen=True)
class _Operacao:
    """Uma operação interestadual de verdade: para onde vai e para quem."""

    uf_destino: str
    nao_contribuinte: bool


@dataclass(frozen=True)
class _DadosDIFAL:
    aliquota_interestadual: Decimal
    aliquota_interna_destino: Decimal
    percentual_fcp: Decimal
    base_dupla: bool


@dataclass(frozen=True)
class _DadosST:
    aliquota_interestadual: Decimal
    aliquota_interna_destino: Decimal
    mva: Decimal
    reducao_base: Optional[Decimal]


@dataclass(frozen=True)
class _ItemInterestadual:
    """O que muda num item por causa da operação interestadual."""

    cfop: str
    cst_icms: Optional[str]
    csosn: Optional[str]
    aliquota_icms: Optional[Decimal]     # None = manter a do produto/UF
    difal: Optional[_DadosDIFAL] = None  # não contribuinte, regime normal
    st: Optional[_DadosST] = None        # contribuinte com MVA na regra


def _operacao_interestadual(venda: Venda, uf_emitente: str) -> Optional[_Operacao]:
    """
    A operação quando é interestadual DE VERDADE, senão None.

    O critério é a operação, não o endereço cadastrado do cliente. Numa venda
    presencial a mercadoria sai pelo balcão e não cruza fronteira — é interna
    mesmo que o comprador more em outra UF. Travar por endereço impedia
    faturar para qualquer cliente de fora, sem irregularidade alguma.
    """
    if _operacao_presencial(venda):
        return None
    uf_cliente = _obter_uf_cliente(venda)
    if not uf_cliente or uf_cliente.upper() == uf_emitente.upper():
        return None
    return _Operacao(uf_destino=uf_cliente.upper(), nao_contribuinte=_cliente_nao_contribuinte(venda))


def _regra_do_perfil(db: Session, fiscal: Any, produto: Any, uf_destino: str, idx: int):
    """
    A regra do perfil tributário do produto para a UF de destino.

    Sem perfil ou sem regra a venda não pode sair: seria uma nota com
    DIFAL/ST errado, aceita pela SEFAZ e cobrada depois.
    """
    perfil_id = getattr(fiscal, "perfil_tributario_id", None)
    nome = getattr(produto, "nome", "?")
    if perfil_id is None:
        raise OperacaoInterestadualError(
            f"Produto '{nome}' (item {idx}) não possui perfil tributário "
            f"configurado. Para vendas interestaduais, todos os produtos devem "
            f"ter um perfil tributário vinculado.",
            campo="perfil_tributario_id",
            item=idx,
        )

    regra = resolver_regra_perfil(db, perfil_id, uf_destino, getattr(fiscal, "ncm", None))
    if regra is None:
        raise OperacaoInterestadualError(
            f"Perfil tributário do produto '{nome}' (item {idx}) não possui "
            f"regra aplicável para a UF {uf_destino}.",
            campo="perfil_tributario_id",
            item=idx,
        )
    return regra


def _resolver_item_interestadual(
    db: Session,
    fiscal: Any,
    produto: Any,
    operacao: _Operacao,
    uf_emitente: str,
    simples_nacional: bool,
    idx: int,
) -> _ItemInterestadual:
    """
    A encruzilhada interestadual, por item:

      não contribuinte, regime normal → DIFAL pelo perfil (TASK007); ICMS
          próprio pela alíquota interestadual; CFOP 6107/6108.
      não contribuinte, Simples      → sem DIFAL e sem perfil: o remetente
          optante não recolhe o DIFAL de partilha (STF, ADI 5464 — cláusula
          nona do Conv. 93/2015 suspensa). PREMISSA LEGAL a confirmar com o
          contador (docs da TASK007). Só o CFOP muda.
      contribuinte (PJ com IE)       → perfil obrigatório nos dois regimes:
          é o `mva_st` da regra que diz se o remetente é substituto
          (ICMS-ST, CFOP 6403/6404, CST 10/70 ou CSOSN 201/202) ou se é uma
          revenda interestadual comum (6101/6102, situação do produto).
    """
    regra = None
    if not (operacao.nao_contribuinte and simples_nacional):
        regra = _regra_do_perfil(db, fiscal, produto, operacao.uf_destino, idx)

    existe_st = (
        not operacao.nao_contribuinte and regra is not None and (regra.mva_st or 0) > 0
    )
    cfop_produto = getattr(fiscal, "cfop_padrao", None) or ""
    cfop = derivar_cfop_operacao(
        uf_emitente=uf_emitente,
        uf_destinatario=operacao.uf_destino,
        indicador_presenca=None,
        indicador_ie_destinatario=IND_IE_NAO_CONTRIBUINTE if operacao.nao_contribuinte else IND_IE_CONTRIBUINTE,
        existe_st_na_regra=existe_st,
        eh_producao_propria=cfop_produto.endswith(str(SUFIXO_PRODUCAO_PROPRIA)),
    )
    situacao = derivar_situacao_operacao(
        getattr(fiscal, "cst_icms", None), getattr(fiscal, "csosn", None),
        simples=simples_nacional, existe_st=existe_st,
        tem_reducao=bool(getattr(fiscal, "reducao_base_icms", None)),
    )
    item = _ItemInterestadual(
        cfop=cfop,
        cst_icms=getattr(fiscal, "cst_icms", None) if simples_nacional else situacao,
        csosn=situacao if simples_nacional else getattr(fiscal, "csosn", None),
        aliquota_icms=None,
    )
    if regra is None:
        return item
    return _aplicar_regra(item, regra, operacao.nao_contribuinte, existe_st, simples_nacional)


def _aplicar_regra(
    item: _ItemInterestadual, regra: Any, nao_contribuinte: bool, existe_st: bool, simples_nacional: bool,
) -> _ItemInterestadual:
    """As alíquotas da regra viram DIFAL (não contribuinte) ou ST (contribuinte com MVA)."""
    inter = _centesimos_para_decimal(regra.aliquota_interestadual, ZERO)
    interna = _centesimos_para_decimal(regra.aliquota_interna_destino, ZERO)

    if nao_contribuinte:
        difal = _DadosDIFAL(
            aliquota_interestadual=inter,
            aliquota_interna_destino=interna,
            percentual_fcp=_centesimos_para_decimal(regra.percentual_fcp, ZERO),
            base_dupla=bool(regra.calculo_base_dupla),
        )
        return replace(item, aliquota_icms=inter, difal=difal)

    st = None
    if existe_st:
        st = _DadosST(
            aliquota_interestadual=inter,
            aliquota_interna_destino=interna,
            mva=_centesimos_para_decimal(regra.mva_st, ZERO),
            reducao_base=_centesimos_para_decimal(regra.reducao_base_calculo, ZERO) if regra.reducao_base_calculo else None,
        )
    # No Simples o ICMS próprio não é destacado: a alíquota fica como está.
    return replace(item, aliquota_icms=None if simples_nacional else inter, st=st)


def resolver_aliquotas_venda(
    db: Session,
    venda: Venda,
    uf_emitente: str,
    simples_nacional: bool,
    excluir_icms_base_pis_cofins: bool = False,
    regime_apuracao: str = "CUMULATIVO",
) -> tuple[list[ItemEntrada], DadosNota]:
    """
    Converte uma Venda (ORM) em DTOs puros para o tax_engine.

    Resolução de alíquotas: ProdutoFiscal (override) > AliquotaUF (default).

    Args:
        db: Sessão SQLAlchemy.
        venda: Modelo Venda com itens e cliente carregados.
        uf_emitente: UF do emitente (ex: "SP").
        simples_nacional: Se empresa é do Simples Nacional.
        excluir_icms_base_pis_cofins: Flag STF Tema 69.
        regime_apuracao: "CUMULATIVO" (Lucro Presumido) ou "NAO_CUMULATIVO"
            (Lucro Real). Decide o default de PIS/COFINS. Ignorado no Simples.

    Returns:
        Tupla (itens_entrada, dados_nota) pronta para calcular_impostos().

    Raises:
        OperacaoInterestadualError: operação interestadual com item sem perfil
            tributário ou sem regra para a UF de destino (exceto não
            contribuinte no Simples, que dispensa o perfil).
        AliquotaNaoEncontradaError: se UF do emitente não tem registro na tabela.
        DadosFiscaisAusentesError: se produto não tem ProdutoFiscal.
    """
    # 0. Operação interestadual (None = interna ou balcão). Por item, decide
    #    CFOP, CST/CSOSN, DIFAL ou ST — ver _resolver_item_interestadual.
    operacao = _operacao_interestadual(venda, uf_emitente)

    # 1. Carregar defaults da UF
    from app.db.crud import fiscal as crud
    aliq_uf = crud.get_aliquota_uf(db, uf_emitente)

    if not aliq_uf and not simples_nacional:
        raise AliquotaNaoEncontradaError(
            f"Alíquota padrão não encontrada para UF '{uf_emitente}'. "
            f"Verifique a tabela aliquota_uf.",
            campo="uf_emitente",
        )

    # ICMS é estadual: o default vem da UF.
    icms_padrao = _centesimos_para_decimal(
        aliq_uf.aliquota_icms_interna if aliq_uf else None, ZERO,
    )

    # PIS/COFINS são FEDERAIS: o default vem do regime de apuração, nunca da UF.
    # As colunas `aliquota_pis_padrao`/`aliquota_cofins_padrao` de `aliquota_uf`
    # existem por engano histórico (as 27 UFs foram semeadas com o mesmo valor)
    # e deixaram de ser lidas aqui. Não remova a leitura achando que é fallback:
    # enquanto elas eram consultadas, corrigir a constante não surtia efeito
    # nenhum, porque o valor semeado vencia.
    nao_cumulativo = regime_apuracao == "NAO_CUMULATIVO"
    pis_padrao = PIS_NAO_CUMULATIVO if nao_cumulativo else PIS_CUMULATIVO
    cofins_padrao = COFINS_NAO_CUMULATIVO if nao_cumulativo else COFINS_CUMULATIVO

    # 2. Montar itens
    itens_entrada: list[ItemEntrada] = []

    for idx, item_venda in enumerate(venda.itens, start=1):
        produto = item_venda.produto
        # Cascata produto → regra por NCM → padrão da loja. Sem nada
        # configurado devolve o próprio `produto.fiscal`, e o cálculo é o
        # mesmo de sempre.
        fiscal = fiscal_efetivo(db, produto) if produto else None

        if not fiscal and produto:
            raise DadosFiscaisAusentesError(
                f"Produto '{produto.nome}' (ID {produto.id}) não possui dados "
                f"fiscais preenchidos. Preencha NCM, CFOP e CST/CSOSN antes de emitir.",
                campo="dados_fiscais",
                item=idx,
            )

        # Resolver alíquotas: produto override > UF default
        aliq_icms = _centesimos_para_decimal(
            fiscal.aliquota_icms if fiscal else None, icms_padrao,
        )

        # Interestadual: no regime normal o ICMS próprio sai pela alíquota
        # interestadual do perfil (7%/12%), não pela interna do emitente.
        inter = (
            _resolver_item_interestadual(db, fiscal, produto, operacao, uf_emitente, simples_nacional, idx)
            if operacao else None
        )
        if inter and inter.aliquota_icms is not None:
            aliq_icms = inter.aliquota_icms
        difal = inter.difal if inter else None
        st = inter.st if inter else None
        reducao = _centesimos_para_decimal(
            fiscal.reducao_base_icms if fiscal else None, ZERO,
        )
        if simples_nacional:
            # No Simples Nacional o PIS/COFINS já está embutido na guia única.
            # Destacar alíquota na nota gera bitributação aparente e diverge da
            # apuração. Saída sai como CST 49 (Outras Operações), zerada.
            #
            # Vale para CRT 1 e 4. O CRT 2 (excesso de sublimite) NÃO passa por
            # aqui: `simples_nacional` vem de usa_csosn(), que o exclui.
            cst_pis = CST_PIS_COFINS_SIMPLES
            cst_cofins = CST_PIS_COFINS_SIMPLES
            aliq_pis = ZERO
            aliq_cofins = ZERO
        else:
            aliq_pis = _centesimos_para_decimal(
                fiscal.aliquota_pis if fiscal else None, pis_padrao,
            )
            aliq_cofins = _centesimos_para_decimal(
                fiscal.aliquota_cofins if fiscal else None, cofins_padrao,
            )
            cst_pis = fiscal.cst_pis if fiscal and fiscal.cst_pis else "01"
            cst_cofins = fiscal.cst_cofins if fiscal and fiscal.cst_cofins else "01"

        itens_entrada.append(ItemEntrada(
            numero_item=idx,
            produto_id=item_venda.produto_id,
            descricao=produto.nome if produto else (item_venda.descricao_avulsa or "Item avulso"),
            quantidade=Decimal(str(item_venda.quantidade)),
            valor_unitario=_centavos_para_reais(item_venda.valor_unitario),
            valor_bruto=_centavos_para_reais(item_venda.subtotal),
            desconto_item=_centavos_para_reais(item_venda.desconto),
            ncm=fiscal.ncm if fiscal else None,
            cfop=inter.cfop if inter else (fiscal.cfop_padrao if fiscal else None),
            origem_mercadoria=fiscal.origem_mercadoria if fiscal and fiscal.origem_mercadoria is not None else 0,
            cst_icms=inter.cst_icms if inter else (fiscal.cst_icms if fiscal else None),
            csosn=inter.csosn if inter else (fiscal.csosn if fiscal else None),
            aliquota_icms=aliq_icms,
            reducao_base_icms=reducao,
            codigo_beneficio_fiscal=fiscal.codigo_beneficio_fiscal if fiscal else None,
            aliquota_pis=aliq_pis,
            aliquota_cofins=aliq_cofins,
            cst_pis=cst_pis,
            cst_cofins=cst_cofins,
            # DIFAL (None = operação interna)
            difal_aliquota_interestadual=difal.aliquota_interestadual if difal else None,
            difal_aliquota_interna_destino=difal.aliquota_interna_destino if difal else None,
            difal_percentual_fcp=difal.percentual_fcp if difal else ZERO,
            difal_base_dupla=difal.base_dupla if difal else False,
            # ICMS-ST (None = sem substituição)
            st_aliquota_interestadual=st.aliquota_interestadual if st else None,
            st_aliquota_interna_destino=st.aliquota_interna_destino if st else None,
            st_mva=st.mva if st else None,
            st_reducao_base=st.reducao_base if st else None,
        ))

    # 3. Montar dados da nota
    dados_nota = DadosNota(
        uf_emitente=uf_emitente.upper(),
        simples_nacional=simples_nacional,
        frete=_centavos_para_reais(venda.entrega),
        seguro=ZERO,              # Venda não tem campo seguro ainda
        # O acréscimo (juros de cartão do checkout) entra em Venda.total e no
        # valor dos pagamentos. Sem ele aqui, o total da nota fica menor que a
        # soma dos vPag e a SEFAZ rejeita (767). Mapeado para vOutro — despesa
        # acessória rateada entre os itens, compondo a base de ICMS.
        outras_despesas=_centavos_para_reais(venda.acrescimo or 0),
        desconto_nota=ZERO,       # Descontos são por item no modelo atual
        excluir_icms_base_pis_cofins=excluir_icms_base_pis_cofins,
    )

    return itens_entrada, dados_nota
