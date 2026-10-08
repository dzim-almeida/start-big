# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_builder.py
# DESCRIÇÃO: Montagem de payloads para emissão de NF-e.
#
# O payload segue o formato Focus NFe como referência (será ajustado
# quando os endpoints da API Online StartBig forem definidos).
#
# Valores monetários: o backend armazena em centavos (int).
# O payload converte para reais (str com 2 decimais).
#
# Desde a F5 (07/10/2026) este arquivo guarda só os quatro montar_payload_*;
# os blocos saíram, sem reescrever, para payload_emitente/destinatario/itens/
# totais/comum. O payload não mudou um byte (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

from typing import Optional
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from app.db.models.venda import Venda
from app.db.models.venda_nota_fiscal import VendaNotaFiscal
from .helpers import obter_crt, usa_csosn
from .tax_engine.types import ResultadoCalculo
from .payload_comum import _sanitizar_texto_sefaz, expurgar_nulos, _so_digitos
from .payload_emitente import _montar_emitente
from .payload_destinatario import _montar_destinatario, _montar_destinatario_nfce, _local_destino
from .payload_itens import _montar_itens, _montar_itens_devolucao
from .payload_totais import _montar_totais_pagamentos
from .payload_comum import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    _centavos_para_reais,
    SEM_GTIN,
    _sanitizar_ncm,
    _gtin_valido,
    _codigo_barras_para_sefaz,
)
from .payload_destinatario import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    _CAMPOS_ENDERECO_OBRIGATORIOS,
    _montar_endereco_destinatario,
    LOCAL_DESTINO_INTERNA,
    LOCAL_DESTINO_INTERESTADUAL,
    _montar_destinatario_avulso,
)
from .payload_itens import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    _campos_difal,
    _campos_icms_st,
)
from .payload_totais import (  # noqa: F401 — reexportado: testes e serviços importam daqui
    _totais_interestaduais,
    _CODIGOS_SEFAZ_CARTAO,
    _TP_INTEGRA,
    _montar_pagamentos,
    _validar_fechamento_pagamentos,
)


# indPres aceitos pela NFC-e (modelo 65). A regra de validacao da SEFAZ e
# literalmente `indPres <> 1 e 4` -> rejeicao 717 ("NFC-e em operacao nao
# presencial"). Internet (2), teleatendimento (3) e outros (9) NAO valem em
# NFC-e: essas operacoes pedem NF-e.
#
# O 4 (entrega a domicilio) so existe para NFC-e, e arrasta tres exigencias:
#   787 -> grupo `dest` obrigatorio
#   788 -> `enderDest` obrigatorio
#   786 -> grupo `transporta` obrigatorio
# Alem disso a UF precisa PERMITIR entrega a domicilio em NFC-e (rejeicao
# 785, parametrizavel por estado) -- confirmar no ambiente de homologacao.
INDPRES_BALCAO = 1


INDPRES_ENTREGA_DOMICILIO = 4


INDPRES_NFCE_ACEITOS = (INDPRES_BALCAO, INDPRES_ENTREGA_DOMICILIO)


def montar_payload_nfce(
    empresa: Empresa,
    endereco_empresa: Endereco,
    fiscal_settings: EmpresaFiscalSettings,
    venda: Venda,
    nota_fiscal: Optional[VendaNotaFiscal],
    resultado_calculo: Optional[ResultadoCalculo] = None,
    numero: Optional[int] = None,
    fiscais: Optional[dict] = None,
) -> dict:
    """Monta o payload da NFC-e (modelo 65) a partir de uma venda.

    Diferenças em relação à NF-e que NÃO são cosméticas:

    * `modelo` 65 — NFC-e.
    * `presenca_comprador` vem do que o caixa escolheu no fechamento; cai em 1
      (balcão) quando não informado. Estava CHUMBADO em 1, com a justificativa
      de que "a NFC-e só existe para operação presencial" — o que é falso: o
      indPres 4 (entrega a domicílio) existe justamente e apenas para NFC-e.
      Toda entrega saía com o indicador errado.
    * `consumidor_final` sempre 1: é venda a consumidor, por definição.
    * Destinatário OPCIONAL (ver `_montar_destinatario_nfce`).
    * O CSC NÃO viaja no payload: fica cadastrado na empresa dentro da Focus,
      que monta o QR Code sozinha. Ver o comentário no corpo da função.
    * Saída passa por `expurgar_nulos` — nó vazio é rejeição na hora.

    `numero` é o número já reservado por `crud.reservar_proximo_numero_nfce`.
    Quando omitido (preview), deriva de `ultimo_numero_nfce + 1`, que é uma
    PREVISÃO e não uma reserva: não use esse caminho para emitir.
    """
    crt = obter_crt(empresa)
    simples = usa_csosn(crt)

    natureza = "Venda de Mercadoria"
    if nota_fiscal and nota_fiscal.natureza_operacao:
        natureza = nota_fiscal.natureza_operacao

    if numero is None:
        numero = fiscal_settings.ultimo_numero_nfce + 1

    totais, formas_pagamento, valor_troco = _montar_totais_pagamentos(
        venda, resultado_calculo,
    )

    # Balcão é o default: cobre a esmagadora maioria das vendas e é o que o
    # PDV grava sozinho. `or` em vez de `is not None` é seguro aqui porque 0
    # não é indPres válido (o schema aceita só 1, 2, 3, 4 e 9).
    presenca_comprador = (
        getattr(nota_fiscal, "indicador_presenca", None) or INDPRES_BALCAO
    )
    if presenca_comprador not in INDPRES_NFCE_ACEITOS:
        raise ValueError(
            f"Indicador de presenca {presenca_comprador} nao vale para NFC-e: a "
            f"SEFAZ aceita apenas 1 (presencial) e 4 (entrega a domicilio), e "
            f"recusa o resto com a rejeicao 717. Operacao nao presencial exige "
            f"NF-e."
        )
    entrega_domicilio = presenca_comprador == INDPRES_ENTREGA_DOMICILIO

    documento_consumidor = getattr(nota_fiscal, "documento_consumidor", None)
    destinatario = _montar_destinatario_nfce(
        venda.cliente, documento_consumidor, entrega_domicilio=entrega_domicilio,
    )

    # Quem entrega e a propria loja (motoboy). Sem este grupo a NFC-e com
    # indPres 4 volta com a rejeicao 786.
    transportador = None
    if entrega_domicilio:
        transportador = {
            # Mesma normalização do emitente: documento vai sem pontuação.
            # Ficou de fora quando `_so_digitos` entrou (5e4f934) porque este
            # bloco só existe na NFC-e com entrega a domicílio -- e meio payload
            # normalizado é pior do que nenhum, porque esconde o caso que falta.
            "cnpj": _so_digitos(empresa.documento) if empresa.is_cnpj else None,
            "cpf": None if empresa.is_cnpj else _so_digitos(empresa.documento),
            "razao_social": _sanitizar_texto_sefaz(
                empresa.razao_social or empresa.nome_fantasia
            ),
            "inscricao_estadual": empresa.inscricao_estadual,
            "endereco": _sanitizar_texto_sefaz(endereco_empresa.logradouro),
            "municipio": _sanitizar_texto_sefaz(endereco_empresa.cidade),
            "uf": (
                endereco_empresa.estado.value
                if hasattr(endereco_empresa.estado, "value")
                else str(endereco_empresa.estado)
            ),
        }

    payload = {
        "modelo": 65,
        "natureza_operacao": natureza,
        "tipo_documento": 1,  # saída
        "local_destino": 1,   # operação interna (o motor bloqueia interestadual)
        # 9 = sem transporte (o cliente leva a mercadoria). Na entrega a
        # domicilio quem transporta e a propria loja: 3 = proprio por conta do
        # remetente, e o grupo `transporta` vira obrigatorio (rejeicao 786).
        "modalidade_frete": 3 if entrega_domicilio else 9,
        "finalidade_emissao": 1,
        "consumidor_final": 1,
        "presenca_comprador": presenca_comprador,
        "transportador": transportador,
        "numero": numero,
        "serie": fiscal_settings.serie_nfce,
        "emitente": _montar_emitente(empresa, endereco_empresa, fiscal_settings),
        "items": _montar_itens(venda, simples, resultado_calculo, fiscais),
        "formas_pagamento": formas_pagamento,
        "valor_troco": valor_troco,
        "totais": totais,
        # O CSC NÃO vai aqui, e isso é deliberado.
        #
        # Ele é cadastrado UMA VEZ na ficha da empresa dentro da Focus, junto do
        # certificado A1, e é ela quem monta o hash do QR Code e a URL de
        # consulta. Nunca foi campo de nota.
        #
        # Enquanto a plataforma validava o payload com schema estrito, mandá-lo
        # era inofensivo: o campo era descartado no caminho. Agora que o payload
        # é repassado inteiro, ele atravessaria até a Focus -- segredo em
        # trânsito sem ganho nenhum. Vazado, permite forjar QR Code em nome da
        # loja.
        #
        # Se o cupom sair sem QR Code, o CSC não está na Focus: veja
        # `cscConfigurado` em GET /erp/fiscal/config. E lembre que ele é POR
        # AMBIENTE -- o de homologação não vale em produção.
    }

    if destinatario is not None:
        payload["destinatario"] = destinatario

    return expurgar_nulos(payload) or {}


def montar_payload_nfe(
    empresa: Empresa,
    endereco_empresa: Endereco,
    fiscal_settings: EmpresaFiscalSettings,
    venda: Venda,
    nota_fiscal: Optional[VendaNotaFiscal],
    resultado_calculo: Optional[ResultadoCalculo] = None,
    numero: Optional[int] = None,
    fiscais: Optional[dict] = None,
) -> dict:
    """
    Monta payload completo para emissão de NF-e a partir de uma venda.

    Quando resultado_calculo é fornecido, enriquece itens e header com
    dados tributários calculados pelo FiscalTaxEngine.

    `numero` é o número já reservado por `crud.reservar_proximo_numero_nfe`.
    Quando omitido (preview, testes), deriva de `ultimo_numero_nfe + 1` — que
    é só uma previsão, NÃO uma reserva: não use esse caminho para emitir.

    Retorna dict no formato esperado pela API (referência Focus NFe).
    """
    crt = obter_crt(empresa)
    simples = usa_csosn(crt)

    natureza = "Venda de Mercadoria"
    finalidade = 1
    consumidor_final = True
    indicador_presenca = 1

    if nota_fiscal:
        natureza = nota_fiscal.natureza_operacao or natureza
        finalidade = nota_fiscal.finalidade_emissao or finalidade
        consumidor_final = nota_fiscal.consumidor_final if nota_fiscal.consumidor_final is not None else consumidor_final
        indicador_presenca = nota_fiscal.indicador_presenca or indicador_presenca

    if numero is None:
        numero = fiscal_settings.ultimo_numero_nfe + 1
    serie = fiscal_settings.serie_nfe

    # --- Destinatário ---
    if venda.cliente:
        destinatario = _montar_destinatario(venda.cliente)
    else:
        destinatario = {"nome": "CONSUMIDOR FINAL"}

    # --- Totais, pagamentos e troco ---
    # O troco é derivado (soma dos pagamentos − total da venda). A SEFAZ exige
    # a tag explícita quando há pagamento em dinheiro acima do total (Rej. 391).
    totais, formas_pagamento, valor_troco = _montar_totais_pagamentos(
        venda, resultado_calculo,
    )

    payload = {
        # --- Parâmetros da nota ---
        # modelo 55 = NF-e. Sem este campo a API intermediária teria que
        # adivinhar; NFC-e (65) ainda não é emitida por este caminho.
        "modelo": 55,
        "natureza_operacao": natureza,
        "tipo_documento": 1,  # 1 = saída
        # idDest sai da mesma decisão que o CFOP dos itens (ver _local_destino).
        "local_destino": _local_destino(resultado_calculo),
        # modFrete 9 = sem transporte. Obrigatório mesmo sem frete; quando há
        # valor de entrega ele é por conta do emitente (0).
        "modalidade_frete": 0 if venda.entrega else 9,
        "finalidade_emissao": finalidade,
        "consumidor_final": 1 if consumidor_final else 0,
        "presenca_comprador": indicador_presenca,
        "numero": numero,
        "serie": serie,
        # --- Emitente (objeto aninhado) ---
        "emitente": _montar_emitente(empresa, endereco_empresa, fiscal_settings),
        # --- Destinatário (objeto aninhado) ---
        "destinatario": destinatario,
        # --- Itens ---
        "items": _montar_itens(venda, simples, resultado_calculo, fiscais),
        # --- Pagamentos ---
        "formas_pagamento": formas_pagamento,
        "valor_troco": valor_troco,
        # --- Totais (objeto aninhado) ---
        "totais": totais,
    }

    return payload


def montar_payload_teste_nfe(
    empresa: Empresa,
    endereco_empresa: Endereco,
    fiscal_settings: EmpresaFiscalSettings,
) -> dict:
    """
    Monta payload fictício para emissão de teste em homologação.
    Usa dados mínimos válidos para a SEFAZ aceitar.
    """
    numero = fiscal_settings.ultimo_numero_nfe + 1
    serie = fiscal_settings.serie_nfe

    return {
        "natureza_operacao": "VENDA DE MERCADORIA",
        "tipo_documento": 1,
        "finalidade_emissao": 1,
        "consumidor_final": 1,
        "presenca_comprador": 1,
        # modFrete 9 = sem transporte. Obrigatorio na NF-e 4.0 mesmo quando nao
        # ha frete: a Focus recusou a nota de teste por "modalidade_frete nao
        # pode ser vazio" antes mesmo de chegar na SEFAZ.
        "modalidade_frete": 9,
        "numero": numero,
        "serie": serie,
        "emitente": _montar_emitente(empresa, endereco_empresa, fiscal_settings),
        "destinatario": {
            # CNPJ ficticio padrao de homologacao. Era "00000000000", que a
            # SEFAZ recusa: homologacao dispensa a EXISTENCIA do destinatario,
            # nunca o digito verificador -- e onze zeros nao fecha o modulo 11.
            #
            # Nao inventamos um CPF valido no lugar. Qualquer CPF que passe no
            # digito verificador PODE ser de uma pessoa real, e este numero fica
            # gravado no XML de teste de toda loja. A raiz 99999999 nunca e
            # atribuida pela Receita, entao este CNPJ e valido no calculo e
            # impossivel de colidir com contribuinte de verdade.
            "cnpj": "99999999000191",
            "indicador_ie": "9",  # indIEDest 9 = nao contribuinte
            "nome": "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
            # O enderDest e OBRIGATORIO na NF-e (modelo 55). Este destinatario
            # ficticio saia so com CPF e nome, e a nota de teste era recusada
            # com 422 nomeando os cinco campos de endereco.
            #
            # O endereco e o DO PROPRIO EMITENTE de proposito, e nao um endereco
            # inventado: a Focus resolve o par municipio/UF para codigo IBGE, e
            # um municipio que nao existe naquela UF derruba a nota por um
            # motivo que nada tem a ver com o teste. O endereco da loja ja foi
            # aceito no cadastro, entao o par e valido por construcao.
            "endereco": {
                "logradouro": endereco_empresa.logradouro,
                "numero": endereco_empresa.numero,
                "bairro": endereco_empresa.bairro,
                "cidade": endereco_empresa.cidade,
                "uf": (
                    endereco_empresa.estado.value
                    if hasattr(endereco_empresa.estado, "value")
                    else str(endereco_empresa.estado)
                ),
                "cep": _so_digitos(endereco_empresa.cep),
            },
        },
        "items": [
            {
                "numero_item": 1,
                "codigo_produto": "TESTE001",
                "descricao": "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
                "ncm": "00000000",
                "cfop": "5102",
                "unidade_comercial": "UN",
                "quantidade_comercial": 1.0,
                "valor_unitario_comercial": 1.0,
                "valor_bruto": 1.0,
                "icms_origem": "0",
                "icms_situacao_tributaria": "102",
                "codigo_barras_comercial": "SEM GTIN",
                "unidade_tributavel": "UN",
                "codigo_barras_tributavel": "SEM GTIN",
            }
        ],
        "formas_pagamento": [
            {
                "forma_pagamento": "01",
                "valor_pagamento": 1.0,
            }
        ],
        "totais": {
            "valor_produtos": 1.0,
            "valor_desconto": 0.0,
            "valor_frete": 0.0,
            "valor_seguro": 0.0,
            "valor_outras_despesas": 0.0,
            "icms_base_calculo": 0.0,
            "icms_valor_total": 0.0,
            "valor_total": 1.0,
        },
    }


# ===========================================================================
# NF-e DE DEVOLUÇÃO (finalidade 4, entrada) — TASK003
# ===========================================================================

NATUREZA_DEVOLUCAO = "DEVOLUCAO DE VENDA"


FORMA_PAGAMENTO_SEM_PAGAMENTO = "90"


def montar_payload_devolucao(
    empresa: Empresa,
    endereco_empresa: Endereco,
    fiscal_settings: EmpresaFiscalSettings,
    chave_referenciada: str,
    destinatario: dict,
    itens_devolucao: list,
    resultado_calculo: ResultadoCalculo,
    numero: int,
    motivo: str,
) -> dict:
    """NF-e de devolução: os 4 pilares da Focus/SEFAZ num payload só.

    1. `finalidade_emissao: 4`
    2. `notas_referenciadas` com a chave de 44 dígitos da nota devolvida
    3. `tipo_documento: 0` (entrada) com CFOP 1xxx/2xxx nos itens
    4. `formas_pagamento` = 90 (sem pagamento), valor zero
    """
    simples = usa_csosn(obter_crt(empresa))
    t = resultado_calculo.totais

    return {
        "modelo": 55,
        "natureza_operacao": NATUREZA_DEVOLUCAO,
        "tipo_documento": 0,
        "local_destino": 1,
        "modalidade_frete": 9,
        "finalidade_emissao": 4,
        "consumidor_final": 1,
        "presenca_comprador": 1,
        "numero": numero,
        "serie": fiscal_settings.serie_nfe,
        "emitente": _montar_emitente(empresa, endereco_empresa, fiscal_settings),
        "destinatario": destinatario,
        "notas_referenciadas": [{"chave_nfe": chave_referenciada}],
        "items": _montar_itens_devolucao(itens_devolucao, resultado_calculo, simples),
        "formas_pagamento": [
            {"forma_pagamento": FORMA_PAGAMENTO_SEM_PAGAMENTO, "valor_pagamento": 0.0},
        ],
        "valor_troco": 0.0,
        "informacoes_adicionais_contribuinte": _sanitizar_texto_sefaz(
            f"Devolucao referente a NF chave {chave_referenciada}. Motivo: {motivo}", 2000,
        ),
        "totais": {
            "valor_produtos": float(t.valor_total_produtos),
            "valor_frete": 0.0,
            "valor_seguro": 0.0,
            "valor_outras_despesas": 0.0,
            "valor_desconto": float(t.valor_desconto),
            "icms_base_calculo": float(t.base_calculo_icms),
            "icms_valor_total": float(t.valor_icms),
            "valor_total": float(t.valor_total_nota),
        },
        "valor_total": float(t.valor_total_nota),
    }
