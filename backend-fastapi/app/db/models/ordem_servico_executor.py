# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/ordem_servico_executor.py
# DESCRICAO: Quem EXECUTA a OS, alem do responsavel (docs/lava-rapido/
#            SPEC-00 O7a e Spec 10A). No lava-rapido: os lavadores.
# ---------------------------------------------------------------------------
"""
O responsavel da OS (`ordens_servico.funcionario_id`) e quem a abriu, como
sempre. Na loja pequena quem abre tambem lava; na grande, o atendente abre e
um ou dois lavadores executam. Esta tabela registra os executores.

Generica de proposito (nome nao fala de lavagem): so e usada pelo segmento
que declara a capacidade `executores_os`. Sem linha aqui, a OS e exatamente
a de sempre -- e a comissao vai para o responsavel, como hoje.

COMISSAO: com executores, a mao de obra da OS vai para ELES, dividida ou
inteira conforme o dono configurou no cargo/funcionario (`comissao_divisao`,
SPEC-00 O7c). Ver db/crud/relatorio/equipe.py.
"""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OrdemServicoExecutor(Base):
    __tablename__ = "ordem_servico_executores"
    __table_args__ = (
        # O mesmo lavador duas vezes na OS dobraria a parte dele na comissao.
        UniqueConstraint("ordem_servico_id", "funcionario_id", name="uq_os_executor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ordem_servico_id: Mapped[int] = mapped_column(
        ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"), nullable=False, index=True,
    )
