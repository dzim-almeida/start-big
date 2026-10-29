# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/rota.py
# DESCRIÇÃO: Por onde sai a NFS-e desta empresa (Nacional × prefeitura) e o
#            que a cidade exige. G6 de backend-fastapi/docs/nfse-fase2-plano.md.
# ---------------------------------------------------------------------------
"""
Quem decide a rota é a PLATAFORMA (regime + cidade, com a palavra do suporte):
o ERP só pergunta (`GET /erp/fiscal/nfse/municipio`) e ajusta duas coisas:

- a completude: na rota municipal, cobra o que a cidade exige (código
  tributário municipal, CNAE) e deixa de cobrar o NBS, que só a Nacional pede;
  com a rota pendente, avisa ANTES de tentar (a plataforma recusaria);
- a DPS: na municipal, leva `_municipal{}` com CNAE e item da LC 116, que a
  plataforma usa na tradução para o formato da prefeitura.

O ERP manda a MESMA DPS nas duas rotas; a tradução é da plataforma.

Sem resposta (rede fora, plataforma antiga, sem módulo NFSE) vale a Nacional,
que é o comportamento de antes da G6: a conferência nunca trava a loja.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from app.schemas.fiscal.verificacao import PendenciaFiscal

logger = logging.getLogger(__name__)

NACIONAL = "NACIONAL"
MUNICIPAL = "MUNICIPAL"
MUNICIPAL_PENDENTE = "MUNICIPAL_PENDENTE"

# A rota muda quando o suporte decide a cidade: dez minutos bastam para não
# perguntar a cada tela, e a troca chega no mesmo dia.
_VALIDADE_S = 600
_cache: dict = {"quando": 0.0, "valor": None}


@dataclass
class RotaNfse:
    rota: str = NACIONAL
    cidade: Optional[str] = None
    # `*_obrigatorio_nfse` da Focus, sem o sufixo: {"codigo_cnae": True, ...}.
    obrigatorios: dict = field(default_factory=dict)
    exige_login: bool = False
    # False = a plataforma não respondeu; valem as regras da Nacional.
    confirmada: bool = False

    @property
    def municipal(self) -> bool:
        return self.rota == MUNICIPAL

    def exige(self, campo: str) -> bool:
        return self.municipal and self.obrigatorios.get(campo) is True


def _de_resposta(dados: dict) -> RotaNfse:
    if not dados or not dados.get("rota"):
        return RotaNfse()
    municipio = dados.get("municipio") or {}
    cidade = f"{municipio.get('nome')}/{municipio.get('uf')}" if municipio.get("nome") else None
    return RotaNfse(
        rota=str(dados["rota"]),
        cidade=cidade,
        obrigatorios=dict(municipio.get("obrigatorios") or {}),
        exige_login=bool(municipio.get("exige_login")),
        confirmada=True,
    )


def limpar_cache() -> None:
    _cache.update(quando=0.0, valor=None)


def consultar_plataforma(db, empresa_id: int) -> dict:
    """A resposta crua de `GET /erp/fiscal/nfse/municipio`; {} quando não há."""
    from app.core.config import settings
    from app.db.crud import fiscal as crud
    from app.services.fiscal.http import get_fiscal_client

    token = crud.get_licenca_token(db)
    if not token and not settings.FISCAL_MOCK_ENABLED:
        # Sem licença não há o que perguntar (a plataforma responderia 401).
        return {}
    fs = crud.get_fiscal_settings(db, empresa_id)
    ambiente = (fs.ambiente_emissao if fs else None) or 2
    return get_fiscal_client(ambiente, token).consultar_municipio_nfse()


def rota_da_empresa(db, empresa_id: int) -> RotaNfse:
    """A rota desta empresa, com cache de dez minutos. Nunca levanta."""
    agora = time.monotonic()
    if _cache["valor"] is not None and agora - _cache["quando"] < _VALIDADE_S:
        return _cache["valor"]
    try:
        dados = consultar_plataforma(db, empresa_id)
    except Exception as exc:  # pragma: no cover - rede de segurança
        logger.warning("[NFS-e] Rota da NFS-e indisponível: %s", exc)
        dados = {}
    rota = _de_resposta(dados)
    # Só guarda o que a plataforma confirmou: sem resposta, pergunta de novo
    # na próxima tela, em vez de prender a loja dez minutos na Nacional.
    if rota.confirmada:
        _cache.update(quando=agora, valor=rota)
    elif _cache["valor"] is not None:
        return _cache["valor"]
    return rota


def pendencia_da_rota(rota: Optional[RotaNfse]) -> Optional[PendenciaFiscal]:
    """A empresa toda: a cidade ainda não tem rota decidida."""
    if rota is None or rota.rota != MUNICIPAL_PENDENTE:
        return None
    return PendenciaFiscal(
        categoria="emitente", campo="rota_nfse",
        mensagem="A NFS-e da sua cidade ainda está sendo configurada pelo suporte StartBig. "
                 "Fale com o suporte para liberar a emissão.",
    )


def exige_nbs(rota: Optional[RotaNfse]) -> bool:
    """O NBS é campo da DPS Nacional; na prefeitura só vai se houver."""
    return rota is None or not rota.municipal


def pendencias_do_servico(
    rota: Optional[RotaNfse], fiscal, ref_id: Optional[int] = None, ref_nome: Optional[str] = None,
) -> list[PendenciaFiscal]:
    """O que a cidade exige do cadastro do serviço (só na rota municipal)."""
    if rota is None or not rota.municipal:
        return []
    falta: list[PendenciaFiscal] = []
    onde = f" ({rota.cidade})" if rota.cidade else ""
    if rota.exige("codigo_tributario_municipio") and not getattr(fiscal, "codigo_tributacao_municipio", None):
        falta.append(PendenciaFiscal(
            categoria="item", campo="codigo_tributacao_municipio",
            mensagem=f"A prefeitura{onde} exige o código tributário municipal (cadastro do serviço).",
            referencia_id=ref_id, referencia_nome=ref_nome,
        ))
    if rota.exige("codigo_cnae") and not getattr(fiscal, "cnae", None):
        falta.append(PendenciaFiscal(
            categoria="item", campo="cnae",
            mensagem=f"A prefeitura{onde} exige o CNAE do serviço (cadastro do serviço).",
            referencia_id=ref_id, referencia_nome=ref_nome,
        ))
    return falta


def extensao_municipal(rota: Optional[RotaNfse], fiscal) -> Optional[dict]:
    """O `_municipal{}` da DPS: só na rota municipal, e só com o que houver."""
    if rota is None or not rota.municipal:
        return None
    ext = {
        "codigo_cnae": getattr(fiscal, "cnae", None) or None,
        "item_lista_servico": getattr(fiscal, "codigo_servico_lc116", None) or None,
    }
    ext = {k: v for k, v in ext.items() if v}
    return ext or None
