# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa/fiscal.py
# DESCRICAO: Empresa - configuracao fiscal (ambiente, serie, numeracao, CSC...).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

# Importa modelos e serviços
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.schemas.empresa import (
    FiscalSettingsUpdate,
)


# A pasta `certificados` (A1 guardado no disco) deixou de ser criada em
# 12/10/2026, com a aposentadoria de `upload_certificado_a1`. Arquivos que ja
# estejam la nas lojas ficam onde estao: nada aqui os apaga.

# Campos cuja edição explícita equivale a confirmar a numeração fiscal
# (ver `update_fiscal_settings`).
CAMPOS_QUE_CONFIRMAM_NUMERACAO = frozenset({
    "serie_nfe", "ultimo_numero_nfe", "serie_nfce", "ultimo_numero_nfce",
})


# ---------------------------------------------------------------------------
# FUNÇÕES DE CONFIGURAÇÕES FISCAIS
# ---------------------------------------------------------------------------

def get_or_create_fiscal_settings(db: Session, empresa_id: int) -> EmpresaFiscalSettings:
    """
    Garante que fiscal_settings sempre existe para uma empresa.
    Se não existir, cria com valores padrão.

    Args:
        db: Sessão do banco de dados.
        empresa_id: ID da empresa.

    Returns:
        EmpresaFiscalSettings: Configurações fiscais da empresa.
    """
    settings = db.query(EmpresaFiscalSettings).filter(
        EmpresaFiscalSettings.empresa_id == empresa_id
    ).first()

    if not settings:
        settings = EmpresaFiscalSettings(empresa_id=empresa_id)
        db.add(settings)
        db.flush()
        db.refresh(settings)

    return settings


def update_fiscal_settings(
    db: Session,
    empresa_id: int,
    update_data: FiscalSettingsUpdate
) -> EmpresaFiscalSettings:
    """
    Atualiza configurações fiscais (upsert).

    Args:
        db: Sessão do banco de dados.
        empresa_id: ID da empresa.
        update_data: Dados para atualização.

    Returns:
        EmpresaFiscalSettings: Configurações atualizadas.
    """
    settings = get_or_create_fiscal_settings(db, empresa_id)

    update_dict = update_data.model_dump(exclude_unset=True)

    # O CSC é o segredo que autentica o QR Code da NFC-e: quem o tem consegue
    # forjar cupom em nome da loja. Vai para o banco cifrado, como a senha do
    # certificado A1 — ver `cifrar_csc_token`.
    #
    # A tela recebe o token MASCARADO e o devolve inteiro no salvamento. Gravar
    # a máscara destruiria o CSC configurado sem ninguém perceber — o erro só
    # apareceria na primeira venda, com o cupom sem QR Code válido. Por isso a
    # máscara é descartada aqui, e não tratada como "apagar o campo".
    if "csc_token" in update_dict:
        from app.services.fiscal.helpers import cifrar_csc_token, e_csc_mascarado

        if e_csc_mascarado(update_dict["csc_token"]):
            update_dict.pop("csc_token")
        else:
            update_dict["csc_token"] = cifrar_csc_token(update_dict["csc_token"])

    # Voltar o contador para trás de uma nota deste sistema repetiria o número
    # (Rejeição 204/539, número gasto). Confere com a série que vai valer.
    if update_dict.keys() & CAMPOS_QUE_CONFIRMAM_NUMERACAO:
        from app.services.fiscal.emissoes.numeracao import validar_novo_ultimo_numero

        for tipo, campo_serie, campo_ultimo in (
            ("NFE", "serie_nfe", "ultimo_numero_nfe"),
            ("NFCE", "serie_nfce", "ultimo_numero_nfce"),
        ):
            if campo_serie in update_dict or campo_ultimo in update_dict:
                validar_novo_ultimo_numero(
                    db, tipo,
                    update_dict.get(campo_serie, getattr(settings, campo_serie)),
                    update_dict.get(campo_ultimo, getattr(settings, campo_ultimo)),
                )

        # Número informado À MÃO vira o piso: abaixo dele, o que não tem nota é
        # do sistema anterior (ver `numeracao_piso_nfe`). Só quando muda — a
        # tela reenvia o valor de sempre, e isso não pode esconder buraco que o
        # próprio StartBig abriu.
        nova_serie = update_dict.get("serie_nfe", settings.serie_nfe)
        novo_ultimo = update_dict.get("ultimo_numero_nfe", settings.ultimo_numero_nfe)
        if nova_serie != settings.serie_nfe or novo_ultimo != settings.ultimo_numero_nfe:
            settings.numeracao_piso_nfe = novo_ultimo

    for field, value in update_dict.items():
        setattr(settings, field, value)

    # Quem digita série ou último número está, na prática, confirmando a
    # sequência -- não faz sentido exigir um segundo clique. Vale mesmo que o
    # payload traga `numeracao_confirmada=False` junto: o número manda.
    if update_dict.keys() & CAMPOS_QUE_CONFIRMAM_NUMERACAO:
        settings.numeracao_confirmada = True

    db.flush()
    db.refresh(settings)
    return settings
