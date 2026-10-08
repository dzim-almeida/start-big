"""concede a permissão de Etiquetas a quem já tinha Produtos

Revision ID: z9a0b1c2d3e4
Revises: y8z9a0b1c2d3
Create Date: 2026-09-27 15:00:00.000000

CONTEXTO (docs/etiquetas-plano.md):
Até aqui as etiquetas iam de carona na permissão de Produtos. Agora têm linha
própria na tela de Cargos (view_labels / manage_labels / delete_labels, e a
chave de módulo "etiqueta"). Sem esta migração, TODO cargo das lojas em
produção perderia o acesso às etiquetas no dia da atualização, até alguém
reconfigurar os cargos.

MIGRAÇÃO DE DADOS: cargo que tinha Produtos (a chave "produto" ou qualquer
view/manage/delete_products) ganha as três permissões de Etiquetas — é
exatamente o acesso que tinha antes. Daí em diante o dono restringe.

SEGURANÇA:
- Decide pela AUSÊNCIA da chave "etiqueta" no cargo: se ela existe (mesmo
  falsa), o cargo já foi configurado na tela nova e não é tocado. Rodar de
  novo não muda nada.
- Cargo com "all" (administrador) não precisa: "all" já libera tudo.
- Só altera o JSON `permissoes` da tabela `cargos`; nenhum schema muda.
"""
import json
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'z9a0b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = 'y8z9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CHAVES_PRODUTOS = ("produto", "view_products", "manage_products", "delete_products")
CHAVES_ETIQUETAS = ("etiqueta", "view_labels", "manage_labels", "delete_labels")


def conceder_etiquetas(permissoes: dict[str, Any]) -> dict[str, Any] | None:
    """As permissões com Etiquetas concedidas, ou None se não há o que mudar."""
    if "etiqueta" in permissoes or permissoes.get("all") is True:
        return None
    if not any(permissoes.get(chave) is True for chave in CHAVES_PRODUTOS):
        return None
    return {**permissoes, **{chave: True for chave in CHAVES_ETIQUETAS}}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("cargos"):
        return

    for cargo_id, bruto in bind.execute(sa.text("SELECT id, permissoes FROM cargos")).fetchall():
        permissoes = json.loads(bruto) if isinstance(bruto, str) else (bruto or {})
        novas = conceder_etiquetas(permissoes)
        if novas is None:
            continue
        bind.execute(
            sa.text("UPDATE cargos SET permissoes = :permissoes WHERE id = :id"),
            {"permissoes": json.dumps(novas), "id": cargo_id},
        )


def downgrade() -> None:
    # Não remove: depois do upgrade o dono pode ter ajustado as permissões na
    # tela, e não há como distinguir o que veio daqui do que ele marcou.
    pass
