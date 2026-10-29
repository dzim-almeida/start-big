# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/os_para_emitir.py
# DESCRIÇÃO: As OS prontas para a NFS-e, para a tela escolher com um clique
#            (docs/nfse-melhorias-plano.md, M3; revisão do Alan: "ninguém
#            lembra OS-2026-000158").
# ---------------------------------------------------------------------------
"""
Só leitura. Uma OS entra na lista quando:
- está FINALIZADA (a mesma regra da emissão, `emissao_os.emitir_nfse_os`);
- tem serviço aprovado (`servicos_da_os`) e não é da marcenaria (lá a
  instalação tem fluxo próprio, G5);
- ainda não tem NFS-e viva — salvo com "uma nota por código" ligada, em que
  a OS pode ter um código emitido e outro por emitir (a tela marca qual).

A busca aceita o número curto ("158" acha OS-2026-000158) e o nome do cliente.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.busca import normalizar
from app.core.enum import OrdemServicoStatus
from app.db.crud import fiscal as crud
from app.db.models.ordem_servico import OrdemServico
from app.services.fiscal.nfse.payload import desconto_dos_servicos, servicos_da_os

ORIGEM_MARCENARIA = "ORCAMENTO_MARCENARIA"
# Janela das OS finalizadas olhadas por consulta: a lista é para o dia a dia,
# e a busca por número continua achando as antigas.
JANELA = 300


def _nome_cliente(os_obj) -> Optional[str]:
    cliente = getattr(getattr(os_obj, "objeto", None), "cliente", None)
    if cliente is None:
        return None
    return (getattr(cliente, "razao_social", None) or getattr(cliente, "nome_fantasia", None)
            or getattr(cliente, "nome", None))


def os_para_emitir(db: Session, empresa_id: int, buscar: str = "", limite: int = 30) -> list[dict]:
    fs = crud.get_fiscal_settings(db, empresa_id)
    varias_por_os = bool(fs and getattr(fs, "nfse_uma_nota_por_codigo", False))

    termo = (buscar or "").strip()
    numero_inteiro = termo.upper().startswith("OS")
    so_digitos = termo.isdigit()

    consulta = db.query(OrdemServico).filter(OrdemServico.status == OrdemServicoStatus.FINALIZADA)
    if numero_inteiro:
        consulta = consulta.filter(OrdemServico.numero_os.ilike(f"%{termo}%"))
    elif so_digitos:
        # "158" acha OS-2026-000158 (o número termina com os dígitos).
        consulta = consulta.filter(OrdemServico.numero_os.like(f"%{termo}"))
    consulta = consulta.order_by(OrdemServico.data_finalizacao.desc(), OrdemServico.id.desc()).limit(JANELA)

    alvo_nome = normalizar(termo) if termo and not (numero_inteiro or so_digitos) else ""
    resultado: list[dict] = []
    for os_obj in consulta.all():
        if any(getattr(i, "origem", None) == ORIGEM_MARCENARIA for i in os_obj.itens):
            continue
        itens = servicos_da_os(os_obj)
        if not itens:
            continue
        cliente = _nome_cliente(os_obj)
        if alvo_nome and alvo_nome not in normalizar(cliente or "") and alvo_nome not in normalizar(os_obj.numero_os):
            continue
        tem_nfse = crud.get_nfse_ativa_por_os(db, os_obj.numero_os) is not None
        if tem_nfse and not varias_por_os:
            continue
        base = sum(i.valor_total for i in itens)
        data = os_obj.data_finalizacao or os_obj.data_criacao
        resultado.append({
            "numero_os": os_obj.numero_os,
            "cliente": cliente,
            "data": data.isoformat() if data else None,
            "valor_servicos": base - desconto_dos_servicos(os_obj, base),
            "nfse_parcial": tem_nfse,
        })
        if len(resultado) >= limite:
            break
    return resultado
