# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_emitente.py
# DESCRIÇÃO: Bloco `emitente{}` do payload (o mesmo que vai na ativação).
#
# Saiu do payload_builder.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. O payload da nota não muda nem um byte
# (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.endereco import Endereco
from .helpers import obter_crt
from .payload_comum import _sanitizar_texto_sefaz, _so_digitos


def _montar_emitente(empresa: Empresa, endereco: Endereco, fiscal_settings: EmpresaFiscalSettings) -> dict:
    return {
        "cnpj": _so_digitos(empresa.documento),
        "razao_social": _sanitizar_texto_sefaz(empresa.razao_social),
        "nome_fantasia": _sanitizar_texto_sefaz(empresa.nome_fantasia or empresa.razao_social),
        "inscricao_estadual": empresa.inscricao_estadual,
        "inscricao_municipal": empresa.inscricao_municipal,
        # A SEFAZ espera o CRT numérico (1..4). O texto vai junto só como
        # rótulo — nunca é ele que decide a tributação.
        "codigo_regime_tributario": obter_crt(empresa),
        "regime_tributario": empresa.regime_tributario,
        "endereco": {
            "logradouro": endereco.logradouro,
            "numero": endereco.numero,
            "complemento": endereco.complemento or "",
            "bairro": endereco.bairro,
            "cidade": endereco.cidade,
            "uf": endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado),
            "cep": _so_digitos(endereco.cep),
        },
    }
