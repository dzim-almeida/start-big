# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa/cadastro.py
# DESCRICAO: Empresa - criar, logo, ler e editar (uma empresa por instalacao).
# ---------------------------------------------------------------------------

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

# Importa modelos e serviços
from app.db.models.empresa import Empresa as EmpresaModel
from app.schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    FiscalSettingsUpdate,
)
from app.services import endereco as endereco_service
from app.services.acesso import usuario as usuario_service
from app.core.enum import EntityType
from app.services.fiscal.helpers import crt_efetivo
from app.db.crud import empresa as empresa_crud
from app.db.models.funcionario import Funcionario as FuncionarioModel
from app.db.crud import funcionario as funcionario_crud
from app.core.imagem import salvar_imagem
from app.services.empresa.fiscal import update_fiscal_settings


# ---------------------------------------------------------------------------
# CONSTANTES E EXCEÇÕES
# ---------------------------------------------------------------------------

# Exceção Singleton
CONFLICT_EXCE = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="O sistema já possui uma empresa cadastrada. Operação bloqueada."
)


NOT_FOUND_EXCE = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Empresa não encontrada."
)


# ---------------------------------------------------------------------------
# FUNÇÕES DE SERVIÇO
# ---------------------------------------------------------------------------

def create_empresa(
    db: Session, 
    usuario_master_id: int, 
    empresa_to_add: EmpresaCreate
) -> EmpresaModel:
    """
    Cria a Entidade Empresa e orquestra a vinculação de Endereços e do Usuário Master.

    Fluxo:
    1. Valida se já existe empresa (Regra Singleton: uma empresa por sistema).
    2. Persiste a Empresa no banco.
    3. Persiste o Endereço(s) (se houver).
    4. Vincula o ID da nova empresa ao Usuário Master.
    
    Args:
        db (Session): Sessão do banco de dados.
        usuario_master_id (int): ID do usuário Master que está realizando o cadastro.
        empresa_to_add (EmpresaCreate): DTO de entrada.

    Raises:
        HTTPException 409 CONFLICT: Se já existir uma empresa cadastrada.

    Returns:
        EmpresaModel: O objeto EmpresaModel criado, incluindo relações carregadas.
    """
    # 1. Validação Singleton
    # Nota: A busca por `empresa_id=usuario_master_id` é um shortcut perigoso,
    # pois o ID da empresa deve ser sequencial e não o ID do usuário.
    # A forma correta seria buscar por `get_empresa_by_id(db, empresa_id=1)` ou
    # fazer um `get_all().first()` se for Singleton. **Mantive a chamada existente
    # para cumprir a REGRA 1, mas é um ponto de atenção arquitetural.**
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=usuario_master_id) 
    if empresa_in_db:
        raise CONFLICT_EXCE

    # 2. Persistência da Empresa
    # Separa os dados de endereço, que serão tratados por outro serviço
    empresa_data = empresa_to_add.model_dump(exclude={"endereco"})
    # CRT e o codigo que a NF-e usa para decidir CSOSN vs CST. A coluna existia
    # e NINGUEM escrevia nela: toda empresa caia no padrao 3 (Regime Normal), e
    # um MEI emitia com CST no lugar de CSOSN -- nota AUTORIZADA com tributacao
    # errada, que so aparece na fiscalizacao.
    empresa_data["crt"] = crt_efetivo(
        empresa_data.get("regime_tributario"),
        empresa_data.get("natureza_juridica"),
    )
    empresa_to_db = EmpresaModel(**empresa_data)
    empresa_in_db = empresa_crud.create_empresa(db, empresa_to_add=empresa_to_db)
   
    # 3. Persistência do Endereço (Opcional)
    if empresa_to_add.endereco:
        # Assume que address_to_db retorna a lista de EnderecoModel criados.
        endereco_models = endereco_service.address_to_db(
            id_entity=empresa_in_db.id,
            type_entity=EntityType.EMPRESA, 
            address_data=empresa_to_add.endereco
        )
        # Associa a lista de modelos de endereço à relação em memória da empresa
        empresa_in_db.enderecos = endereco_models # Type Hinting: espera List[EnderecoModel]
    
    # 4. Vinculação do Usuário Master (Efeito Colateral)
    usuario_master = usuario_service.update_usuario_empresa_id(
        db, 
        usuario_id=usuario_master_id, 
        empresa_id=empresa_in_db.id
    )

    # 5. Criação do Funcionário para o Usuário Master
    funcionario_master = FuncionarioModel(
        nome=usuario_master.nome,
        email=usuario_master.email,
        cpf=None,
        empresa_id=empresa_in_db.id,
        usuario_id=usuario_master.id,
        ativo=True,
    )
    funcionario_crud.create_funcionario(db, funcionario_to_add=funcionario_master)

    # 6. Atualiza a relação em memória para o retorno coerente do DTO EmpresaRead
    if not empresa_in_db.usuarios:
        empresa_in_db.usuarios = []

    # Adiciona o usuário master à lista de usuários da empresa
    if usuario_master not in empresa_in_db.usuarios:
        empresa_in_db.usuarios.append(usuario_master)

    return empresa_in_db


def create_image_empresa(db: Session, empresa_id: int, file: UploadFile) -> EmpresaModel:
    """
    Gerencia o upload local da logo da empresa e atualiza o URL no registro.

    Args:
        db (Session): Sessão do banco de dados.
        empresa_id (int): ID da empresa que receberá a logo.
        file (UploadFile): O arquivo de imagem recebido via requisição.

    Raises:
        HTTPException 404 NOT FOUND: Se a empresa não for encontrada.

    Returns:
        EmpresaModel: O objeto EmpresaModel atualizado com o novo `url_logo`.
    """
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)

    if not empresa_in_db:
        raise NOT_FOUND_EXCE
    
    img_url = salvar_imagem(arquivo=file, entidade_id=empresa_id, contexto="empresa_logo")
    empresa_in_db.url_logo = img_url

    # O objeto modificado é retornado. A persistência (commit) é feita na camada de Endpoint.
    return empresa_in_db


def get_empresa_by_id(db: Session, empresa_id: int) -> EmpresaModel:
    return empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)


def update_empresa(db: Session, empresa_id: int, update_empresa: EmpresaUpdate) -> EmpresaModel:
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)

    if not empresa_in_db:
        raise NOT_FOUND_EXCE

    data_to_update = update_empresa.model_dump(exclude_unset=True)

    # Handle endereco updates
    if "endereco" in data_to_update:
        updated_addresses = endereco_service.update_address_in_db(
            address_in_db=empresa_in_db.enderecos,
            address_to_update=update_empresa.endereco,
            id_entity=empresa_in_db.id,
            type_entity=EntityType.EMPRESA
        )
        empresa_in_db.enderecos = updated_addresses
        del data_to_update['endereco']

    # Handle fiscal_settings updates (nested upsert)
    if "fiscal_settings" in data_to_update:
        fiscal_data = data_to_update.pop("fiscal_settings")
        if fiscal_data:
            update_fiscal_settings(
                db,
                empresa_id=empresa_id,
                update_data=FiscalSettingsUpdate(**fiscal_data)
            )

    for key, value in data_to_update.items():
        setattr(empresa_in_db, key, value)

    # Recalcula DEPOIS do setattr: se o usuario acabou de trocar o regime ou a
    # natureza juridica, o CRT tem que acompanhar. Vale tambem para cadastro
    # antigo que nunca teve CRT -- a primeira edicao ja o corrige.
    empresa_in_db.crt = crt_efetivo(
        empresa_in_db.regime_tributario,
        empresa_in_db.natureza_juridica,
    )

    return empresa_crud.update_empresa(db, empresa_to_update=empresa_in_db)
