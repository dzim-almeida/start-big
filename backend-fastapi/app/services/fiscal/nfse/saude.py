# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/saude.py
# DESCRIÇÃO: "Saúde Fiscal" da aba NFS-e: o que falta para a NFS-e sair,
#            item a item (docs/nfse-melhorias-plano.md, M4; pedido do Alan
#            para ter a mesma barra da aba NF-e).
# ---------------------------------------------------------------------------
"""
Só leitura. Quatro itens, cada um ok ou não, e a porcentagem é a fração dos
que estão ok — como a barra da NF-e:

- empresa: CNPJ e cidade identificável (o código IBGE vai na DPS);
- rota: por onde a nota sai, e se a cidade já foi decidida pelo suporte;
- certificado: enviado à emissora (o mesmo cadastro da NF-e);
- serviços: os ativos com o que a NFS-e da empresa pede (código nacional,
  NBS na Nacional e o que a cidade exige na municipal).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.db.models.servico import Servico
from app.db.models.servico_fiscal import ServicoFiscal
from app.services.fiscal.nfse.municipio import codigo_ibge
from app.services.fiscal.nfse.rota import MUNICIPAL_PENDENTE, exige_nbs, pendencias_do_servico, rota_da_empresa

# A lista de serviços vai para um popover: o suficiente para agir.
LIMITE_SERVICOS = 50


def _item(chave: str, titulo: str, ok: bool, detalhe: str, **extra) -> dict:
    return {"chave": chave, "titulo": titulo, "ok": ok, "detalhe": detalhe, **extra}


def _item_empresa(db: Session, empresa_id: int) -> dict:
    empresa = crud.get_empresa(db, empresa_id)
    endereco = crud.get_endereco_empresa(db, empresa_id)
    falta = []
    if len("".join(c for c in (getattr(empresa, "documento", None) or "") if c.isdigit())) != 14:
        falta.append("CNPJ")
    uf = getattr(getattr(endereco, "estado", None), "value", getattr(endereco, "estado", None))
    if endereco is None or not codigo_ibge(endereco.cidade, uf):
        falta.append("cidade e UF")
    if falta:
        return _item("empresa", "Dados da empresa", False, f"Confira em Dados da Empresa: {', '.join(falta)}.")
    return _item("empresa", "Dados da empresa", True, "CNPJ e cidade conferem.")


def _item_rota(rota) -> dict:
    titulo = "Por onde a nota sai"
    if rota.rota == MUNICIPAL_PENDENTE:
        return _item("rota", titulo, False,
                     f"A NFS-e de {rota.cidade or 'sua cidade'} ainda está sendo configurada pelo suporte StartBig.")
    if rota.municipal:
        return _item("rota", titulo, True, f"Sistema da prefeitura de {rota.cidade or 'sua cidade'}.")
    if not rota.confirmada:
        return _item("rota", titulo, True, "Padrão nacional (sem resposta da plataforma agora; vale o padrão).")
    return _item("rota", titulo, True, "Padrão nacional (nfse.gov.br).")


def _item_certificado(db: Session, empresa_id: int, agora: datetime) -> dict:
    titulo = "Certificado digital"
    fs = crud.get_fiscal_settings(db, empresa_id)
    status = getattr(fs, "certificado_status", None)
    validade = getattr(fs, "certificado_validade", None)
    if validade is not None and validade.tzinfo is None:
        validade = validade.replace(tzinfo=timezone.utc)
    if validade is not None and validade < agora:
        return _item("certificado", titulo, False, "Vencido. Envie o novo em Centro Fiscal › Configurações.")
    if status != "CONECTADO_NUVEM":
        return _item("certificado", titulo, False,
                     "Ainda não chegou à emissora. Envie em Centro Fiscal › Configurações.")
    return _item("certificado", titulo, True, "Enviado à emissora.")


def _item_servicos(db: Session, rota) -> dict:
    titulo = "Serviços prontos para a nota"
    linhas = (
        db.query(Servico, ServicoFiscal)
        .outerjoin(ServicoFiscal, ServicoFiscal.servico_id == Servico.id)
        .filter(Servico.ativo == True)  # noqa: E712
        .order_by(Servico.descricao)
        .all()
    )
    faltando = []
    for servico, fiscal in linhas:
        campos = []
        if fiscal is None or not fiscal.codigo_tributacao_nacional:
            campos.append("código nacional")
        if exige_nbs(rota) and (fiscal is None or not fiscal.codigo_nbs):
            campos.append("NBS")
        if fiscal is not None:
            campos += [p.campo.replace("_", " ") for p in pendencias_do_servico(rota, fiscal)]
        if campos:
            faltando.append({"id": servico.id, "nome": servico.descricao or "Sem descrição", "falta": ", ".join(campos)})

    if not linhas:
        return _item("servicos", titulo, False, "Nenhum serviço cadastrado ainda.", servicos=[], total_faltando=0)
    if faltando:
        return _item(
            "servicos", titulo, False,
            f"{len(faltando)} de {len(linhas)} serviço(s) sem os códigos da NFS-e.",
            servicos=faltando[:LIMITE_SERVICOS], total_faltando=len(faltando),
        )
    return _item("servicos", titulo, True, f"Todos os {len(linhas)} serviço(s) com os códigos da NFS-e.",
                 servicos=[], total_faltando=0)


def saude_nfse(db: Session, empresa_id: int, agora: datetime | None = None) -> dict:
    agora = agora or datetime.now(timezone.utc)
    rota = rota_da_empresa(db, empresa_id)
    itens = [
        _item_empresa(db, empresa_id),
        _item_rota(rota),
        _item_certificado(db, empresa_id, agora),
        _item_servicos(db, rota),
    ]
    prontos = sum(1 for i in itens if i["ok"])
    return {
        "percentual": round(prontos * 100 / len(itens)),
        "pendencias": len(itens) - prontos,
        "itens": itens,
    }
