# ---------------------------------------------------------------------------
# ARQUIVO: schemas/funcionario/__init__.py
# DESCRICAO: Gestao de equipe - schemas de funcionario, cargo e usuario.
#
# Ate 12/10/2026 eram tres arquivos soltos (schemas/funcionario.py, cargo.py e
# usuario.py) que se importavam em cadeia: funcionario -> usuario -> cargo. Por
# isso estao juntos: separados, nao dava para agrupar sem fechar import circular.
# Este __init__ reexporta tudo, na ordem das dependencias.
# ---------------------------------------------------------------------------

from app.schemas.funcionario.cargo import (
    ComissaoModo,
    CargoBase,
    CargoCreate,
    CargoRead,
    CargoUpdate,
)

from app.schemas.funcionario.usuario import (
    UsuarioBase,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdateMe,
    UsuarioAlterarSenha,
    UsuarioUpdate,
)

from app.schemas.funcionario.cadastro import (
    FuncionarioBase,
    FuncionarioCreate,
    FuncionarioRead,
    FuncionarioUpdate,
)

__all__ = [
    "ComissaoModo",
    "CargoBase",
    "CargoCreate",
    "CargoRead",
    "CargoUpdate",
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioRead",
    "UsuarioUpdateMe",
    "UsuarioAlterarSenha",
    "UsuarioUpdate",
    "FuncionarioBase",
    "FuncionarioCreate",
    "FuncionarioRead",
    "FuncionarioUpdate",
]
