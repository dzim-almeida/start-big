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
from app.services.fiscal.nfse.rota import RotaNfse, exige_nbs, pendencia_da_rota, pendencias_do_servico


def _p(categoria: str, campo: str, mensagem: str, ref_id: Optional[int] = None, ref_nome: Optional[str] = None):
    return PendenciaFiscal(categoria=categoria, campo=campo, mensagem=mensagem,
                           referencia_id=ref_id, referencia_nome=ref_nome)


class GrupoNfse:
    """Os serviços de UM código nacional: uma NFS-e (D2)."""

    __slots__ = ("codigo", "fiscal", "itens")

    def __init__(self, codigo: str, fiscal, itens: list):
        self.codigo, self.fiscal, self.itens = codigo, fiscal, itens


def verificar_nfse_os(
    db: Session, os_obj, empresa, endereco, uma_nota_por_codigo: bool = False,
    rota: Optional[RotaNfse] = None,
) -> tuple[list[PendenciaFiscal], list[GrupoNfse]]:
    """Pendências da NFS-e da OS e os grupos que viram nota (um por código nacional).

    Sem `uma_nota_por_codigo` (o padrão, G3), códigos diferentes na mesma OS são
    pendência — a DPS leva um serviço só, e juntar códigos é declarar errado.
    Com a opção, cada código vira a sua nota. Com pendência, os grupos vêm vazios.

    `rota` (G6): na municipal, cobra o que a cidade exige e não cobra o NBS;
    pendente, avisa. Sem ela, as regras da Nacional (as de antes).
    """
    pendencias: list[PendenciaFiscal] = []
    da_rota = pendencia_da_rota(rota)
    if da_rota:
        pendencias.append(da_rota)

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
        return pendencias, []

    grupos: dict[str, GrupoNfse] = {}
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
        if not fiscal.codigo_nbs and exige_nbs(rota):
            pendencias.append(_p("item", "codigo_nbs",
                                 "Sem NBS (cadastro do serviço › NFS-e Nacional).", item.servico.id, nome))
        pendencias.extend(pendencias_do_servico(rota, fiscal, item.servico.id, nome))
        codigo = fiscal.codigo_tributacao_nacional
        if codigo not in grupos:
            grupos[codigo] = GrupoNfse(codigo, fiscal, [])
        grupos[codigo].itens.append(item)

    if len(grupos) > 1 and not uma_nota_por_codigo:
        pendencias.append(_p(
            "item", "codigos_diferentes",
            "Os serviços desta OS têm códigos de tributação nacional diferentes "
            f"({', '.join(sorted(grupos))}). A NFS-e leva um código por nota "
            "(ou ligue 'uma nota por código' na configuração da NFS-e).",
        ))

    for grupo in grupos.values():
        base = sum(i.valor_total for i in grupo.itens)
        if base - desconto_dos_servicos(os_obj, base) <= 0:
            pendencias.append(_p("item", "valor", f"O valor dos serviços do código {grupo.codigo} é zero."))

    return pendencias, ([] if pendencias else list(grupos.values()))
