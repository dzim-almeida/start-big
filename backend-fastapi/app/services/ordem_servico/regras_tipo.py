# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/regras_tipo.py
# DESCRICAO: Regras da OS ligadas ao tipo de trabalho e ao item que veio de
#            outro documento (Specs 03A e 08A da marcenaria).
#
# Era services/ordem_servico_regras_tipo.py ate 13/10/2026.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core import segmentos as reg
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.services.segmentos import get_segmento_atual


# Item que veio de outro documento (ex.: orçamento técnico da marcenaria).
item_de_outro_documento_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Este item veio do orçamento. Para mudar, desfaça a aprovação ou crie uma nova versão do orçamento.",
)


def _assert_item_sem_origem(item: OSItemModel) -> None:
    """409 no item criado a partir de outro documento (Spec 08A da marcenaria, D18).

    Genérico de propósito: o serviço da OS não sabe o que é marcenaria, só que
    item com `origem` muda no documento de origem (desfazer a aprovação ou nova
    versão do orçamento). Item com origem nula -- todos os que existiam antes da
    coluna, e todo item lançado à mão -- passa direto.
    """
    if item.origem:
        raise item_de_outro_documento_exce


# Chave do tipo de trabalho dentro de `dados_adicionais` DA OS: é onde o
# frontend grava (OSObjetoDinamicoTab.vue, CHAVE_TIPO). Spec 03A, D9.
CHAVE_TIPO_TRABALHO = "tipo_trabalho"


def _assert_tipo_pode_ser_criado(db: Session, dados_adicionais_os: dict | None, origem_orcamento: bool) -> None:
    """Recusa a OS cujo tipo só nasce de outro documento (Spec 03A, D5-D7).

    Hoje é o caso de Móveis planejados (marcenaria), que nasce da aprovação de
    um orçamento. A regra lê a MARCAÇÃO do tipo no registry (`criacao_manual`),
    nunca o nome do segmento: serigrafia, oficina e informática declaram tipos
    criáveis à mão (ou nenhum tipo) e passam direto, como sempre.
    """
    if origem_orcamento:                                   # caminho legítimo da Spec 08A
        return
    tipo_id = (dados_adicionais_os or {}).get(CHAVE_TIPO_TRABALHO)  # pode vir ausente
    segmento = get_segmento_atual(db)                      # segmento da empresa
    if reg.tipo_permite_criacao_manual(segmento, tipo_id):  # tipo criável à mão: segue
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=(
            f"OS de {reg.label_do_tipo(segmento, tipo_id)} é criada pela aprovação "
            "de um orçamento. Use a tela Orçamentos."
        ),
    )


def _assert_tipo_pode_ser_trocado(db: Session, dados_atuais: dict | None, dados_novos: dict | None) -> None:
    """A OS não troca de tipo quando o antigo OU o novo só nasce de outro
    documento (Spec 03A, D8): uma OS de Móveis planejados virando outra coisa
    perderia o vínculo com o orçamento. Reenviar o MESMO tipo (o formulário
    reenvia tudo) não é troca.
    """
    tipo_antigo = (dados_atuais or {}).get(CHAVE_TIPO_TRABALHO)
    tipo_novo = (dados_novos or {}).get(CHAVE_TIPO_TRABALHO, tipo_antigo)
    if tipo_novo != tipo_antigo:                           # só olha o registry se mudou
        segmento = get_segmento_atual(db)
        if not (reg.tipo_permite_criacao_manual(segmento, tipo_antigo)
                and reg.tipo_permite_criacao_manual(segmento, tipo_novo)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="O tipo de trabalho desta OS não pode ser alterado.",
            )
