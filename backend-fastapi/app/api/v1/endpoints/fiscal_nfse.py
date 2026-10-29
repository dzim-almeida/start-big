# ---------------------------------------------------------------------------
# ARQUIVO: api/v1/endpoints/fiscal_nfse.py
# DESCRIÇÃO: NFS-e (docs/nfse-plano.md): a busca do código de tributação
#            nacional e do NBS para o cadastro do serviço (F1) e a NFS-e da OS
#            (F3).
#
# O router inteiro exige o módulo NFSE na licença (R1 do plano). Sem ele, a
# tela do serviço nem mostra os campos novos; quem chamar a rota direto recebe
# 403 MODULO_NAO_CONTRATADO.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.depends import _handle_db_transaction, check_permission, get_current_active_user, get_db
from app.core.modulos import requer_modulo
from app.schemas.fiscal.emissao import CancelamentoRequest, EmissaoResponse
from app.schemas.fiscal.nfse import NfseAvulsaRequest, NfseConfiguracao
from app.schemas.fiscal.verificacao import ResultadoVerificacaoFiscal
from app.services.fiscal.nfse import tabelas

router = APIRouter(dependencies=[Depends(requer_modulo("NFSE"))])


@router.get(
    "/servicos-nacionais",
    summary="Buscar Código de Tributação Nacional",
    description=(
        "Procura na lista de serviços nacional embarcada (Anexo B do portal da "
        "NFS-e). Aceita o código (com ou sem pontos) e a descrição — 'suporte "
        "informática'. Funciona sem internet."
    ),
)
def buscar_servicos_nacionais(
    user_token: dict = Depends(get_current_active_user),
    *,
    buscar: str = Query("", max_length=120),
    limite: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {"resultados": tabelas.buscar_servicos_nacionais(db, buscar, limite)}


@router.get(
    "/nbs",
    summary="Buscar NBS",
    description=(
        "Com `codigo_tributacao_nacional`, devolve em `sugeridos` os NBS que a "
        "Receita correlaciona com ele (Anexo VIII). Com `buscar`, procura na "
        "tabela NBS inteira, pelo código ou pela descrição."
    ),
)
def buscar_nbs(
    user_token: dict = Depends(get_current_active_user),
    *,
    buscar: str = Query("", max_length=120),
    codigo_tributacao_nacional: str = Query("", max_length=10),
    limite: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return {
        "sugeridos": tabelas.nbs_sugeridos(db, codigo_tributacao_nacional),
        "resultados": tabelas.buscar_nbs(db, buscar, limite),
    }


# ===========================================================================
# NFS-e DA OS (F3): conferir, ver a DPS, emitir, consultar e cancelar
#
# Consulta e cancelamento chamam os MESMOS serviços da NF-e (eles escolhem a
# rota da plataforma pelo `tipo_documento`); existem aqui de novo só porque as
# rotas do Centro Fiscal exigem o módulo NFE, e o prestador MEI tem só a NFS-e.
# ===========================================================================

def _nfse_ou_404(db: Session, documento_id: int):
    from app.db.crud import fiscal as crud

    doc = crud.get_documento_fiscal(db, documento_id)
    if not doc or doc.tipo_documento != "NFSE":
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")
    return doc


@router.get(
    "/os/{numero_os}/verificar",
    response_model=ResultadoVerificacaoFiscal,
    summary="O que falta para a NFS-e da OS",
)
def verificar_nfse_da_os(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    numero_os: str = Path(...),
    db: Session = Depends(get_db),
):
    from app.db.crud import fiscal as crud
    from app.services.fiscal.nfse.completude import verificar_nfse_os
    from app.services.fiscal.nfse.rota import rota_da_empresa

    os_obj = crud.get_os_completa(db, numero_os)
    if not os_obj:
        raise HTTPException(status_code=404, detail="Ordem de Serviço não encontrada.")
    empresa_id = user_token["empresa_id"]
    fs = crud.get_fiscal_settings(db, empresa_id)
    pendencias, _ = verificar_nfse_os(
        db, os_obj, crud.get_empresa(db, empresa_id), crud.get_endereco_empresa(db, empresa_id),
        uma_nota_por_codigo=bool(fs and fs.nfse_uma_nota_por_codigo),
        rota=rota_da_empresa(db, empresa_id),
    )
    return ResultadoVerificacaoFiscal(completo=not pendencias, pendencias=pendencias)


@router.get("/os-para-emitir", summary="OS finalizadas prontas para a NFS-e (para escolher com um clique)")
def listar_os_para_emitir(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    buscar: str = Query("", max_length=80, description="Número curto ('158') ou nome do cliente"),
    limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.os_para_emitir import os_para_emitir

    return os_para_emitir(db, user_token["empresa_id"], buscar, limite)


@router.post("/os/{numero_os}/preview", summary="A DPS que sairia (não envia nada)")
def preview_nfse_da_os(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    numero_os: str = Path(...),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.emissao_os import preview_nfse_os

    return preview_nfse_os(db, numero_os, user_token["empresa_id"])


@router.post("/os/{numero_os}/emitir", response_model=EmissaoResponse, summary="Emitir a NFS-e da OS")
def emitir_nfse_da_os(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(check_permission(required_permission="servico")),
    numero_os: str = Path(...),
    confirmar_duplicidade: bool = Query(
        False, description="O operador viu o aviso de nota repetida (409 NOTA_DUPLICADA_SUSPEITA) e confirmou.",
    ),
    codigo_nacional: Optional[str] = Query(
        None, max_length=10, description="Com uma nota por código (G3): qual código emitir.",
    ),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import poll_nfe_status_async
    from app.services.fiscal.nfse.emissao_os import emitir_nfse_os

    empresa_id = user_token["empresa_id"]
    doc = _handle_db_transaction(
        db, emitir_nfse_os, numero_os, empresa_id, None, confirmar_duplicidade, codigo_nacional,
    )
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)
    return EmissaoResponse.de_documento(doc, "NFS-e")


@router.get("/documentos/{documento_id}", summary="Detalhe da NFS-e (motivo inteiro, o que fazer, tentativas)")
def obter_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    documento_id: int = Path(...),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.detalhe import detalhe_nfse

    detalhe = detalhe_nfse(db, documento_id)
    if detalhe is None:
        raise HTTPException(status_code=404, detail="NFS-e não encontrada.")
    return detalhe


@router.post("/documentos/{documento_id}/consultar", response_model=EmissaoResponse, summary="Consultar a NFS-e")
def consultar_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    documento_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import consultar_documento

    _nfse_ou_404(db, documento_id)
    doc = _handle_db_transaction(db, consultar_documento, documento_id, user_token["empresa_id"])
    return EmissaoResponse.de_documento(doc, "NFS-e")


@router.post("/documentos/{documento_id}/cancelar", response_model=EmissaoResponse, summary="Cancelar a NFS-e")
def cancelar_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    documento_id: int = Path(..., ge=1),
    payload: CancelamentoRequest = Body(...),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import cancelar_documento

    _nfse_ou_404(db, documento_id)
    doc = _handle_db_transaction(db, cancelar_documento, documento_id, user_token["empresa_id"], payload.justificativa)
    return EmissaoResponse.de_documento(doc, "NFS-e")


@router.get("/exportar-xml", summary="XMLs das NFS-e do período (ZIP para o contador)")
def exportar_xml_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db),
):
    """O mesmo pacote do Centro Fiscal (`fiscal_documentos.exportar_xml_periodo`),
    só com NFS-e — aquela rota exige o módulo NFE, e o MEI tem só a NFS-e."""
    from fastapi.responses import Response
    from app.services.fiscal.documentos.exportacao_xml import montar_pacote_xml

    if data_fim < data_inicio:
        raise HTTPException(status_code=422, detail="data_fim anterior a data_inicio.")
    if (data_fim - data_inicio).days > 366:
        raise HTTPException(status_code=422, detail="O período máximo é de um ano.")
    conteudo, resumo = montar_pacote_xml(db, user_token["empresa_id"], data_inicio, data_fim, "NFSE")
    return Response(
        content=conteudo,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="xml-nfse-{data_inicio:%Y-%m-%d}_{data_fim:%Y-%m-%d}.zip"',
            "X-Fiscal-Documentos": str(resumo["documentos"]),
            "X-Fiscal-Baixados": str(resumo["baixados"]),
            "X-Fiscal-Nao-Baixados": str(resumo["nao_baixados"]),
        },
    )


@router.get("/documentos", summary="As NFS-e emitidas (mais recentes primeiro)")
def listar_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """A lista da aba NFS-e. O código de verificação vem do espelho na OS
    (`nfse/espelho.py`), porque `documento_fiscal` não tem coluna para ele."""
    from app.db.models.documento_fiscal import DocumentoFiscal
    from app.db.models.ordem_servico_nota_fiscal import OrdemServicoNotaFiscal

    linhas = (
        db.query(DocumentoFiscal, OrdemServicoNotaFiscal.codigo_verificacao_nfse)
        .outerjoin(OrdemServicoNotaFiscal, OrdemServicoNotaFiscal.os_id == DocumentoFiscal.origem_id)
        .filter(DocumentoFiscal.tipo_documento == "NFSE")
        .order_by(DocumentoFiscal.data_criacao.desc(), DocumentoFiscal.id.desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "id": doc.id,
            "numero_os": doc.origem_numero_os,
            "status": doc.status,
            "numero": doc.numero_documento,
            "codigo_verificacao": doc.codigo_verificacao or codigo,
            "valor_total": doc.valor_total,
            "tomador": doc.destinatario_nome_enviado,
            "mensagem": doc.mensagem_sefaz,
            "url_pdf": doc.url_pdf,
            "url_consulta": doc.url_consulta,
            "ambiente": doc.ambiente_emissao,
            "data_emissao": doc.data_emissao,
            "data_autorizacao": doc.data_autorizacao,
        }
        for doc, codigo in linhas
    ]


# ===========================================================================
# CONFIGURAÇÃO DA NFS-e (G3): as decisões do contador como opção
# ===========================================================================

def _settings_ou_422(db: Session, empresa_id: int):
    from app.db.crud import fiscal as crud

    fs = crud.get_fiscal_settings(db, empresa_id)
    if not fs:
        raise HTTPException(status_code=422, detail="Configurações fiscais não cadastradas para esta empresa.")
    return fs


@router.get("/configuracao", response_model=NfseConfiguracao, summary="Configuração da NFS-e")
def obter_configuracao_nfse(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    db: Session = Depends(get_db),
):
    return NfseConfiguracao.model_validate(_settings_ou_422(db, user_token["empresa_id"]))


@router.put("/configuracao", response_model=NfseConfiguracao, summary="Salvar a configuração da NFS-e")
def salvar_configuracao_nfse(
    dados: NfseConfiguracao,
    user_token: dict = Depends(check_permission(required_permission="servico")),
    db: Session = Depends(get_db),
):
    def _salvar(db: Session):
        fs = _settings_ou_422(db, user_token["empresa_id"])
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(fs, campo, valor)
        db.flush()
        return NfseConfiguracao.model_validate(fs)

    return _handle_db_transaction(db, _salvar)


@router.get("/resumo", summary="Contadores das NFS-e por status (cards da aba NFS-e)")
def obter_resumo_nfse(
    user_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """O mesmo resumo da NF-e, só das NFS-e: a rota da NF-e exige o módulo NFE,
    e o prestador MEI tem só a NFS-e."""
    from app.services.fiscal.documentos import consultas

    return consultas.obter_resumo(db, tipo="NFSE")


@router.get("/saude", summary="Saúde Fiscal da NFS-e (o que falta para a nota sair)")
def obter_saude_nfse(
    user_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.saude import saude_nfse

    return saude_nfse(db, user_token["empresa_id"])


@router.get("/rota", summary="Por onde sai a NFS-e e o que a nota pede (para a tela)")
def obter_rota_nfse(
    user_token: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Rota (Nacional/Municipal/pendente), cidade, campos que a cidade exige e o
    regime da empresa. Sem resposta da plataforma, vale a Nacional."""
    from app.services.fiscal.nfse.rota import perfil_para_tela

    return perfil_para_tela(db, user_token["empresa_id"])


# ===========================================================================
# NFS-e AVULSA (G4): serviço que não passou por OS
# ===========================================================================

@router.post("/avulsa/preview", summary="A DPS da NFS-e avulsa (não envia nada)")
def preview_nfse_avulsa(
    dados: NfseAvulsaRequest,
    user_token: dict = Depends(check_permission(required_permission="servico")),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.avulsa import preview_nfse_avulsa as _preview

    return _preview(db, user_token["empresa_id"], dados)


@router.post("/avulsa/emitir", response_model=EmissaoResponse, summary="Emitir NFS-e avulsa")
def emitir_nfse_avulsa(
    dados: NfseAvulsaRequest,
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(check_permission(required_permission="servico")),
    confirmar_duplicidade: bool = Query(False),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import poll_nfe_status_async
    from app.services.fiscal.nfse.avulsa import emitir_nfse_avulsa as _emitir

    empresa_id = user_token["empresa_id"]
    doc = _handle_db_transaction(db, _emitir, empresa_id, dados, confirmar_duplicidade)
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)
    return EmissaoResponse.de_documento(doc, "NFS-e")


# ===========================================================================
# MARCENARIA (G5): a NFS-e da instalação, uma por OS
# ===========================================================================

@router.post("/os/{numero_os}/instalacao/preview", summary="A DPS da instalação (não envia nada)")
def preview_nfse_instalacao(
    user_token: dict = Depends(check_permission(required_permission="servico")),
    numero_os: str = Path(...),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.nfse.marcenaria import preview_nfse_instalacao as _preview

    return _preview(db, numero_os, user_token["empresa_id"])


@router.post("/os/{numero_os}/instalacao/emitir", response_model=EmissaoResponse,
             summary="Emitir a NFS-e da instalação dos móveis")
def emitir_nfse_instalacao(
    background_tasks: BackgroundTasks,
    user_token: dict = Depends(check_permission(required_permission="servico")),
    numero_os: str = Path(...),
    confirmar_duplicidade: bool = Query(False),
    db: Session = Depends(get_db),
):
    from app.services.fiscal.emissao import poll_nfe_status_async
    from app.services.fiscal.nfse.marcenaria import emitir_nfse_instalacao as _emitir

    empresa_id = user_token["empresa_id"]
    doc = _handle_db_transaction(db, _emitir, numero_os, empresa_id, confirmar_duplicidade)
    if doc.status == "PROCESSANDO":
        background_tasks.add_task(poll_nfe_status_async, doc.id, empresa_id)
    return EmissaoResponse.de_documento(doc, "NFS-e")
