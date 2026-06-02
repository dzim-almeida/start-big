from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class ConfiguracaoClientes(Base):
    """
    Configurações do módulo de clientes por empresa.
    Relacionamento 1:1 com Empresa.
    """
    __tablename__ = "configuracoes_clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Campos obrigatórios
    exigir_cpf_pf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_cnpj_pj: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_celular: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    exigir_rg_pf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_ie_pj: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exigir_endereco: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Exibição do formulário
    tipo_pessoa_padrao: Mapped[str] = mapped_column(String(2), default="PF", nullable=False)
    exibir_genero: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    exibir_data_nascimento: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Comportamento
    bloquear_faturamento_inativo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    oferecer_reativacao_rapida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Controle financeiro
    ativar_limite_credito: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bloquear_venda_limite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadados
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="config_clientes",
    )

    def __repr__(self) -> str:
        return f"<ConfiguracaoClientes(id={self.id}, empresa_id={self.empresa_id})>"
