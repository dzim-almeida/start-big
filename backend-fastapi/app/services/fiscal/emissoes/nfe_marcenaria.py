# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/emissoes/nfe_marcenaria.py
# DESCRIÇÃO: As NF-e dos móveis da marcenaria, como produto acabado
#            (docs/marcenaria-faturamento-plano.md, F3 e F4).
# ---------------------------------------------------------------------------
"""
Três papéis de nota (`documento_fiscal.papel`), conforme o modo da loja (D7):

  NOTA_NA_ENTREGA  -> VENDA (5101/5102) a cada entrega, com os móveis dela;
  ENTREGA_FUTURA   -> SIMPLES_FATURAMENTO (5922) no fechamento, com todos os
                      móveis ainda sem ela (o aditivo, aprovado depois, ganha a
                      sua), sem destaque de ICMS e sem mexer no estoque; e
                      REMESSA (5116/5117) a cada entrega, com o ICMS, sem
                      pagamento ("90") e apontando para a 5922 pela chave.

Diferenças em relação à NF-e da OS comum (`nfe_os.py`), cada uma por um motivo:

- A OS NÃO precisa estar finalizada: a obra é entregue por ambiente, em dias
  diferentes, e cada saída de mercadoria precisa da sua nota.
- A trava é POR MÓVEL (D1): cada móvel sai em uma venda/remessa só, e só entra
  móvel NO_ESTOQUE (pronto, F2). Na 5922, cada móvel em um simples faturamento.
- O estoque do produto acabado SAI quando a venda/remessa é criada (origem
  PRODUCAO, fora do CMV) e VOLTA se ela cair (`estoque_acabado.ao_mudar_documento`).
  Marcar antes de transmitir é o que impede o mesmo móvel de ir para duas notas
  se a resposta da SEFAZ se perder.

Todo o miolo (alíquotas, rateio, montagem, fechamento dos pagamentos) é o
MESMO da venda: a entrega é apresentada como venda em `adaptador_marcenaria.py`.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.documento_fiscal import DocumentoFiscal
from app.services.fiscal.emissoes.adaptador_marcenaria import REMESSA, SIMPLES_FATURAMENTO, VENDA
from app.services.fiscal.emissoes.nucleo import _aplicar_resultado, _avisos, _fiscais_efetivos, _obter_fiscal_settings
from app.services.fiscal.emissoes.snapshot import gravar_snapshot
from app.services.fiscal.helpers import criar_pendencia, obter_crt, regime_apuracao, usa_csosn
from app.services.fiscal.http import get_fiscal_client
from app.services.fiscal.payload.builder import montar_payload_nfe
from app.services.fiscal.tax_engine import calcular_impostos
from app.services.fiscal.tax_engine.resolver import resolver_aliquotas_venda

logger = logging.getLogger(__name__)

MSG_DESLIGADO = "O faturamento dos móveis está desligado (Configurações › Marcenaria)."
MSG_SEM_MOVEIS = "Escolha ao menos um móvel para a nota."
MSG_MODO_ERRADO = {
    VENDA: "No modo de entrega futura, a nota de cada entrega é a de remessa.",
    SIMPLES_FATURAMENTO: "O simples faturamento só existe no modo de venda para entrega futura.",
}
# Simples faturamento que ainda vale (o móvel continua coberto por ele).
STATUS_VIVOS = ("AUTORIZADA", "PROCESSANDO", "INDETERMINADA")
REF_POR_PAPEL = {VENDA: "ent", REMESSA: "rem", SIMPLES_FATURAMENTO: "sf"}


def _erro(codigo: int, detalhe) -> None:
    raise HTTPException(status_code=codigo, detail=detalhe)


def papel_da_entrega(config) -> str:
    """A nota de uma entrega: venda (nota na entrega) ou remessa (entrega futura)."""
    return REMESSA if config.faturamento_modo == "ENTREGA_FUTURA" else VENDA


def _preparar(db: Session, numero_os: str, empresa_id: int, movel_ids: Optional[list[int]], papel: Optional[str]):
    """Tudo que pode recusar, ANTES de reservar número (como `nfe_os`).

    `papel` None = a nota de uma entrega no modo da loja; SIMPLES_FATURAMENTO =
    a 5922 da OS (os `movel_ids` são ignorados: entram todos os ainda sem ela).

    Returns:
        (empresa, endereco, os_obj, papel, moveis_escolhidos, linhas, simples, adaptado, resultado_calculo)
    """
    from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoStatus
    from app.db.models.marcenaria.faturamento import SituacaoFaturamento
    from app.db.models.produto import Produto
    from app.services.fiscal.completude import validators
    from app.services.fiscal.emissoes.adaptador_marcenaria import MovelParaNota, adaptar_entrega
    from app.services.marcenaria.aprovacao import NOME_INSTALACAO, ORIGEM
    from app.services.marcenaria.faturamento import configuracao_ligada
    from app.services.marcenaria.faturamento.estoque_acabado import linhas_da_os, produto_do_movel
    from app.services.marcenaria.orcamento_comum import orcamentos_da_os

    config = configuracao_ligada(db, empresa_id)
    if config is None:
        _erro(status.HTTP_409_CONFLICT, MSG_DESLIGADO)
    da_entrega = papel_da_entrega(config)
    if papel is None:
        papel = da_entrega
    elif papel == SIMPLES_FATURAMENTO and da_entrega != REMESSA:
        _erro(status.HTTP_409_CONFLICT, MSG_MODO_ERRADO[SIMPLES_FATURAMENTO])

    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj or not os_obj.ativo:
        _erro(status.HTTP_404_NOT_FOUND, "Ordem de Serviço não encontrada.")
    if getattr(os_obj.status, "value", os_obj.status) == OrdemServicoStatus.CANCELADA.value:
        _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "OS cancelada não gera nota.")
    vista = orcamentos_da_os(db, os_obj)
    if vista is None:
        _erro(status.HTTP_404_NOT_FOUND, "Esta OS não veio de um orçamento de marcenaria.")

    itens_os = {i.id: i for i in os_obj.itens}

    def item_do_movel(movel):
        item = itens_os.get(movel.os_item_id)
        if item is None or item.status_aprovacao == OrdemServicoItemAprovacao.REPROVADO:
            return None
        return item

    aprovados = {m.id: m for a in vista.ambientes for m in a.moveis if m.aprovado and item_do_movel(m) is not None}
    linhas = linhas_da_os(db, os_obj.id)
    docs_sf = {d.id: d for d in db.query(DocumentoFiscal).filter(
        DocumentoFiscal.origem_tipo == "OS", DocumentoFiscal.origem_id == os_obj.id,
        DocumentoFiscal.papel == SIMPLES_FATURAMENTO).all()}

    def sf_do_movel(movel) -> Optional[DocumentoFiscal]:
        doc = docs_sf.get(movel.simples_faturamento_id) if movel.simples_faturamento_id else None
        return doc if doc is not None and doc.status in STATUS_VIVOS else None

    if papel == SIMPLES_FATURAMENTO:
        escolhidos = [mid for mid, m in aprovados.items() if sf_do_movel(m) is None]
        if not escolhidos:
            _erro(status.HTTP_409_CONFLICT, "Todos os móveis desta OS já estão num simples faturamento.")
    else:
        if not movel_ids:
            _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, MSG_SEM_MOVEIS)
        escolhidos = list(dict.fromkeys(movel_ids))
        if any(mid not in aprovados for mid in escolhidos):
            _erro(status.HTTP_404_NOT_FOUND, "Há móvel escolhido que não é desta OS.")
        sem_estoque = [aprovados[mid].nome for mid in escolhidos
                       if linhas.get(mid) is None or linhas[mid].situacao != SituacaoFaturamento.NO_ESTOQUE]
        if sem_estoque:
            _erro(status.HTTP_409_CONFLICT, (
                f"Estes móveis não estão no estoque para faturar: {', '.join(sem_estoque)}. "
                f"Só entra na nota o móvel pronto que ainda não saiu em outra nota."
            ))
        if papel == REMESSA:
            sem_sf = [aprovados[mid].nome for mid in escolhidos
                      if sf_do_movel(aprovados[mid]) is None or sf_do_movel(aprovados[mid]).status != "AUTORIZADA"]
            if sem_sf:
                _erro(status.HTTP_409_CONFLICT, (
                    f"Emita (e aguarde a autorização d)o simples faturamento antes da remessa: {', '.join(sem_sf)}."
                ))

    empresa = crud.get_empresa(db, empresa_id)
    simples = usa_csosn(obter_crt(empresa))

    # Gate: emitente, destinatário e o cadastro fiscal de cada produto acabado.
    pendencias = list(validators.verificar_emitente(db, empresa_id))
    cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
    if not cliente:
        pendencias.append(criar_pendencia("destinatario", "cliente", "OS sem cliente no objeto."))
    else:
        pendencias.extend(validators.verificar_documento_cliente(cliente))
        pendencias.extend(validators.verificar_endereco_destinatario(cliente))
    moveis: list[MovelParaNota] = []
    conferidos: set[int] = set()
    for mid in escolhidos:
        movel = aprovados[mid]
        produto_id = linhas[mid].produto_id if mid in linhas and papel != SIMPLES_FATURAMENTO else produto_do_movel(config, movel)
        produto = db.get(Produto, produto_id) if produto_id else None
        if produto is None:
            pendencias.append(criar_pendencia("item", "produto_acabado",
                                              "Escolha o produto do móvel fabricado em Configurações › Marcenaria.",
                                              movel.id, movel.nome))
            continue
        if produto.id not in conferidos:
            validators.verificar_produto_fiscal(db, produto, pendencias, simples)
            conferidos.add(produto.id)
        quantidade = linhas[mid].quantidade if mid in linhas and papel != SIMPLES_FATURAMENTO else float(movel.quantidade)
        moveis.append(MovelParaNota(item_os=item_do_movel(movel), produto=produto, quantidade=quantidade,
                                    terceirizado=movel.tipo_producao == "TERCEIRIZADA"))
    if pendencias:
        _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, {
            "mensagem": "Dados fiscais incompletos para emissão.",
            "pendencias": [p.model_dump() for p in pendencias],
        })

    valor_de = lambda movel: item_do_movel(movel).valor_total or 0              # noqa: E731
    valor_total_moveis = sum(valor_de(m) for m in aprovados.values())
    if papel == SIMPLES_FATURAMENTO:
        ja_cobertos = [m for mid, m in aprovados.items() if mid not in escolhidos]
    else:
        ja_cobertos = [aprovados[mid] for mid, linha in linhas.items()
                       if mid in aprovados and mid not in escolhidos and linha.situacao == SituacaoFaturamento.FATURADO]
    instalacao = sum(i.valor_total or 0 for i in os_obj.itens
                     if i.origem == ORIGEM and i.nome == NOME_INSTALACAO
                     and i.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO)
    chaves = (sorted({sf_do_movel(aprovados[mid]).chave_acesso for mid in escolhidos})
              if papel == REMESSA else None)

    adaptado = adaptar_entrega(
        os_obj, moveis,
        valor_moveis_total=valor_total_moveis,
        valor_moveis_ja_faturados=sum(valor_de(m) for m in ja_cobertos),
        instalacao_valor=instalacao,
        instalacao_modo=config.instalacao_modo,
        papel=papel,
        chaves_referenciadas=chaves,
    )

    endereco = crud.get_endereco_empresa(db, empresa_id)
    uf_emitente = endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado)
    try:
        itens_entrada, dados_nota = resolver_aliquotas_venda(
            db, adaptado, uf_emitente, simples, regime_apuracao=regime_apuracao(empresa),
        )
        resultado_calculo = calcular_impostos(itens_entrada, dados_nota)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[FISCAL] Erro no cálculo tributário da nota da OS %s: %s", numero_os, e)
        _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Erro no cálculo tributário: {str(e)}")

    escolhidos_moveis = [aprovados[mid] for mid in escolhidos]
    linhas_escolhidas = [linhas[mid] for mid in escolhidos if mid in linhas] if papel != SIMPLES_FATURAMENTO else []
    sfs = {mid: sf_do_movel(aprovados[mid]) for mid in escolhidos} if papel == REMESSA else {}
    return (empresa, endereco, os_obj, papel, escolhidos_moveis, linhas_escolhidas, sfs,
            adaptado, resultado_calculo)


def preview_nfe_marcenaria(db: Session, numero_os: str, empresa_id: int, movel_ids: Optional[list[int]],
                           papel: Optional[str] = None) -> dict:
    """Pré-visualização da nota. Não emite e NÃO reserva número."""
    empresa, endereco, os_obj, papel, _moveis, _linhas, _sfs, adaptado, resultado = _preparar(
        db, numero_os, empresa_id, movel_ids, papel)
    payload = montar_payload_nfe(
        empresa, endereco, _obter_fiscal_settings(db, empresa_id), adaptado, adaptado.nota_fiscal,
        resultado_calculo=resultado, fiscais=_fiscais_efetivos(db, adaptado),
    )
    return {
        "numero_os": numero_os,
        "papel": papel,
        "natureza_operacao": payload.get("natureza_operacao"),
        "itens": payload.get("items", []),
        "totais": payload.get("totais", {}),
        "formas_pagamento": payload.get("formas_pagamento", []),
        "destinatario": payload.get("destinatario", {}),
        "notas_referenciadas": payload.get("notas_referenciadas", []),
        "avisos": _avisos(empresa, getattr(adaptado, "cliente", None)),
    }


def emitir_nfe_marcenaria(
    db: Session, numero_os: str, empresa_id: int, movel_ids: Optional[list[int]],
    usuario: Optional[dict] = None, papel: Optional[str] = None,
) -> DocumentoFiscal:
    """Emite a nota. Mesma ordem do `emitir_nfe_os`: recusar antes de reservar."""
    from app.services.marcenaria.faturamento import estoque_acabado

    empresa, endereco, os_obj, papel, moveis, linhas, sfs, adaptado, resultado = _preparar(
        db, numero_os, empresa_id, movel_ids, papel)
    fiscal_settings = _obter_fiscal_settings(db, empresa_id)

    numero = crud.reservar_proximo_numero_nfe(db, empresa_id)
    payload = montar_payload_nfe(
        empresa, endereco, fiscal_settings, adaptado, adaptado.nota_fiscal,
        resultado_calculo=resultado, numero=numero, fiscais=_fiscais_efetivos(db, adaptado),
    )

    tentativas = crud.contar_documentos_por_os(db, numero_os)
    ref = re.sub(r"[^A-Za-z0-9._-]", "-", f"os-{numero_os}-{REF_POR_PAPEL[papel]}{tentativas + 1}")[:50]
    doc = DocumentoFiscal(
        tipo_documento="NFE",
        origem_tipo="OS",
        origem_id=os_obj.id,
        origem_numero_os=numero_os,
        papel=papel,
        status="PROCESSANDO",
        numero_documento=numero,
        serie=fiscal_settings.serie_nfe,
        ref_api=ref,
        idempotency_key=str(uuid.uuid4()),
        ambiente_emissao=fiscal_settings.ambiente_emissao,
        valor_total=adaptado.total,          # o valor DESTA nota, não o da OS
        data_emissao=datetime.now(timezone.utc),
    )
    gravar_snapshot(doc, payload, venda=adaptado)
    crud.salvar_documento(db, doc)

    # Antes de transmitir: os móveis ficam presos a esta nota.
    if papel == SIMPLES_FATURAMENTO:
        for movel in moveis:
            movel.simples_faturamento_id = doc.id
        db.flush()
    else:
        estoque_acabado.faturar(db, os_obj, linhas, doc, usuario)
        for linha in linhas:
            sf = sfs.get(linha.movel_id)
            linha.documento_simples_faturamento_id = sf.id if sf is not None else None

    client = get_fiscal_client(fiscal_settings.ambiente_emissao, crud.get_licenca_token(db))
    try:
        resultado_api = client.emitir_nfe(ref, payload, idempotency_key=doc.idempotency_key)
        _aplicar_resultado(doc, resultado_api, client)
    except NotImplementedError as e:
        doc.status = "REJEITADA"
        doc.mensagem_sefaz = str(e)
    except Exception as e:
        # Falha de comunicação NÃO é rejeição (ver `emitir_nfe_os`): os móveis
        # continuam presos a esta nota até a consulta dizer o que houve.
        logger.error("[FISCAL] Falha de comunicação ao emitir NF-e da OS ref=%s: %s", ref, e)
        doc.status = "INDETERMINADA"
        doc.mensagem_sefaz = (
            f"Não foi possível confirmar o resultado junto à SEFAZ: {str(e)[:300]}. "
            f"O documento será reconsultado automaticamente."
        )

    estoque_acabado.ao_mudar_documento(db, doc, usuario)
    return doc
