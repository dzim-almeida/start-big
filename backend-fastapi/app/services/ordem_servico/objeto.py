# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/objeto.py
# DESCRICAO: Ordem de servico - historico de KM, revisoes pendentes e
#            identificador do objeto (verificar e buscar).
# ---------------------------------------------------------------------------

from datetime import datetime, date
from sqlalchemy.orm import Session
from app.db.crud import ordem_servico as os_crud
from app.services.sistema.segmentos import (
    get_segmento_atual,
)
from app.core import segmentos as reg
from app.core.busca import compactar
from app.core.enum import (
    OrdemServicoStatus,
)


# ===========================================================================
# HISTÓRICO DE KM (oficina)
# ===========================================================================

def get_historico_km(db: Session, objeto_id: int) -> list[dict]:
    """
    Histórico de quilometragem de um objeto/veículo ao longo das suas OS.

    Lê o KM de entrada gravado em dados_adicionais["km_entrada"] de cada OS,
    da mais antiga para a mais recente. Retorna apenas as OS que registraram KM.
    """
    ordens = os_crud.get_ordens_by_objeto_id(db, objeto_id)
    historico = []
    for o in ordens:
        km = (o.dados_adicionais or {}).get("km_entrada")
        if km is None:
            continue
        historico.append({
            "numero_os": o.numero_os,
            "data": o.data_criacao,
            "km_entrada": km,
        })
    return historico


def _ultimo_km_conhecido(db: Session, objeto_id: int) -> int | None:
    """Maior km_entrada registrado nas OS de um objeto (KM atual estimado)."""
    kms = [
        (o.dados_adicionais or {}).get("km_entrada")
        for o in os_crud.get_ordens_by_objeto_id(db, objeto_id)
    ]
    kms = [k for k in kms if isinstance(k, int)]
    return max(kms) if kms else None


def get_revisoes_pendentes(db: Session) -> list[dict]:
    """
    Veículos com revisão vencida — por data (proxima_revisao_data <= hoje) e/ou
    por KM (km atual >= proxima_revisao_km). Objetos sem revisão agendada (ex:
    informática) não aparecem, pois têm ambos os campos nulos.
    """
    hoje = date.today()
    pendentes = []
    for obj in os_crud.get_objetos_com_revisao_agendada(db):
        km_atual = _ultimo_km_conhecido(db, obj.id)
        venc_data = obj.proxima_revisao_data is not None and obj.proxima_revisao_data <= hoje
        venc_km = (
            obj.proxima_revisao_km is not None
            and km_atual is not None
            and km_atual >= obj.proxima_revisao_km
        )
        if not (venc_data or venc_km):
            continue
        cliente_nome, cliente_telefone = _cliente_contato(obj.cliente)
        # Já existe uma OS em aberto (não finalizada/cancelada) para este veículo?
        # Usado pela UI para bloquear "Nova OS" e avisar o usuário.
        tem_os_aberta = any(
            o.status not in (OrdemServicoStatus.FINALIZADA, OrdemServicoStatus.CANCELADA)
            for o in os_crud.get_ordens_by_objeto_id(db, obj.id)
        )
        pendentes.append({
            "objeto_id": obj.id,
            "cliente_id": obj.cliente_id,
            "cliente_nome": cliente_nome,
            "cliente_telefone": cliente_telefone,
            "tem_os_aberta": tem_os_aberta,
            "numero_serie": obj.numero_serie,
            "marca": obj.marca,
            "modelo": obj.modelo,
            "proxima_revisao_data": obj.proxima_revisao_data,
            "proxima_revisao_km": obj.proxima_revisao_km,
            "km_atual": km_atual,
            "motivo": "data" if venc_data else "km",
            # Quando este veiculo mexeu pela ultima vez (o agendamento da revisao
            # grava aqui). E o que permite a UI mostrar a revisao mais recente no
            # topo: sem isto a lista saia na ordem do banco, e um veiculo que
            # acabou de entrar aparecia embaixo de um de semanas atras.
            "atualizado_em": obj.data_atualizacao,
        })
    # Mais recente primeiro. `datetime.min` no lugar de None manda o objeto sem
    # data para o fim SEM comparar None com None, que levanta TypeError no
    # sort e derrubaria a tela inteira de revisoes.
    pendentes.sort(key=lambda p: p["atualizado_em"] or datetime.min, reverse=True)
    return pendentes


def _cliente_contato(cliente) -> tuple[str | None, str | None]:
    """Nome de exibição e telefone do cliente (PF usa nome, PJ usa razão social)."""
    if cliente is None:
        return None, None
    nome = (
        getattr(cliente, "nome", None)
        or getattr(cliente, "razao_social", None)
        or getattr(cliente, "nome_fantasia", None)
    )
    telefone = getattr(cliente, "celular", None) or getattr(cliente, "telefone", None)
    return (nome.strip() if isinstance(nome, str) else nome), telefone


def verificar_identificador_objeto(
    db: Session,
    identificador: str,
    cliente_id: int | None = None,
) -> dict:
    """
    Responde se a placa/serial digitada já pertence a algum objeto cadastrado —
    inclusive de OUTRO cliente, que é o caso que o reuso comum nunca enxergou
    (`get_objeto_ativo_by_cliente_e_serie` é escopado ao dono).

    É um AVISO, nunca um bloqueio: a máquina pode ter sido vendida, e o atendente
    decide se abre a OS com o dono antigo ou segue com o novo.

    Duas regras de silêncio, para o aviso não virar ruído:
      - identificador não pesquisável ("S/N", "não sei") não bate com nada;
      - se o cliente atual JÁ tem um objeto com esse identificador, é o cliente
        voltando com o mesmo bem — reuso normal, nada a avisar. É isso que faz o
        aviso aparecer só na primeira OS depois da troca de dono, sem precisar
        guardar "já avisei" em lugar nenhum.
    """
    segmento = get_segmento_atual(db)
    pesquisavel = reg.identificador_pesquisavel(identificador, segmento)

    resultado: dict = {
        "identificador": identificador,
        "pesquisavel": pesquisavel,
        "conflitos": [],
    }

    if not pesquisavel:
        return resultado

    if cliente_id is not None and os_crud.get_objetos_ativos_por_identificador(
        db, identificador, cliente_id=cliente_id
    ):
        return resultado

    for objeto in os_crud.get_objetos_ativos_por_identificador(
        db, identificador, excluir_cliente_id=cliente_id
    ):
        nome_cliente, _ = _cliente_contato(objeto.cliente)
        ultima_os = os_crud.get_ultima_os_do_objeto(db, objeto.id)
        resultado["conflitos"].append({
            "objeto_id": objeto.id,
            "cliente_id": objeto.cliente_id,
            "cliente_nome": nome_cliente,
            "marca": objeto.marca,
            "modelo": objeto.modelo,
            "numero_serie": objeto.numero_serie,
            "ultima_os_numero": ultima_os.numero_os if ultima_os else None,
            "ultima_os_data": ultima_os.data_criacao if ultima_os else None,
        })

    return resultado


# Teto da lista devolvida ao seletor da OS. Busca por identificador que devolve
# vinte linhas ja errou o alvo -- quem digita placa quer UM bem.
BUSCA_OBJETO_LIMITE = 20


# Piso de caracteres para BUSCAR -- proposital que seja MENOR que o
# `IDENTIFICADOR_MIN_CARACTERES` (4) do registry.
#
# Os dois pisos respondem perguntas diferentes. La: "este texto identifica um
# bem?", e errar custa dedup errado, entao 4 e sensato. Aqui: "vale ir ao banco
# procurar?", e errar custa uma consulta que nao acha nada. Com 4, digitar as
# tres primeiras letras da placa ("ABC") nao devolvia o carro -- que e
# exatamente como se comeca a digitar uma placa.
BUSCA_OBJETO_MIN_CARACTERES = 3


def buscar_objetos_por_identificador(
    db: Session,
    termo: str,
    limite: int = BUSCA_OBJETO_LIMITE,
) -> list[dict]:
    """
    Objetos cujo identificador casa com o texto digitado, com o nome do dono
    junto -- o que permite ao seletor da OS achar o cliente pela placa, pelo
    numero de serie ou pelo codigo da arte, e nao so por nome/CPF.

    NAO usa `identificador_pesquisavel` para aprovar o termo, e isso e
    deliberado: aquela funcao cobra o regex do segmento, que na oficina e a
    placa INTEIRA (`^...$`). Quem lembra so o final da placa e digita "1D23"
    seria recusado justamente no segmento que mais precisa desta busca. Ali o
    regex esta certo -- decide o que vale como CHAVE de dedup; aqui seria
    errado, porque busca boa aceita pedaco.

    Ficam os dois filtros que a busca de fato precisa:
      - minimo de caracteres (ver BUSCA_OBJETO_MIN_CARACTERES), para "ab" nao
        varrer a loja inteira;
      - identificador generico, para "S/N" nao devolver todo mundo que nao
        tinha o numero em maos (ver IDENTIFICADORES_GENERICOS no registry).
    """
    compacto = compactar(termo)

    if len(compacto) < BUSCA_OBJETO_MIN_CARACTERES:
        return []
    if compacto in reg.IDENTIFICADORES_GENERICOS:
        return []

    encontrados: list[dict] = []
    for objeto in os_crud.buscar_objetos_por_identificador(db, termo, limite):
        nome_cliente, _ = _cliente_contato(objeto.cliente)
        encontrados.append({
            "objeto_id": objeto.id,
            "cliente_id": objeto.cliente_id,
            # Sai em cinza embaixo do objeto na lista. E o que distingue duas
            # linhas iguais quando o bem foi VENDIDO e existe no nome de dois
            # clientes -- o mesmo caso que o aviso de duplicidade ja trata.
            "cliente_nome": nome_cliente,
            "tipo_equipamento": str(objeto.tipo_equipamento),
            "marca": objeto.marca,
            "modelo": objeto.modelo,
            "numero_serie": objeto.numero_serie,
            "cor": objeto.cor,
            # Vao para o formulario junto com o resto: e o que faz a OS abrir
            # com chassi/ano/IMEI ja preenchidos, sem passar pela tela de
            # "objeto ja cadastrado?".
            "dados_adicionais": objeto.dados_adicionais or {},
        })

    return encontrados
