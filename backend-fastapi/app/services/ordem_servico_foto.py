# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico_foto.py
# DESCRICAO: Lógica de negócio para upload e remoção de fotos de OS.
#
# Estrutura de armazenamento:
#   static/uploads/ordens-servico/{os_id}/{uuid}.{ext}
#
# Os arquivos são nomeados com UUID para evitar conflitos.
# A URL salva no banco é o caminho relativo ao diretório raiz do servidor.
# Fotos são acessíveis via: GET /static/uploads/ordens-servico/{os_id}/{arquivo}
# ---------------------------------------------------------------------------

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models.ordem_servico_foto import OrdemServicoFoto as OSFotoModel
from app.db.crud import ordem_servico as os_crud
from app.schemas.ordem_servico import OSFotoRead
from app.core.imagem import salvar_imagem, deletar_imagem


# ---------------------------------------------------------------------------
# Exceções reutilizáveis
# ---------------------------------------------------------------------------

os_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ordem de Serviço não encontrada"
)

foto_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Foto não encontrada"
)

file_delete_error_exce = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Erro ao remover o arquivo da foto do disco"
)


# ---------------------------------------------------------------------------
# Funções de serviço
# ---------------------------------------------------------------------------

def upload_foto_os(db: Session, numero_os: str, image_file: UploadFile) -> OSFotoModel:
    """
    Faz o upload de uma foto de diagnóstico para uma OS.

    Salva o arquivo em disco e registra a referência no banco.
    Retorna o modelo da foto criada.
    """
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce

    foto_url = salvar_imagem(arquivo=image_file, entidade_id=os_in_db.id, contexto="os_foto")

    foto_to_db = OSFotoModel(
        ordem_servico_id=os_in_db.id,
        nome_arquivo=image_file.filename,
        url=foto_url,
    )

    return os_crud.create_os_foto(db, foto_to_add=foto_to_db)


def delete_foto_os(db: Session, numero_os: str, foto_id: int) -> None:
    """
    Remove uma foto de OS: deleta o arquivo físico e o registro no banco.

    Valida que a foto pertence à OS informada (segurança por ownership).
    Lança 404 se a OS ou a foto não existir e 500 se o arquivo não puder ser removido.
    """
    os_in_db = os_crud.get_ordem_servico_by_numero_os(db, numero_os=numero_os)
    if not os_in_db:
        raise os_not_found_exce

    foto_in_db = os_crud.get_os_foto_by_id(db, foto_id=foto_id)
    if not foto_in_db or foto_in_db.ordem_servico_id != os_in_db.id:
        raise foto_not_found_exce

    if not deletar_imagem(caminho_arquivo=foto_in_db.url):
        raise file_delete_error_exce

    os_crud.delete_os_foto(db, foto_to_delete=foto_in_db)
