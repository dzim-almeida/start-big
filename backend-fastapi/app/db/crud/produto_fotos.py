# ---------------------------------------------------------------------------
# ARQUIVO: app/repository/produto_fotos.py (Presumido)
# DESCRIÇÃO: Funções de Repositório para interagir diretamente com o banco de
#            dados (CRUD básico) para a tabela de Fotos de Produto.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.produto_fotos import ProdutoFoto as ProdutoFotoModel

# =========================
# Função: Buscar Registro de Foto por ID
# =========================
def get_product_image_by_id(db: Session, image_id: int) -> ProdutoFotoModel:
    """
    Busca um registro de metadados de foto no banco de dados pelo seu ID único.
    """
    # Cria a instrução SQL Alchemy 2.0 (SELECT * FROM produto_fotos WHERE id = :image_id)
    stmt = select(ProdutoFotoModel).where(ProdutoFotoModel.id == image_id)
    # Executa a instrução, retorna o primeiro resultado (ou None se não encontrado)
    image_in_db = db.scalars(stmt).first()
    return image_in_db

# =========================
# Função: Criar Registro de Foto
# =========================
def create_product_image(db: Session, image_to_add: ProdutoFotoModel) -> ProdutoFotoModel:
    """
    Adiciona um novo registro de metadados de foto ao banco de dados.
    Esta função apenas lida com a persistência do registro;
    o upload físico deve ser tratado na camada de Serviço.
    """
    db.add(image_to_add) # Adiciona a instância do modelo de foto à sessão do SQLAlchemy.
    db.flush()           # Executa a inserção para garantir que o ID primário seja gerado.
    db.refresh(image_to_add) # Recarrega a instância com os dados do DB (incluindo o ID).
    return image_to_add  # Retorna a instância persistida.

# =========================
# Função: Deletar Registro de Foto
# =========================
def delete_product_image(db: Session, image_to_delete: ProdutoFotoModel) -> None:
    """
    Remove um registro de metadados de foto do banco de dados.

    NOTA: O objeto `image_to_delete` deve ser uma instância válida
    do modelo SQLAlchemy que está anexada à sessão.
    A exclusão do arquivo físico associado deve ser tratada na camada de Serviço.
    """
    db.delete(image_to_delete) # Marca a instância para exclusão.
    db.flush()                 # Executa a operação de exclusão dentro da sessão (opcional, mas não prejudica).