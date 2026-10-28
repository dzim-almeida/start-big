# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/completude.py
# DESCRIÇÃO: O que impede a NFS-e de uma OS, nomeado ANTES de enviar
#            (docs/nfse-plano.md, F3).
# ---------------------------------------------------------------------------
"""
Por que não dentro de `completude/validators.py`: aquela verificação roda hoje
em TODA OS (tipo "ambos"), inclusive de quem não tem NFS-e. Cobrar código
nacional e NBS lá mostraria pendência nova a quem nem emite nota de serviço.
Esta só roda quando alguém pede a NFS-e — e só com o módulo NFSE.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.db.crud import fiscal as crud
from app.schemas.fiscal.verificacao import PendenciaFiscal
from app.services.fiscal.nfse.municipio import codigo_ibge
from app.services.fiscal.nfse.payload import desconto_dos_servicos, servicos_da_os


def _p(categoria: str, campo: str, mensagem: str, ref_id: Optional[int] = None, ref_nome: Optional[str] = None):
    return PendenciaFiscal(categoria=categoria, campo=campo, mensagem=mensagem,
                           referencia_id=ref_id, referencia_nome=ref_nome)


def verificar_nfse_os(db: Session, os_obj, empresa, endereco) -> tuple[list[PendenciaFiscal], Optional[object]]:
    """Pendências da NFS-e da OS e o `ServicoFiscal` que vai na nota (D2: um só código)."""
    pendencias: list[PendenciaFiscal] = []

    documento = "".join(c for c in (getattr(empresa, "documento", None) or "") if c.isdigit())
    if len(documento) != 14:
        pendencias.append(_p("emitente", "cnpj", "Informe o CNPJ da empresa em Dados da Empresa."))

    uf = getattr(getattr(endereco, "estado", None), "value", getattr(endereco, "estado", None))
    if endereco is None or not codigo_ibge(endereco.cidade, uf):
        pendencias.append(_p(
            "emitente", "municipio",
            "Não foi possível identificar a cidade da empresa. Confira cidade e UF em Dados da Empresa.",
        ))

    itens = servicos_da_os(os_obj)
    if not itens:
        pendencias.append(_p("item", "itens_servico", "A OS não tem serviço aprovado para a nota de serviço."))
        return pendencias, None

    fiscais = []
    for item in itens:
        if not item.servico_id or not item.servico:
            pendencias.append(_p("item", "avulso_servico",
                                 "Serviço avulso: cadastre o serviço para emitir a NFS-e.", item.id, item.nome))
            continue
        fiscal = crud.get_servico_fiscal(db, item.servico.id)
        nome = item.servico.descricao
        if not fiscal or not fiscal.codigo_tributacao_nacional:
            pendencias.append(_p("item", "codigo_tributacao_nacional",
                                 "Sem código de tributação nacional (cadastro do serviço › NFS-e Nacional).",
                                 item.servico.id, nome))
            continue
        if not fiscal.codigo_nbs:
            pendencias.append(_p("item", "codigo_nbs",
                                 "Sem NBS (cadastro do serviço › NFS-e Nacional).", item.servico.id, nome))
        fiscais.append(fiscal)

    codigos = {f.codigo_tributacao_nacional for f in fiscais}
    if len(codigos) > 1:
        # D2: a DPS leva UM serviço. Juntar códigos diferentes numa nota é
        # declarar errado; uma nota por código fica para quando alguém precisar.
        pendencias.append(_p(
            "item", "codigos_diferentes",
            "Os serviços desta OS têm códigos de tributação nacional diferentes "
            f"({', '.join(sorted(codigos))}). A NFS-e leva um código por nota.",
        ))

    base = sum(i.valor_total for i in itens)
    if base - desconto_dos_servicos(os_obj, base) <= 0:
        pendencias.append(_p("item", "valor", "O valor dos serviços desta OS é zero."))

    return pendencias, (fiscais[0] if fiscais and len(codigos) == 1 else None)
