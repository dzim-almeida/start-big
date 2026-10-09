# ---------------------------------------------------------------------------
# ARQUIVO: app/db/models/marcenaria/orcamento.py
# DESCRICAO: Cabecalho do orcamento de marcenaria, os arquitetos (RT) e os
#            anexos da medicao (Spec 06A, secao 5).
# ---------------------------------------------------------------------------
"""
Uma linha de `marcenaria_orcamentos` por VERSAO: o codigo (ORC-2026-000084) se
repete em todas as versoes, e o par (codigo, versao) e unico (D16).

Unidades iguais as do motor da Spec 05 (D10): dinheiro em centavos, percentual
em basis points (9000 = 90%), tudo inteiro. Nada de float (SPEC-00, PR4).

Os valores CALCULADOS (preco, total, margem) NAO moram aqui: a cada leitura o
motor recalcula a partir da arvore (D5). O cabecalho guarda so um RESUMO para a
lista, que nao pode rodar o motor para 200 orcamentos.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.tempo import agora_utc
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.cliente import Cliente
    from app.db.models.fornecedor import Fornecedor
    from app.db.models.funcionario import Funcionario
    from app.db.models.marcenaria.ambiente import MarcenariaAmbiente
    from app.db.models.objeto_servico import ObjetoServico


class StatusOrcamento:
    """Os status do orcamento (secao 4.2). Texto gravado no banco."""
    RASCUNHO = "RASCUNHO"          # o unico editavel (D11)
    ENVIADO = "ENVIADO"            # o cliente recebeu a proposta (D13)
    APROVADO = "APROVADO"          # so a Spec 08A escreve (D19)
    RECUSADO = "RECUSADO"          # com motivo (D17)
    VENCIDO = "VENCIDO"            # enviado com a validade no passado (D14)
    SUBSTITUIDO = "SUBSTITUIDO"    # virou versao antiga (D16); so leitura

    TODOS = (RASCUNHO, ENVIADO, APROVADO, RECUSADO, VENCIDO, SUBSTITUIDO)


class MarcenariaOrcamento(Base):
    """Cabecalho do orcamento (uma linha por versao)."""
    __tablename__ = "marcenaria_orcamentos"
    __table_args__ = (
        # Dois computadores pedindo o mesmo numero: o segundo bate aqui e tenta
        # de novo com o numero seguinte (secao 7.1).
        UniqueConstraint("codigo", "versao", name="uq_marcenaria_orcamentos_codigo_versao"),
        Index("ix_marcenaria_orcamentos_status", "status"),
        Index("ix_marcenaria_orcamentos_cliente", "cliente_id"),
        Index("ix_marcenaria_orcamentos_validade", "data_validade"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)               # ORC-2026-000084
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default=StatusOrcamento.RASCUNHO)
    # Trava otimista (D20): toda escrita manda a revisao que tem; se nao bater,
    # outro computador mexeu antes. Cada escrita bem-sucedida soma 1.
    revisao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # A mesma `revisao` e a "coluna de versao" do SQLAlchemy: todo UPDATE (e
    # DELETE) desta linha leva `WHERE revisao = <a que foi lida>`. Se outro
    # computador gravou no meio, nenhuma linha bate e o SQLAlchemy levanta
    # StaleDataError (a API responde 409). `version_id_generator=False`: quem
    # soma 1 e o servico, so nas edicoes (o vencimento automatico nao soma).
    __mapper_args__ = {"version_id_col": revisao, "version_id_generator": False}

    # --- Quem e o que --------------------------------------------------------
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)        # obrigatorio para enviar
    funcionario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("funcionarios.id"), nullable=True)  # vendedor
    # Projeto JA cadastrado do cliente (D6). Sem ele, so nome e endereco: o
    # objeto so nasce na aprovacao (Spec 08A), para nao sobrar objeto orfao.
    objeto_id: Mapped[Optional[int]] = mapped_column(ForeignKey("objetos_servico.id"), nullable=True)
    projeto_nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # obrigatorio para enviar
    endereco_obra: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    medicao_observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # D29 (ate 4000)

    # --- Parametros COPIADOS da configuracao na criacao (D4) ----------------
    # Mudar a configuracao depois nao muda este orcamento.
    markup_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    perda_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    custo_hora_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    rt_padrao_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)    # % do arquiteto escolhido sem % (Revisao 3)
    rt_modo: Mapped[str] = mapped_column(String(10), nullable=False)                 # MARGEM | PRECO
    validade_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Instalacao, desconto e sinal (D8, D9) -------------------------------
    instalacao_custo_centavos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # vazio = sem instalacao
    desconto_modo: Mapped[str] = mapped_column(String(10), nullable=False, default="PERCENTUAL")  # PERCENTUAL | VALOR
    desconto_valor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)               # bp ou centavos
    sinal_modo: Mapped[str] = mapped_column(String(10), nullable=False, default="PERCENTUAL")
    sinal_valor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    observacoes_proposta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # sai na proposta (Spec 07)

    # --- Datas do ciclo de vida ---------------------------------------------
    data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_validade: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_recusa: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    motivo_recusa: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    data_aprovacao: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)   # Spec 08A
    os_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ordens_servico.id"), nullable=True)  # Spec 08A

    # --- Resumo para a LISTA (D5): atualizado a cada escrita ------------------
    resumo_bruto_centavos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resumo_total_centavos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resumo_margem_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resumo_qtd_moveis: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=agora_utc)
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=agora_utc, onupdate=agora_utc,
    )

    # --- Relacionamentos ----------------------------------------------------
    # So de ida: os models de cliente, funcionario e objeto (em producao em
    # outros segmentos) nao foram tocados.
    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente")
    funcionario: Mapped[Optional["Funcionario"]] = relationship("Funcionario")
    objeto: Mapped[Optional["ObjetoServico"]] = relationship("ObjetoServico")

    # A arvore: apagar o orcamento apaga os ambientes (e, deles, moveis e insumos).
    ambientes: Mapped[List["MarcenariaAmbiente"]] = relationship(
        "MarcenariaAmbiente",
        back_populates="orcamento",
        cascade="all, delete-orphan",
        order_by="(MarcenariaAmbiente.ordem, MarcenariaAmbiente.id)",
    )
    # Os arquitetos (D7): N linhas; o motor recebe a SOMA dos percentuais.
    rts: Mapped[List["MarcenariaOrcamentoRT"]] = relationship(
        "MarcenariaOrcamentoRT",
        back_populates="orcamento",
        cascade="all, delete-orphan",
        order_by="MarcenariaOrcamentoRT.id",
    )

    def __repr__(self) -> str:
        return f"<MarcenariaOrcamento(id={self.id}, codigo={self.codigo!r}, versao={self.versao}, status={self.status!r})>"


class MarcenariaOrcamentoRT(Base):
    """Um arquiteto (fornecedor) e o percentual de RT dele neste orcamento (D7)."""
    __tablename__ = "marcenaria_orcamento_rt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orcamento_id: Mapped[int] = mapped_column(
        ForeignKey("marcenaria_orcamentos.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    rt_bp: Mapped[int] = mapped_column(Integer, nullable=False)    # 0 a 3000 (30%)

    orcamento: Mapped["MarcenariaOrcamento"] = relationship("MarcenariaOrcamento", back_populates="rts")
    fornecedor: Mapped["Fornecedor"] = relationship("Fornecedor")


class MarcenariaOrcamentoAnexo(Base):
    """Foto ou PDF da medicao (D27-D31).

    Pendurado no CODIGO, nao na versao (D30): todas as versoes veem os mesmos
    anexos, e a nova versao nao copia arquivo nenhum.
    """
    __tablename__ = "marcenaria_orcamento_anexos"
    __table_args__ = (
        Index("ix_marcenaria_orcamento_anexos_codigo", "codigo_orcamento"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_orcamento: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo: Mapped[str] = mapped_column(String(4), nullable=False)            # FOTO | PDF
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)  # nome que o usuario enviou
    url: Mapped[str] = mapped_column(String(500), nullable=False)           # caminho relativo no disco
    legenda: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)   # "Parede da pia"
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=agora_utc)
