# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/ativacao.py
# DESCRIÇÃO: O emitente que vai junto com o certificado na ativação da emissão.
#
# A plataforma passou a CRIAR a empresa na emissora (06/10/2026) — antes, o
# primeiro cliente em produção precisou cadastrar tudo à mão no painel da
# Focus. Para criar, ela precisa de razão social, regime e endereço, que só o
# ERP tem. O ERP manda o MESMO bloco `emitente{}` das notas (que a SEFAZ já
# autoriza), montado pela mesma função: um dado só, num lugar só.
# ---------------------------------------------------------------------------

from typing import Optional

from app.services.fiscal.helpers import obter_crt


def montar_emitente_para_ativacao(empresa, endereco, fiscal_settings) -> dict:
    """Bloco `emitente{}` das notas; sem endereço cadastrado, vai sem ele.

    Sem endereço a plataforma ainda consegue ATUALIZAR uma empresa que já
    existe na emissora; para CRIAR, ela devolve a lista do que falta.
    """
    from app.services.fiscal.payload_builder import _montar_emitente, _so_digitos

    if endereco is not None:
        return _montar_emitente(empresa, endereco, fiscal_settings)

    return {
        "cnpj": _so_digitos(empresa.documento),
        "razao_social": empresa.razao_social,
        "nome_fantasia": empresa.nome_fantasia or empresa.razao_social,
        "inscricao_estadual": empresa.inscricao_estadual,
        "inscricao_municipal": empresa.inscricao_municipal,
        "codigo_regime_tributario": obter_crt(empresa),
        "regime_tributario": empresa.regime_tributario,
    }


def contato_da_empresa(empresa) -> tuple[Optional[str], Optional[str]]:
    """E-mail e telefone para o cadastro na emissora (opcionais lá)."""
    return getattr(empresa, "email", None), getattr(empresa, "telefone", None)
