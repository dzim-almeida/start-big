# ---------------------------------------------------------------------------
# ARQUIVO: cliente.py (CRUD)
# DESCRIÇÃO: Este módulo contém as funções de CRUD (Create, Read, Update,
#            Delete) para interagir com os modelos de Cliente no banco de dados
#            (Repository Layer).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, or_, and_
from typing import Sequence, Callable, Optional # Adicionado Optional

from app.db.models.cliente import Cliente as ClienteModel, ClientePF as ClientePFModel, ClientePJ as ClientePJModel

# =========================
# Funções de Validação/Conflito
# =========================

def verify_client_conflict(
    db: Session,
    value: str,
    search_method: Callable[[Session, str], ClienteModel | None],
    search_name: str
) -> str | None: # Retorna a mensagem de erro (str) ou None
    """
    Verifica se o valor fornecido (ex: CPF, CNPJ, Email) já existe no BD e se está ativo.
    """
    if not value:
        return None

    client_in_db = search_method(db, value)
    
    if client_in_db:
        # Verifica o status de atividade (para retornar mensagem específica de reativação)
        # O modelo PF/PJ precisa herdar de ClienteModel para ter o atributo 'ativo'
        if not client_in_db.ativo: 
            return "disabled client"
    
        # Conflito: Registro ativo encontrado
        return f"{search_name} já cadastrado"

    return None

# =========================
# Funções de Leitura (Read)
# =========================

def get_all_clients(db: Session) -> Sequence[ClienteModel]:
    """
    Busca TODOS os clientes ativos cadastrados no banco de dados.
    """
    # Constrói a query: SELECT * FROM cliente WHERE ativo = True
    stmt = select(ClienteModel).where(ClienteModel.ativo == True)
    # Executa a query e retorna todos os resultados
    clients_in_db = db.scalars(stmt).all()
    return clients_in_db

def get_client_by_id(db: Session, client_id: int) -> ClienteModel | None:
    """
    Busca um cliente (base) pelo seu ID.
    """
    stmt = select(ClienteModel).where(ClienteModel.id == client_id)
    client_in_db = db.scalars(stmt).first()
    return  client_in_db

def get_client_by_email(db: Session, client_email: str) -> ClienteModel | None: # Corrigido: email é string
    """
    Busca um cliente (base) pelo seu email.
    """
    stmt = select(ClienteModel).where(ClienteModel.email == client_email)
    client_in_db = db.scalars(stmt).first()
    return  client_in_db

def get_client_by_cpf(db: Session, client_cpf: str) -> ClientePFModel | None:
    """
    Busca um Cliente Pessoa Física pelo seu CPF.
    """
    stmt = select(ClientePFModel).where(ClientePFModel.cpf == client_cpf)
    client_in_db = db.scalars(stmt).first()
    return client_in_db

def get_client_by_rg(db: Session, client_rg: str) -> ClientePFModel | None:
    """
    Busca um Cliente Pessoa Física pelo seu RG.
    """
    stmt = select(ClientePFModel).where(ClientePFModel.rg == client_rg)
    client_in_db = db.scalars(stmt).first()
    return client_in_db

def get_client_by_cnpj(db: Session, client_cnpj: str) -> ClientePJModel | None:
    """
    Busca um Cliente Pessoa Jurídica pelo seu CNPJ.
    """
    stmt = select(ClientePJModel).where(ClientePJModel.cnpj == client_cnpj)
    client_in_db = db.scalars(stmt).first()
    return client_in_db

def get_client_by_ie(db: Session, client_ie: str) -> ClientePJModel | None:
    """
    Busca um Cliente Pessoa Jurídica pelo seu IE.
    """
    stmt = select(ClientePJModel).where(ClientePJModel.ie == client_ie)
    client_in_db = db.scalars(stmt).first()
    return client_in_db

def get_client_by_search(db: Session, search: str) -> Sequence[ClienteModel]: # Corrigido: Retorna Sequence[ClienteModel]
    """
    Busca polimórfica por clientes (PF ou PJ) que correspondam ao termo.
    A busca considera nome/CPF (PF) e razão social/CNPJ/nome fantasia (PJ).
    """
    
    # Cria aliases explícitos para as tabelas filhas (padrão de herança)
    pf_alias = aliased(ClientePFModel)
    pj_alias = aliased(ClientePJModel)

    # Define as condições de busca (OR) em ambas as tabelas aliadas, usando ilike para case-insensitive
    conditions = or_(
        pf_alias.nome.ilike(f"{search}%"),
        pf_alias.cpf.startswith(search),
        pj_alias.razao_social.ilike(f"{search}%"),
        pj_alias.cnpj.startswith(search),
        pj_alias.nome_fantasia.ilike(f"{search}%"),
    )

    # Inicia a query a partir da classe base ClienteModel
    stmt = select(ClienteModel)
    
    # Adiciona os joins explícitos (necessário para herança de tabela única ou mista)
    stmt = stmt.outerjoin(pf_alias, ClienteModel.id == pf_alias.id)
    stmt = stmt.outerjoin(pj_alias, ClienteModel.id == pj_alias.id)
    
    # Aplica o filtro 'WHERE' com as condições (deve ser ativo E corresponder à busca)
    stmt = stmt.where(
        and_(
            ClienteModel.ativo == True,
            conditions
        )
    )
    
    # Executa a query e retorna a sequência de objetos ClienteModel (que podem ser PF ou PJ)
    result = db.scalars(stmt).all()

    return result


# =========================
# Funções de Criação (Create)
# =========================

def create_client_pf(db: Session, new_client: ClientePFModel) -> ClientePFModel:
    """
    Adiciona um novo cliente polimórfico (ClientePF) ao banco de dados,
    incluindo seus relacionamentos em cascata (Endereços).
    """
    # Adiciona o objeto principal e seus filhos (em cascata) à sessão
    db.add(new_client)
    # Envia as instruções SQL para o banco para gerar o ID
    db.flush()
    # Atualiza a instância 'new_client' com os dados do banco (incluindo o ID)
    db.refresh(new_client)
    return new_client

def create_client_pj(db: Session, new_client: ClientePJModel) -> ClientePJModel:
    """
    Adiciona um novo cliente polimórfico (ClientePJ) ao banco de dados.
    """
    # Adiciona o objeto principal e seus filhos (em cascata) à sessão
    db.add(new_client)
    # Envia as instruções SQL para o banco para gerar o ID
    db.flush()
    # Atualiza a instância 'new_client' com os dados do banco (incluindo o ID)
    db.refresh(new_client)
    return new_client

# =========================
# Função de Atualização (Update)
# =========================

def update_client_in_db(db: Session, update_client: ClienteModel) -> ClienteModel:
    """
    Persiste as alterações feitas em um objeto Cliente na sessão.
    O objeto deve ter sido modificado pela camada de serviço.
    """
    # Envia os UPDATEs para o DB (mas não comita)
    db.flush()
    # Atualiza o objeto Python com dados do DB
    db.refresh(update_client)
    return update_client

# =========================
# Funções de Status (Ativar/Desativar)
# =========================

def active_client_by_id(db: Session, active_client: ClienteModel) -> ClienteModel: # Corrigido retorno
    """
    Persiste o status de ativação (ativo=True) para o cliente na sessão.
    """
    # A modificação (active_client.ativo = True) é feita na camada de serviço.
    db.flush()
    db.refresh(active_client)
    return active_client

def disable_client_by_id(db: Session, disable_client: ClienteModel) -> ClienteModel: # Corrigido retorno
    """
    Persiste o status de desativação (ativo=False) para o cliente na sessão (Soft Delete).
    """
    # A modificação (disable_client.ativo = False) é feita na camada de serviço.
    db.flush()
    db.refresh(disable_client)
    return disable_client