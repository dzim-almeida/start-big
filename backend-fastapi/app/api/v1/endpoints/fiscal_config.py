# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/fiscal_config.py
# DESCRIÇÃO: Centro Fiscal — configuração: dados fiscais, tributação padrão, regras
# por NCM, perfis tributários, diagnóstico e certificado.
#
# Saiu do fiscal.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. As URLs não mudaram: `fiscal.py` inclui
# este router sem prefixo, e a trava do módulo NFE vem de lá.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.depends import get_current_active_user, get_db, requer_configuracao_fiscal, _handle_db_transaction
from app.db.crud import fiscal as fiscal_crud
from app.schemas.emissao_fiscal import DiagnosticoPlataforma, EnvioPlataforma, FiscalConfiguracao
from app.schemas.perfil_tributario import PerfilTributarioCreate, PerfilTributarioListItem, PerfilTributarioRead, PerfilTributarioUpdate
from app.schemas.tributacao import RegraNcmRead, RegraNcmUpsert, TributacaoPadraoRead, TributacaoPadraoUpdate
from app.services import perfil_tributario as perfil_tributario_service
from app.services.fiscal.helpers import dias_para_vencer_certificado, e_csc_mascarado, mascarar_csc, obter_csc_token
from app.services.fiscal.payload_builder import _so_digitos
from app.schemas.empresa import FiscalSettingsUpdate
from app.services.empresa import update_fiscal_settings, upload_certificado_focus
from fastapi import UploadFile, File, Form

# Sem `dependencies`: a trava do módulo NFE é herdada do router de `fiscal.py`.
router = APIRouter()


# ===========================================================================
# CONFIGURAÇÃO DO AMBIENTE FISCAL
# ===========================================================================

@router.get(
    "/configuracao",
    response_model=FiscalConfiguracao,
    summary="Configuração Fiscal",
    description="Retorna o ambiente atual (homologação/produção) e status do módulo.",
)
def obter_configuracao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    empresa_id = user_token["empresa_id"]
    fs = fiscal_crud.get_fiscal_settings(db, empresa_id)
    return _montar_configuracao(fs)


def _montar_configuracao(
    fs, csc_plataforma: EnvioPlataforma | None = None,
) -> FiscalConfiguracao:
    """Projeta `EmpresaFiscalSettings` (ou None) na resposta da tela.

    Compartilhado pelo GET e pelo PUT: os dois devolviam o mesmo objeto com o
    mapeamento copiado, e um campo novo tinha de ser lembrado nos dois lugares.
    """
    ambiente = fs.ambiente_emissao if fs else 2
    # "Configurado" passou a significar CHEGOU NA EMISSORA.
    #
    # `tipo_certificado == "NUVEM"` saiu desta conta: ele e gravado no upload
    # mesmo quando a plataforma nao recebeu o arquivo, e era o que fazia o card
    # exibir "Conectado" com o certificado parado nesta maquina. VALIDADO_LOCAL
    # e um estado proprio, e a tela o mostra como tal.
    cert_configurado = bool(
        fs and (
            fs.certificado_digital_path
            or fs.certificado_thumbprint
            or fs.certificado_status == "CONECTADO_NUVEM"
        )
    )
    cert_valido = bool(
        cert_configurado and fs.certificado_validade and fs.certificado_validade.replace(tzinfo=None) > datetime.now()
    )

    return FiscalConfiguracao(
        ambiente=ambiente,
        ambiente_label="Homologação" if ambiente == 2 else "Produção",
        # `or ambiente == 2` saiu: quem escolhe o client e a factory, e ela
        # olha SO o FISCAL_MOCK_ENABLED. Em homologacao a tela mostrava
        # "(mock)" enquanto a emissao batia de verdade na plataforma --
        # exatamente o tipo de mentira que atrapalha um diagnostico.
        mock_ativo=settings.FISCAL_MOCK_ENABLED,
        certificado_configurado=cert_configurado,
        certificado_valido=cert_valido,
        certificado_status=fs.certificado_status if fs else None,
        certificado_cnpj=fs.certificado_cnpj if fs else None,
        certificado_validade=fs.certificado_validade if fs else None,
        certificado_dias_restantes=dias_para_vencer_certificado(fs.certificado_validade) if fs else None,
        serie_nfe=fs.serie_nfe if fs else 1,
        ultimo_numero_nfe=fs.ultimo_numero_nfe if fs else 0,
        serie_nfce=fs.serie_nfce if fs else 1,
        ultimo_numero_nfce=fs.ultimo_numero_nfce if fs else 0,
        numeracao_confirmada=bool(fs and fs.numeracao_confirmada),
        csc_token=mascarar_csc(obter_csc_token(fs)) if fs else None,
        csc_configurado=bool(fs and obter_csc_token(fs)),
        csc_id=fs.csc_id if fs else None,
        # So o PUT que levou CSC novo preenche isto; no GET e' None.
        csc_plataforma=csc_plataforma,
        limite_consumidor_anonimo=(
            fs.limite_consumidor_anonimo if fs else 1000000
        ),
    )


# ===========================================================================
# TRIBUTAÇÃO DA LOJA (padrão + regras por NCM)
# ===========================================================================
#
# A cascata é: produto (exceção) → regra por NCM → padrão da loja.
# Ver `app/services/fiscal/tributacao.py` e `docs/cadastro-produto-plano.md`.
#
# LER é para qualquer usuário ativo; ESCREVER exige master
# (`requer_configuracao_fiscal`), porque muda o imposto de TODA nota futura —
# é decisão do dono, de preferência com o contador.


@router.get(
    "/tributacao-padrao",
    response_model=Optional[TributacaoPadraoRead],
    summary="Tributação Padrão da Loja",
    description=(
        "A resposta padrão da loja para CFOP, origem, CST/CSOSN e PIS/COFINS. "
        "Devolve null enquanto ninguém configurou — e nesse estado a cascata é "
        "inerte: cada produto vale pelo que tem gravado nele."
    ),
)
def obter_tributacao_padrao(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    from app.db.crud import tributacao as tributacao_crud

    return tributacao_crud.get_tributacao_padrao(db, user_token["empresa_id"])


@router.put(
    "/tributacao-padrao",
    response_model=TributacaoPadraoRead,
    summary="Salvar a Tributação Padrão da Loja",
    description=(
        "Cria ou atualiza a tributação padrão. Campo omitido não é apagado: "
        "vazio significa 'não decido isto' e deixa o produto responder."
    ),
)
def salvar_tributacao_padrao(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    dados: TributacaoPadraoUpdate,
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    from app.db.crud import tributacao as tributacao_crud

    def _salvar(db_: Session):
        registro = tributacao_crud.upsert_tributacao_padrao(
            db_, user_token["empresa_id"], dados,
        )
        # Quem confirmou importa: o padrão nasce SUGERIDO pelo motor de
        # derivação, e emitir com valor que ninguém olhou é o risco da nota
        # aceita e errada.
        registro.confirmado_em = datetime.now(timezone.utc)
        registro.confirmado_por = user_token.get("nome") or "Master"
        db_.flush()
        return registro

    return _handle_db_transaction(db, _salvar)


@router.get(
    "/regras-ncm",
    response_model=list[RegraNcmRead],
    summary="Regras Tributárias por NCM",
    description="As exceções ao padrão da loja. Quem tem dez pneus cadastra uma regra, e os dez obedecem.",
)
def listar_regras_ncm(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    from app.db.crud import tributacao as tributacao_crud

    return tributacao_crud.listar_regras_ncm(db, user_token["empresa_id"])


@router.put(
    "/regras-ncm/{ncm}",
    response_model=RegraNcmRead,
    summary="Salvar Regra Tributária de um NCM",
)
def salvar_regra_ncm(
    user_token: dict = Depends(requer_configuracao_fiscal),
    ncm: str = Path(..., min_length=8, max_length=8, description="NCM de 8 dígitos"),
    *,
    dados: RegraNcmUpsert,
    db: Session = Depends(get_db),
):

    from app.db.crud import tributacao as tributacao_crud

    if not ncm.isdigit():
        raise HTTPException(status_code=422, detail="NCM deve conter 8 dígitos numéricos.")

    return _handle_db_transaction(
        db, tributacao_crud.upsert_regra_ncm, user_token["empresa_id"], ncm, dados,
    )


@router.delete(
    "/regras-ncm/{ncm}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover Regra Tributária de um NCM",
    description=(
        "Os produtos daquele NCM voltam a seguir o padrão da loja. Nenhum "
        "produto é alterado — a cascata é resolvida na leitura."
    ),
)
def remover_regra_ncm(
    user_token: dict = Depends(requer_configuracao_fiscal),
    ncm: str = Path(..., min_length=8, max_length=8),
    *,
    db: Session = Depends(get_db),
):
    from app.db.crud import tributacao as tributacao_crud

    removeu = _handle_db_transaction(
        db, tributacao_crud.deletar_regra_ncm, user_token["empresa_id"], ncm,
    )
    if not removeu:
        raise HTTPException(status_code=404, detail=f"Nenhuma regra cadastrada para o NCM {ncm}.")


# ===========================================================================
# PERFIS TRIBUTÁRIOS (operação interestadual)
# ===========================================================================
#
# Um perfil agrupa as alíquotas que variam por UF de destino (interestadual,
# interna do destino, FCP, MVA-ST) para N produtos apontarem para ele
# (TASK004–006). Complementa a cascata acima, não a substitui.
#
# O perfil chega e sai EM BLOCO com suas regras: o PUT é replace-all. Ler é
# para qualquer usuário ativo (o cadastro de produto precisa da lista);
# escrever exige master, como a tributação padrão.


@router.get(
    "/perfis-tributarios",
    response_model=list[PerfilTributarioListItem],
    summary="Listar Perfis Tributários",
    description="Os perfis da empresa, sem as regras — só quantas cada um tem.",
)
def listar_perfis_tributarios(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    return perfil_tributario_service.listar_perfis(db, user_token["empresa_id"])


@router.post(
    "/perfis-tributarios",
    response_model=PerfilTributarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Perfil Tributário",
    description="Cria o perfil com a lista completa de regras (exige uma regra de fallback).",
)
def criar_perfil_tributario(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    dados: PerfilTributarioCreate,
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, perfil_tributario_service.criar_perfil, user_token["empresa_id"], dados,
    )


@router.get(
    "/perfis-tributarios/{perfil_id}",
    response_model=PerfilTributarioRead,
    summary="Detalhar Perfil Tributário",
)
def obter_perfil_tributario(
    user_token: dict = Depends(get_current_active_user),
    perfil_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    return perfil_tributario_service.obter_perfil(db, user_token["empresa_id"], perfil_id)


@router.put(
    "/perfis-tributarios/{perfil_id}",
    response_model=PerfilTributarioRead,
    summary="Atualizar Perfil Tributário",
    description="Troca a descrição e SUBSTITUI todas as regras pelas enviadas.",
)
def atualizar_perfil_tributario(
    user_token: dict = Depends(requer_configuracao_fiscal),
    perfil_id: int = Path(..., ge=1),
    *,
    dados: PerfilTributarioUpdate,
    db: Session = Depends(get_db),
):
    return _handle_db_transaction(
        db, perfil_tributario_service.atualizar_perfil, user_token["empresa_id"], perfil_id, dados,
    )


@router.delete(
    "/perfis-tributarios/{perfil_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Perfil Tributário",
    description="Apaga o perfil e suas regras. Recusa (409 PERFIL_EM_USO) se algum produto o usa.",
)
def excluir_perfil_tributario(
    user_token: dict = Depends(requer_configuracao_fiscal),
    perfil_id: int = Path(..., ge=1),
    *,
    db: Session = Depends(get_db),
):
    _handle_db_transaction(
        db, perfil_tributario_service.deletar_perfil, user_token["empresa_id"], perfil_id,
    )


# ===========================================================================
# ATIVACAO LOCAL DO MODULO -- REMOVIDA DE PROPOSITO
# ===========================================================================
#
# A feat/fiscal-module tinha aqui um POST /ativar que ligava uma flag local
# (empresa_fiscal_settings.modulo_fiscal_ativo) para liberar as telas. A
# propria docstring dizia que existia so ate o servidor de licencas mandar o
# claim de recursos no JWT.
#
# Aqui esse claim JA existe: e o `modulos`, o mesmo que o FINANCEIRO usa, e a
# concessao do NFE e feita pela plataforma, por plano ou por cliente. Manter a
# rota daria a um master a chance de destravar as telas na propria maquina --
# contra a regra de NEGAR por padrao que sustenta o modulo fiscal aqui.
#
# Se um dia o onboarding precisar de um empurrao, ele vem da plataforma, nao
# de uma coluna no SQLite do cliente.



@router.put(
    "/configuracao",
    response_model=FiscalConfiguracao,
    summary="Atualizar Configuração Fiscal",
    description="Atualiza configurações fiscais da empresa.",
)
def atualizar_configuracao(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    db: Session = Depends(get_db),
    payload: FiscalSettingsUpdate = Body(...)
):
    empresa_id = user_token["empresa_id"]
    # `update_fiscal_settings` termina em `flush`, nunca em `commit`, e o
    # `get_db` so fecha a sessao -- fechar com transacao pendente DESCARTA a
    # escrita. A tela dizia "salvo", devolvia os valores novos (que estao na
    # sessao) e no proximo GET tudo voltava ao que era: serie, numero, CSC e
    # limite nunca chegaram ao disco. Quem comita nesta base e o
    # `_handle_db_transaction`, como nos outros oito endpoints deste arquivo.
    fs = _handle_db_transaction(db, update_fiscal_settings, empresa_id, payload)

    # O CSC digitado aqui não vale nada até estar na ficha da empresa na
    # emissora — é ela quem monta o QR Code, e a nota não o carrega. Até
    # 15/09/2026 ele parava no SQLite: o cartão dizia "Configurado" e a
    # plataforma respondia `cscConfigurado=false`. Vai DEPOIS do commit, de
    # propósito: a plataforma fora do ar não pode desfazer a série e a
    # numeração que o lojista acabou de salvar. O que ela respondeu volta na
    # resposta para a tela contar a verdade.
    csc_plataforma = None
    if payload.csc_token and not e_csc_mascarado(payload.csc_token):
        from app.services.fiscal.http import get_fiscal_client

        resultado = get_fiscal_client(
            fs.ambiente_emissao or 2, fiscal_crud.get_licenca_token(db),
        ).enviar_csc(fs.csc_id or "", payload.csc_token)
        csc_plataforma = EnvioPlataforma(
            aceito=resultado["aceito"],
            indisponivel=resultado.get("indisponivel", False),
            mensagem=resultado.get("mensagem"),
        )

    return _montar_configuracao(fs, csc_plataforma=csc_plataforma)


@router.get(
    "/plataforma",
    response_model=DiagnosticoPlataforma,
    summary="Diagnóstico da Plataforma",
    description=(
        "O que a plataforma de emissão enxerga desta licença — ambiente, token, "
        "CSC e certificado — ao lado do CNPJ que este ERP envia como emitente."
    ),
)
def obter_diagnostico_plataforma(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    """
    Responde "de quem é o problema" sem abrir chamado.

    Quando a emissão é recusada, hoje o lojista só vê a mensagem que a
    plataforma devolveu — e ela costuma parecer da SEFAZ, porque o corpo do 4xx
    vira `mensagem_sefaz`. Não havia como olhar o outro lado.

    "Não sei" NUNCA vira "não configurado": se a consulta falhar,
    `consultar_config` devolve {} e esta rota responde `consultou=False`. Um
    diagnóstico indisponível não pode virar acusação.
    """
    from app.services.fiscal.http import get_fiscal_client

    empresa_id = user_token["empresa_id"]
    fs = fiscal_crud.get_fiscal_settings(db, empresa_id)
    ambiente = fs.ambiente_emissao if fs else 2

    empresa = fiscal_crud.get_empresa(db, empresa_id)
    cnpj_erp = _so_digitos(empresa.documento) if empresa else None

    config = get_fiscal_client(ambiente, fiscal_crud.get_licenca_token(db)).consultar_config()
    if not config:
        return DiagnosticoPlataforma(consultou=False, cnpj_erp=cnpj_erp)

    # A plataforma ainda não devolve o CNPJ da ficha dela. Aceitamos as duas
    # grafias prováveis para o dia em que devolver — até lá, `cnpj_confere` fica
    # None, que a tela mostra como "a plataforma não informa", e não como
    # divergência.
    cnpj_plataforma = _so_digitos(config.get("cnpj") or config.get("cnpjEmitente"))

    return DiagnosticoPlataforma(
        consultou=True,
        ambiente=config.get("ambiente"),
        ambiente_nome=config.get("ambienteNome"),
        configurado=config.get("configurado"),
        token_configurado=config.get("tokenConfigurado"),
        csc_configurado=config.get("cscConfigurado"),
        certificado_status=config.get("certificadoStatus"),
        pendencias=[str(p) for p in (config.get("pendencias") or [])],
        cnpj_erp=cnpj_erp,
        cnpj_plataforma=cnpj_plataforma,
        cnpj_confere=(
            None if not (cnpj_erp and cnpj_plataforma) else cnpj_erp == cnpj_plataforma
        ),
    )


@router.post(
    "/certificado/upload-focus",
    summary="Upload de Certificado para a Nuvem",
    description="Envia o certificado para a API da Focus NFe (simulado) e atualiza o status."
)
def upload_certificado_focus_endpoint(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    senha: str = Form(...)
):
    empresa_id = user_token["empresa_id"]
    # Mesmo defeito do PUT /configuracao acima: o servico so dava `flush`, e a
    # sessao morria sem `commit`. O lojista via "Certificado enviado com
    # sucesso!", reabria o Centro Fiscal e lia "Nao configurado" -- porque de
    # fato nada tinha sido gravado.
    resultado: dict = {}
    _handle_db_transaction(db, upload_certificado_focus, empresa_id, file, senha, resultado)

    # Respondia "enviado e configurado com sucesso" SEMPRE — inclusive quando o
    # certificado ficava só validado neste computador. Foi o que o primeiro
    # cliente em produção leu em 06/10/2026, antes de a primeira nota falhar.
    if resultado.get("aceito"):
        return {
            # A ativação diz se a empresa foi CRIADA ou atualizada na emissora.
            "message": resultado.get("mensagem") or "Certificado enviado à emissora.",
            "enviado": True,
            "certificado_status": resultado.get("certificado_status"),
        }
    return {
        "message": resultado.get("mensagem") or "O certificado foi conferido neste computador, mas não chegou à emissora.",
        "enviado": False,
        "certificado_status": resultado.get("certificado_status"),
    }


@router.post(
    "/certificado/reconferir",
    summary="Reconferir o certificado na plataforma",
    description=(
        "Pergunta à plataforma se o certificado já está na emissora e, se estiver, "
        "tira o cadastro local de 'Validado, não enviado'."
    ),
)
def reconferir_certificado_endpoint(
    user_token: dict = Depends(requer_configuracao_fiscal),
    *,
    db: Session = Depends(get_db),
):
    from app.services.fiscal.certificado import reconferir_certificado

    return _handle_db_transaction(db, reconferir_certificado, user_token["empresa_id"])
