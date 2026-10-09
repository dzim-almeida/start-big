"""marcenaria (Spec 06A): orcamento tecnico, arvore, anexos e historico

Revision ID: 683ff38df873
Revises: 608dc99a8616
Create Date: 2026-10-09 15:00:00.000000

CONTEXTO (backend-fastapi/docs/marcenaria/SPEC-06A-ORCAMENTO-BACKEND-MARCENARIA.md):
- `marcenaria_orcamentos`: cabecalho, uma linha por versao (codigo + versao unicos).
- `marcenaria_orcamento_rt`: os arquitetos de cada orcamento (D7).
- `marcenaria_ambientes` -> `marcenaria_moveis` -> `marcenaria_movel_insumos`: a arvore.
- `marcenaria_orcamento_anexos`: fotos e PDFs da medicao, pelo CODIGO (D30).
- `marcenaria_eventos`: historico da marcenaria (D25), so inclusao.

MIGRACAO DE DADOS: NENHUMA. Todas as tabelas sao novas e nascem vazias.

SEGURANCA:
- So CRIA as tabelas que faltam (PR8): o create_all() do startup costuma cria-las
  antes desta migracao rodar; nesse caso, a tabela e pulada.
- Nenhuma tabela existente e alterada (as `fabrica_*` aposentadas ficam como estao).
- As colunas estao escritas aqui (e nao lidas dos models) de proposito: a
  migracao e uma foto de HOJE; mudar um model amanha nao pode muda-la.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '683ff38df873'
down_revision: Union[str, Sequence[str], None] = '608dc99a8616'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Ordem de criacao: quem e referenciado vem antes de quem referencia.
TABELAS = (
    "marcenaria_orcamentos",
    "marcenaria_orcamento_rt",
    "marcenaria_ambientes",
    "marcenaria_moveis",
    "marcenaria_movel_insumos",
    "marcenaria_orcamento_anexos",
    "marcenaria_eventos",
)


def _criar_orcamentos() -> None:
    op.create_table(
        "marcenaria_orcamentos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("revisao", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=True),
        sa.Column("funcionario_id", sa.Integer(), sa.ForeignKey("funcionarios.id"), nullable=True),
        sa.Column("objeto_id", sa.Integer(), sa.ForeignKey("objetos_servico.id"), nullable=True),
        sa.Column("projeto_nome", sa.String(length=100), nullable=True),
        sa.Column("endereco_obra", sa.String(length=255), nullable=True),
        sa.Column("medicao_observacoes", sa.Text(), nullable=True),
        sa.Column("markup_bp", sa.Integer(), nullable=False),
        sa.Column("perda_bp", sa.Integer(), nullable=False),
        sa.Column("custo_hora_centavos", sa.Integer(), nullable=False),
        sa.Column("rt_padrao_bp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rt_modo", sa.String(length=10), nullable=False),
        sa.Column("validade_dias", sa.Integer(), nullable=False),
        sa.Column("prazo_entrega_dias", sa.Integer(), nullable=False),
        sa.Column("instalacao_custo_centavos", sa.Integer(), nullable=True),
        sa.Column("desconto_modo", sa.String(length=10), nullable=False, server_default="PERCENTUAL"),
        sa.Column("desconto_valor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sinal_modo", sa.String(length=10), nullable=False, server_default="PERCENTUAL"),
        sa.Column("sinal_valor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observacoes_proposta", sa.Text(), nullable=True),
        sa.Column("data_envio", sa.DateTime(), nullable=True),
        sa.Column("data_validade", sa.Date(), nullable=True),
        sa.Column("data_recusa", sa.DateTime(), nullable=True),
        sa.Column("motivo_recusa", sa.String(length=500), nullable=True),
        sa.Column("data_aprovacao", sa.DateTime(), nullable=True),
        sa.Column("os_id", sa.Integer(), sa.ForeignKey("ordens_servico.id"), nullable=True),
        sa.Column("resumo_bruto_centavos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resumo_total_centavos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resumo_margem_bp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resumo_qtd_moveis", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("codigo", "versao", name="uq_marcenaria_orcamentos_codigo_versao"),
    )
    op.create_index("ix_marcenaria_orcamentos_status", "marcenaria_orcamentos", ["status"])
    op.create_index("ix_marcenaria_orcamentos_cliente", "marcenaria_orcamentos", ["cliente_id"])
    op.create_index("ix_marcenaria_orcamentos_validade", "marcenaria_orcamentos", ["data_validade"])


def _criar_rt() -> None:
    op.create_table(
        "marcenaria_orcamento_rt",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("orcamento_id", sa.Integer(),
                  sa.ForeignKey("marcenaria_orcamentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), sa.ForeignKey("fornecedores.id"), nullable=False),
        sa.Column("rt_bp", sa.Integer(), nullable=False),
    )
    op.create_index("ix_marcenaria_orcamento_rt_orcamento_id", "marcenaria_orcamento_rt", ["orcamento_id"])


def _criar_ambientes() -> None:
    op.create_table(
        "marcenaria_ambientes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("orcamento_id", sa.Integer(),
                  sa.ForeignKey("marcenaria_orcamentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
    )
    op.create_index("ix_marcenaria_ambientes_orcamento", "marcenaria_ambientes", ["orcamento_id"])


def _criar_moveis() -> None:
    op.create_table(
        "marcenaria_moveis",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ambiente_id", sa.Integer(),
                  sa.ForeignKey("marcenaria_ambientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("largura_mm", sa.Integer(), nullable=True),
        sa.Column("altura_mm", sa.Integer(), nullable=True),
        sa.Column("profundidade_mm", sa.Integer(), nullable=True),
        sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tipo_producao", sa.String(length=12), nullable=False, server_default="INTERNA"),
        sa.Column("central_fornecedor_id", sa.Integer(), sa.ForeignKey("fornecedores.id"), nullable=True),
        sa.Column("terceirizado_centavos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mao_obra_modo", sa.String(length=8), nullable=False, server_default="NENHUMA"),
        sa.Column("mao_obra_centavos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mao_obra_horas_centesimos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aprovado", sa.Boolean(), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
    )
    op.create_index("ix_marcenaria_moveis_ambiente", "marcenaria_moveis", ["ambiente_id"])


def _criar_insumos() -> None:
    op.create_table(
        "marcenaria_movel_insumos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("movel_id", sa.Integer(),
                  sa.ForeignKey("marcenaria_moveis.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", sa.Integer(),
                  sa.ForeignKey("produtos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("codigo", sa.String(length=100), nullable=True),
        sa.Column("unidade", sa.String(length=10), nullable=True),
        sa.Column("quantidade_milesimos", sa.Integer(), nullable=False),
        sa.Column("custo_unit_centavos", sa.Integer(), nullable=False),
        sa.Column("custo_origem", sa.String(length=14), nullable=False),
        sa.Column("sofre_perda", sa.Boolean(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
    )
    op.create_index("ix_marcenaria_movel_insumos_movel", "marcenaria_movel_insumos", ["movel_id"])
    op.create_index("ix_marcenaria_movel_insumos_produto", "marcenaria_movel_insumos", ["produto_id"])


def _criar_anexos() -> None:
    op.create_table(
        "marcenaria_orcamento_anexos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("codigo_orcamento", sa.String(length=20), nullable=False),
        sa.Column("tipo", sa.String(length=4), nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("legenda", sa.String(length=120), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_marcenaria_orcamento_anexos_codigo", "marcenaria_orcamento_anexos", ["codigo_orcamento"])


def _criar_eventos() -> None:
    op.create_table(
        "marcenaria_eventos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("orcamento_id", sa.Integer(),
                  sa.ForeignKey("marcenaria_orcamentos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("os_id", sa.Integer(), sa.ForeignKey("ordens_servico.id"), nullable=True),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("descricao", sa.String(length=500), nullable=False),
        sa.Column("dados", sa.JSON(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("usuario_nome", sa.String(length=150), nullable=False),
        sa.Column("ocorrido_em", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_marcenaria_eventos_orcamento", "marcenaria_eventos", ["orcamento_id", "ocorrido_em"])
    op.create_index("ix_marcenaria_eventos_os", "marcenaria_eventos", ["os_id", "ocorrido_em"])


# Cada tabela com a funcao que a cria (mesma ordem de TABELAS).
_CRIADORES = {
    "marcenaria_orcamentos": _criar_orcamentos,
    "marcenaria_orcamento_rt": _criar_rt,
    "marcenaria_ambientes": _criar_ambientes,
    "marcenaria_moveis": _criar_moveis,
    "marcenaria_movel_insumos": _criar_insumos,
    "marcenaria_orcamento_anexos": _criar_anexos,
    "marcenaria_eventos": _criar_eventos,
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())                 # o que o banco tem AGORA
    for tabela in TABELAS:
        if insp.has_table(tabela):                   # create_all ja criou: pula
            continue
        _CRIADORES[tabela]()                         # cria com colunas e indices


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    # Ordem inversa: quem referencia sai antes de quem e referenciado. O
    # drop_table leva os indices junto.
    for tabela in reversed(TABELAS):
        if insp.has_table(tabela):                   # nao falha num banco sem a tabela
            op.drop_table(tabela)
