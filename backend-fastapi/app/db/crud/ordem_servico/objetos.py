# ---------------------------------------------------------------------------
# ARQUIVO: db/crud/ordem_servico/objetos.py
# DESCRICAO: Ordem de servico (crud) - objeto/equipamento: OS do objeto,
#            revisao agendada, busca por identificador, ultima OS.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import Sequence
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.objeto_servico import ObjetoServico as OSEquipamentoModel
from app.db.models.cliente import Cliente as ClienteModel
from app.core.busca import filtro_busca


def get_ordens_by_objeto_id(db: Session, objeto_id: int) -> Sequence[OSModel]:
    """Retorna todas as OS de um objeto/veículo, da mais antiga para a mais recente."""
    stmt = (
        select(OSModel)
        .where(OSModel.objeto_id == objeto_id)
        .order_by(OSModel.data_criacao.asc())
    )
    return db.scalars(stmt).all()


def get_objetos_com_revisao_agendada(db: Session) -> Sequence[OSEquipamentoModel]:
    """Objetos ativos que têm alguma revisão agendada (por data e/ou KM)."""
    stmt = select(OSEquipamentoModel).where(
        OSEquipamentoModel.ativo == True,  # noqa: E712
        or_(
            OSEquipamentoModel.proxima_revisao_data.isnot(None),
            OSEquipamentoModel.proxima_revisao_km.isnot(None),
        ),
    )
    return db.scalars(stmt).all()


def get_objeto_ativo_by_cliente_e_serie(
    db: Session, cliente_id: int, numero_serie: str
) -> OSEquipamentoModel | None:
    """
    Objeto ativo do cliente com o mesmo identificador (placa/serial), se existir.
    Base do reuso: o mesmo bem físico é UM registro que acumula histórico entre OSs
    (KM, revisão), em vez de ser duplicado a cada nova OS. Match case-insensitive.
    """
    stmt = select(OSEquipamentoModel).where(
        OSEquipamentoModel.cliente_id == cliente_id,
        OSEquipamentoModel.ativo == True,  # noqa: E712
        func.lower(OSEquipamentoModel.numero_serie) == numero_serie.strip().lower(),
    )
    return db.scalars(stmt).first()


def _identificador_normalizado_sql(coluna):
    """Coluna comparavel a `normalizar_identificador`: sem espaco nem hifen, maiusculo.

    A placa e gravada como o usuario digitou ('ABC-1D23', 'abc 1d23'), entao a
    igualdade crua erra o alvo. Normalizar dos dois lados e o que faz 'abc-1d23'
    achar 'ABC1D23' ja cadastrado.
    """
    return func.upper(func.replace(func.replace(coluna, "-", ""), " ", ""))


def get_objetos_ativos_por_identificador(
    db: Session,
    identificador: str,
    cliente_id: int | None = None,
    excluir_cliente_id: int | None = None,
) -> Sequence[OSEquipamentoModel]:
    """
    Objetos ativos com o mesmo identificador (placa/serial), comparado de forma
    normalizada. Diferente de `get_objeto_ativo_by_cliente_e_serie`, esta NAO se
    limita a um cliente -- e o que permite avisar que a maquina ja esta cadastrada
    no nome de outra pessoa.

    cliente_id          → restringe a um cliente (checar se o dono atual ja o tem)
    excluir_cliente_id  → tudo MENOS esse cliente (achar os donos concorrentes)
    """
    alvo = func.upper(func.replace(func.replace(identificador.strip(), "-", ""), " ", ""))

    stmt = select(OSEquipamentoModel).where(
        OSEquipamentoModel.ativo == True,  # noqa: E712
        _identificador_normalizado_sql(OSEquipamentoModel.numero_serie) == alvo,
    )
    if cliente_id is not None:
        stmt = stmt.where(OSEquipamentoModel.cliente_id == cliente_id)
    if excluir_cliente_id is not None:
        stmt = stmt.where(OSEquipamentoModel.cliente_id != excluir_cliente_id)

    return db.scalars(stmt).all()


def buscar_objetos_por_identificador(
    db: Session,
    termo: str,
    limite: int = 20,
) -> Sequence[OSEquipamentoModel]:
    """
    Objetos ativos cujo identificador (placa / n de serie / codigo da arte)
    casa com o texto digitado -- de QUALQUER cliente.

    Diferente de `get_objetos_ativos_por_identificador`, que compara por
    igualdade normalizada para decidir dedup/aviso, aqui a comparacao e de
    BUSCA: passa pelo `filtro_busca`, entao "1d23" acha "ABC1D23" e
    "abc-1d23" acha "ABC1D23" (o ramo do termo colado cobre o hifen, que o
    motor trata como separador de palavras).

    Cliente inativo fica de fora: nao adianta oferecer no seletor da OS um
    dono que o sistema nao deixa mais selecionar.
    """
    filtro = filtro_busca(termo, (OSEquipamentoModel.numero_serie,))
    if filtro is None:
        return []

    stmt = (
        select(OSEquipamentoModel)
        .join(ClienteModel, ClienteModel.id == OSEquipamentoModel.cliente_id)
        .where(
            OSEquipamentoModel.ativo == True,  # noqa: E712
            ClienteModel.ativo == True,  # noqa: E712
            filtro,
        )
        .order_by(OSEquipamentoModel.data_atualizacao.desc())
        .limit(limite)
    )
    return db.scalars(stmt).all()


def get_ultima_os_do_objeto(db: Session, objeto_id: int) -> OSModel | None:
    """OS mais recente de um objeto — usada para datar o cadastro no aviso de
    duplicidade ('última OS em 12/03/2026')."""
    stmt = (
        select(OSModel)
        .where(OSModel.objeto_id == objeto_id)
        .order_by(OSModel.data_criacao.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()
