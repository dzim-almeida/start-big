# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_itens.py
# DESCRIÇÃO: Itens do payload: tributos por item, DIFAL, ICMS-ST e itens de devolução.
#
# Saiu do payload_builder.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. O payload da nota não muda nem um byte
# (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

from decimal import Decimal
from typing import Optional
from app.db.models.venda import Venda
from .embalagem_nota import campos_da_embalagem, conferir_valores_do_item
from .tax_engine.types import ResultadoCalculo
from .payload_comum import _centavos_para_reais, SEM_GTIN, _sanitizar_ncm, _gtin_valido, _codigo_barras_para_sefaz


def _montar_itens(
    venda: Venda,
    simples_nacional: bool,
    resultado_calculo: Optional[ResultadoCalculo] = None,
    fiscais: Optional[dict] = None,
) -> list[dict]:
    """
    `fiscais` traz a tributação EFETIVA por produto_id (cascata produto → NCM →
    padrão da loja), resolvida em `emissao.py`, que é quem tem a sessão.

    Ausente, cai em `produto.fiscal` — o comportamento de antes da cascata, e o
    caminho de todo teste que monta payload sem banco.
    """
    itens = []

    # Indexar impostos por numero_item para lookup rápido
    impostos_por_item: dict = {}
    if resultado_calculo:
        for imp in resultado_calculo.itens:
            impostos_por_item[imp.numero_item] = imp

    for idx, item in enumerate(venda.itens, start=1):
        produto = item.produto
        if not produto:
            raise ValueError(
                f"Item #{idx} é avulso (sem produto). "
                f"Todos os itens devem ter produto vinculado para gerar payload NF-e."
            )

        fiscal = (fiscais or {}).get(produto.id) if fiscais else None
        if fiscal is None:
            fiscal = produto.fiscal

        item_dict = {
            "numero_item": idx,
            "codigo_produto": produto.codigo_produto or str(produto.id),
            "descricao": produto.nome,
            "quantidade_comercial": float(item.quantidade),
            "valor_unitario_comercial": _centavos_para_reais(item.valor_unitario),
            "valor_bruto": _centavos_para_reais(item.subtotal),
            "unidade_comercial": produto.unidade_medida or "UN",
            "codigo_barras_comercial": _codigo_barras_para_sefaz(produto.codigo_barras),
        }

        if fiscal:
            item_dict["ncm"] = _sanitizar_ncm(fiscal.ncm)
            item_dict["cfop"] = fiscal.cfop_padrao
            item_dict["icms_origem"] = str(fiscal.origem_mercadoria or 0)
            item_dict["unidade_tributavel"] = fiscal.unidade_tributavel or produto.unidade_medida or "UN"
            item_dict["codigo_barras_tributavel"] = _codigo_barras_para_sefaz(
                fiscal.gtin_tributavel or produto.codigo_barras
            )
            if fiscal.cest:
                item_dict["cest"] = fiscal.cest

            if simples_nacional:
                item_dict["icms_situacao_tributaria"] = fiscal.csosn
            else:
                item_dict["icms_situacao_tributaria"] = fiscal.cst_icms

        # Linha de fardo/caixa: unidade comercial = embalagem, tributável =
        # unidade do produto (plano de embalagens, D8/D9). Linha de unidade
        # (fator 1, todas as antigas) passa reto: payload idêntico ao de antes.
        fator = getattr(item, "fator_embalagem", 1) or 1
        if fator > 1:
            embalagem = getattr(item, "embalagem", None)
            item_dict.update(campos_da_embalagem(
                quantidade=Decimal(item.quantidade),
                fator=fator,
                sigla=item.sigla_embalagem or (embalagem.sigla if embalagem else "UN"),
                valor_bruto=Decimal(item.subtotal) / 100,
                unidade_base=(fiscal.unidade_tributavel if fiscal else None) or produto.unidade_medida or "UN",
                gtin_embalagem=embalagem.codigo_barras if embalagem else None,
                gtin_unidade=(fiscal.gtin_tributavel if fiscal else None) or produto.codigo_barras,
                gtin_valido=_gtin_valido,
                sem_gtin=SEM_GTIN,
            ))
            problemas = conferir_valores_do_item(item_dict)
            if problemas:
                raise ValueError(" ".join(problemas))

        # Enriquecer com dados tributários calculados pelo tax_engine
        imp = impostos_por_item.get(idx)
        if imp:
            item_dict.update({
                # Rateio
                "valor_frete": float(imp.valor_frete),
                "valor_seguro": float(imp.valor_seguro),
                "valor_outras_despesas_acessorias": float(imp.valor_outras_despesas),
                "valor_desconto": float(imp.valor_desconto),
                # ICMS
                "icms_origem": imp.icms_origem,
                "icms_situacao_tributaria": imp.icms_situacao_tributaria,
                "icms_modalidade_base_calculo": imp.icms_modalidade_base_calculo,
                "icms_base_calculo": float(imp.icms_base_calculo),
                "icms_aliquota": float(imp.icms_aliquota),
                "icms_valor": float(imp.icms_valor),
                # PIS
                "pis_situacao_tributaria": imp.pis_situacao_tributaria,
                "pis_base_calculo": float(imp.pis_base_calculo),
                "pis_aliquota_porcentual": float(imp.pis_aliquota),
                "pis_valor": float(imp.pis_valor),
                # COFINS
                "cofins_situacao_tributaria": imp.cofins_situacao_tributaria,
                "cofins_base_calculo": float(imp.cofins_base_calculo),
                "cofins_aliquota_porcentual": float(imp.cofins_aliquota),
                "cofins_valor": float(imp.cofins_valor),
                # IPI: NÃO ENVIADO. Ver o bloco abaixo.
            })
            # ---------------------------------------------------------------
            # POR QUE O GRUPO DE IPI SAIU DO PAYLOAD (12/09/2026)
            # ---------------------------------------------------------------
            # A primeira emissão numa loja real voltou com rejeição de SCHEMA:
            #
            #   Element '...}IPINT': This element is not expected.
            #   Expected is one of ( CNPJProd, cSelo, qSelo, cEnq )
            #
            # No XSD da NF-e, o grupo IPI exige `cEnq` ANTES do `IPINT`. O ERP
            # mandava os dois campos (`ipi_situacao_tributaria` = 53 e
            # `ipi_codigo_enquadramento` = 999, ver tax_engine/engine.py), mas
            # o cEnq não chegou ao XML — perde-se entre daqui e a SEFAZ.
            #
            # A correção aqui é não mandar o grupo, e ela é a CERTA por mérito
            # próprio: o grupo IPI é OPCIONAL no layout, e este sistema não
            # calcula IPI nenhum (comércio e serviços — ver o comentário do
            # engine). Declarar "não tributado" era informar um grupo que não
            # temos como garantir bem formado, para dizer que não há imposto.
            #
            # Quando houver cliente indústria, o IPI volta calculado de
            # verdade, com cEnq na ordem que o schema pede.
            # ---------------------------------------------------------------

            # CFOP da OPERAÇÃO (5xxx interna, 6xxx interestadual), decidido
            # pelo resolver junto com o idDest. O cfop_padrao do produto é só
            # o fallback de quem não passou pelo motor.
            if imp.cfop:
                item_dict["cfop"] = imp.cfop
            item_dict.update(_campos_difal(imp))
            item_dict.update(_campos_icms_st(imp))

            # CST 20 — Redução de base + código benefício fiscal
            if imp.icms_reducao_base is not None:
                item_dict["icms_reducao_base_calculo"] = float(imp.icms_reducao_base)
            if imp.icms_codigo_beneficio_fiscal:
                item_dict["icms_codigo_beneficio_fiscal_reducao_base_calculo"] = imp.icms_codigo_beneficio_fiscal
            # CSOSN 101 — Crédito do Simples Nacional
            if imp.icms_aliquota_credito_simples is not None:
                item_dict["icms_aliquota_aplicavel_calculo_credito"] = float(imp.icms_aliquota_credito_simples)
                item_dict["icms_valor_credito_aproveitado"] = float(imp.icms_valor_credito_simples)
        else:
            # Fallback: sem tax_engine, mantém desconto do item. Inclui o da
            # regra de preço (R1/R3 vão no vDesc, §6.1); item de OS não tem.
            desconto_item = (item.desconto or 0) + (getattr(item, "desconto_regra", 0) or 0)
            if desconto_item > 0:
                item_dict["valor_desconto"] = _centavos_para_reais(desconto_item)

        itens.append(item_dict)

    # Validar alinhamento: se tax_engine rodou, cada item deve ter imposto calculado
    if resultado_calculo and len(impostos_por_item) != len(itens):
        raise ValueError(
            f"Desalinhamento: tax_engine calculou {len(impostos_por_item)} itens, "
            f"mas payload tem {len(itens)} itens."
        )

    return itens


def _campos_difal(imp) -> dict:
    """
    Grupo ICMSUFDest (partilha EC 87/2015) na nomenclatura da Focus NFe.

    Só quando o motor calculou DIFAL (venda interestadual a não contribuinte,
    regime normal). Operação interna não ganha chave nenhuma — o contrato com
    a plataforma é exato (test_contrato_payload_campos).

    Nomes conferidos na referência oficial (campos.focusnfe.com.br/nfe/
    NotaFiscalXML.html) em 19/09/2026 — a spec trazia outros, e chave que a
    Focus não conhece é descartada em silêncio (Rejeição 694 na SEFAZ).
    `icms_percentual_partilha` (pICMSInterPart) fica de fora: a Focus assume
    100, que é o valor desde 2019.
    """
    if imp.difal_valor is None:
        return {}
    campos = {
        "icms_base_calculo_uf_destino": float(imp.difal_base_calculo),                 # vBCUFDest
        "icms_aliquota_interna_uf_destino": float(imp.difal_aliquota_interna_destino), # pICMSUFDest
        "icms_aliquota_interestadual": float(imp.difal_aliquota_interestadual),        # pICMSInter
        "icms_valor_uf_destino": float(imp.difal_valor),                               # vICMSUFDest
        "icms_valor_uf_remetente": float(imp.difal_valor_remetente or 0),              # vICMSUFRemet
    }
    if imp.fcp_aliquota and imp.fcp_aliquota > 0:
        campos.update({
            "fcp_base_calculo_uf_destino": float(imp.fcp_base_calculo or imp.difal_base_calculo),  # vBCFCPUFDest
            "fcp_percentual_uf_destino": float(imp.fcp_aliquota),                                # pFCPUFDest
            "fcp_valor_uf_destino": float(imp.fcp_valor or 0),                                   # vFCPUFDest
        })
    return campos


def _campos_icms_st(imp) -> dict:
    """
    Grupo de ST do remetente substituto (ICMS10/70, ICMSSN201/202), na
    nomenclatura da Focus NFe. Só quando o motor calculou ST.
    """
    if imp.icms_st_valor is None:
        return {}
    campos = {
        "icms_modalidade_base_calculo_st": imp.icms_st_modalidade_base_calculo,  # modBCST
        "icms_base_calculo_st": float(imp.icms_st_base_calculo),                 # vBCST
        "icms_aliquota_st": float(imp.icms_st_aliquota or 0),                    # pICMSST
        "icms_valor_st": float(imp.icms_st_valor),                               # vICMSST
        "icms_margem_valor_adicionado_st": float(imp.icms_st_mva or 0),          # pMVAST
    }
    if imp.icms_st_reducao_base and imp.icms_st_reducao_base > 0:
        campos["icms_reducao_base_calculo_st"] = float(imp.icms_st_reducao_base)  # pRedBCST
    return campos


def _montar_itens_devolucao(
    itens_devolucao: list,
    resultado_calculo: ResultadoCalculo,
    simples_nacional: bool,
) -> list[dict]:
    """Itens da devolução a partir do SNAPSHOT da nota original.

    `itens_devolucao` é uma lista de `(item_snapshot, quantidade_milesimos,
    cfop_entrada)`. Os valores espelham o que a SEFAZ viu na nota original,
    proporcionais à quantidade devolvida; os tributos vêm do tax_engine,
    alimentado com o CST/CSOSN e a alíquota congelados no snapshot.
    """
    impostos_por_item = {imp.numero_item: imp for imp in resultado_calculo.itens}
    itens = []
    for idx, (snap, qtd_mil, cfop_entrada) in enumerate(itens_devolucao, start=1):
        imp = impostos_por_item[idx]
        item = {
            "numero_item": idx,
            "codigo_produto": snap.codigo_produto or str(snap.produto_id or idx),
            "descricao": snap.descricao,
            "quantidade_comercial": qtd_mil / 1000,
            "valor_unitario_comercial": _centavos_para_reais(snap.valor_unitario),
            # quantidade (milésimos) × unitário (centavos) / 1000 / 100 = reais
            "valor_bruto": round(qtd_mil * snap.valor_unitario / 100_000, 2),
            "unidade_comercial": snap.unidade or "UN",
            "unidade_tributavel": snap.unidade or "UN",
            "codigo_barras_comercial": _codigo_barras_para_sefaz(snap.codigo_barras),
            "codigo_barras_tributavel": _codigo_barras_para_sefaz(snap.codigo_barras),
            "ncm": _sanitizar_ncm(snap.ncm),
            "cfop": cfop_entrada,
            "icms_origem": imp.icms_origem,
            "icms_situacao_tributaria": imp.icms_situacao_tributaria,
            "icms_modalidade_base_calculo": imp.icms_modalidade_base_calculo,
            "icms_base_calculo": float(imp.icms_base_calculo),
            "icms_aliquota": float(imp.icms_aliquota),
            "icms_valor": float(imp.icms_valor),
            "pis_situacao_tributaria": imp.pis_situacao_tributaria,
            "pis_base_calculo": float(imp.pis_base_calculo),
            "pis_aliquota_porcentual": float(imp.pis_aliquota),
            "pis_valor": float(imp.pis_valor),
            "cofins_situacao_tributaria": imp.cofins_situacao_tributaria,
            "cofins_base_calculo": float(imp.cofins_base_calculo),
            "cofins_aliquota_porcentual": float(imp.cofins_aliquota),
            "cofins_valor": float(imp.cofins_valor),
        }
        if snap.cest:
            item["cest"] = snap.cest
        # Fardo devolvido: mesma unidade tributável da nota original (D8).
        fator = getattr(snap, "fator_embalagem", 1) or 1
        if fator > 1:
            q_trib = Decimal(qtd_mil) * fator / 1000
            v_prod = Decimal(str(item["valor_bruto"]))
            item["unidade_tributavel"] = snap.unidade_tributavel or "UN"
            item["codigo_barras_tributavel"] = (
                snap.codigo_barras_tributavel if item["codigo_barras_comercial"] != SEM_GTIN else SEM_GTIN
            ) or SEM_GTIN
            item["quantidade_tributavel"] = float(q_trib)
            item["valor_unitario_tributavel"] = float(
                (v_prod / q_trib).quantize(Decimal("0.0000000001"))
            )
        itens.append(item)
    return itens
