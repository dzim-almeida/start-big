# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/lava_rapido/porte.py
# DESCRICAO: Portes de veiculo da loja e preco/duracao de cada servico por
#            porte (docs/lava-rapido/ SPEC-00 P1, P2a, P5 e Spec 02A).
# ---------------------------------------------------------------------------
"""
POR QUE TABELA, E NAO LISTA NO CODIGO. Cada lava-rapido divide os portes de
um jeito (P/M/G, hatch/seda/SUV, caminhao por eixo). Lista fixa no registry
obrigaria a gerar um instalador para trocar um nome. O registry so traz a
lista INICIAL, gravada aqui na primeira leitura (P2a).

POR QUE O PRECO MORA FORA DE `servicos`. Um servico ("Lavagem completa") tem
um preco por porte. Cadastrar "Lavagem - SUV", "Lavagem - Hatch"... como
servicos separados multiplicaria o catalogo e erraria no balcao (P1). Sem
linha para o porte, vale o `servicos.valor` de sempre -- e e por isso que a
tabela de servicos nao muda (PR1).

Porte nunca e apagado, so desativado: some das escolhas, mas os precos e os
veiculos que ja o usam continuam legiveis.
"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PorteVeiculo(Base):
    """Um porte da loja, dentro de um tipo de veiculo ("SUV" em "carro")."""

    __tablename__ = "portes_veiculo"
    __table_args__ = (
        # Dois "SUV" no mesmo tipo deixariam o preco ambiguo.
        UniqueConstraint("tipo_veiculo", "nome", name="uq_portes_veiculo_tipo_nome"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Id do tipo de trabalho do registry ("carro", "moto", "pesado"...).
    tipo_veiculo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    # Posicao do botao na tela, da esquerda para a direita.
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ServicoPrecoPorte(Base):
    """Preco (e duracao) de um servico para um porte."""

    __tablename__ = "servico_precos_porte"
    __table_args__ = (
        UniqueConstraint("servico_id", "porte_id", name="uq_servico_precos_porte"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    servico_id: Mapped[int] = mapped_column(
        ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    porte_id: Mapped[int] = mapped_column(
        ForeignKey("portes_veiculo.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    valor: Mapped[int] = mapped_column(Integer, nullable=False)              # centavos (PR3)
    # Minutos de trabalho; alimenta a previsao de entrega (O4). Vazio = sem previsao.
    duracao_minutos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
