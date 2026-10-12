# ---------------------------------------------------------------------------
# ARQUIVO: services/funcionario/acesso.py
# DESCRICAO: Funcionarios - conceder login (usuario) a quem ja e funcionario.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.funcionario import UsuarioCreate
from app.db.models.funcionario import Funcionario as FuncionarioModel
from app.db.crud import funcionario as funcionario_crud
from app.services.acesso import usuario as usuario_service
from app.services.funcionario.cadastro import not_found_exce


# ===========================================================================
# LÓGICA DE ACESSO (CONCEDER LOGIN DEPOIS)
# ===========================================================================

def conceder_acesso(db: Session, funcionario_id: int, usuario_to_add: UsuarioCreate) -> FuncionarioModel:
    """Dá login a um funcionário que foi cadastrado sem acesso ao sistema.

    Sem isto, "funcionário sem usuário" seria porta sem saída: o dia em que o
    entregador virar caixa, a ficha dele teria que ser apagada e refeita — e com
    ela iriam embora as vendas, a comissão e o histórico que apontam para o
    `funcionario_id`.

    Quem já tem login não passa por aqui: trocar credencial é outro assunto
    (mexe em senha e e-mail de quem está trabalhando), e deixar esta porta
    aceitar os dois casos faria uma sobrescrever a outra sem ninguém pedir.
    """
    funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=funcionario_id)
    if not funcionario_in_db:
        raise not_found_exce

    if funcionario_in_db.usuario_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este funcionário já tem acesso ao sistema."
        )

    # O cargo continua mandando no is_master, exatamente como no cadastro.
    is_master = bool(
        funcionario_in_db.cargo and funcionario_in_db.cargo.nome.lower() == "master"
    )

    usuario_in_db = usuario_service.create_usuario(
        db,
        usuario_to_add=usuario_to_add,
        empresa_id=funcionario_in_db.empresa_id,
        is_master=is_master,
    )

    funcionario_in_db.usuario_id = usuario_in_db.id
    return funcionario_crud.update_funcionario_in_db(db, funcionario_to_update=funcionario_in_db)
