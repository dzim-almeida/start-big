# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/criacao.py
# DESCRICAO: Ordem de servico - abertura (e o identificador gerado do objeto).
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.ordem_servico import (
    OrdemServicoCreate,
)
from app.db.models.ordem_servico import OrdemServico as OSModel
from app.db.models.objeto_servico import ObjetoServico as OSEquipamentoModel
from app.db.models.ordem_servico_item import OrdemServicoItem as OSItemModel
from app.db.crud import ordem_servico as os_crud
from app.db.crud import cliente as cliente_crud
from app.db.crud import funcionario as funcionario_crud
from app.services.segmentos import (
    validar_objeto_por_segmento,
    identificador_pesquisavel_atual,
    get_segmento_atual,
)
from app.core import segmentos as reg
from app.services.fabrica.modo import fase_inicial as fase_inicial_fabrica
from app.core.enum import (
    OrdemServicoItemTipo,
    OrdemServicoStatus,
)
from app.services.ordem_servico.excecoes import cliente_not_found_exce, funcionario_not_found_exce
from app.services.ordem_servico.regras import _assert_forma_pagamento_entrada, _item_conta_no_total
from app.services.ordem_servico.regras_tipo import _assert_tipo_pode_ser_criado


# ===========================================================================
# CRIAÇÃO (CREATE)
# ===========================================================================

def _preencher_identificador_gerado(
    db: Session,
    objeto_data: dict,
    numero_os: str,
    cliente,
) -> None:
    """Preenche, para segmentos que declaram identificador GERADO, o que o
    usuário não tem como saber.

    Muda `objeto_data` no lugar. É no-op para oficina e informática, que pedem
    o identificador ao usuário porque ele existe no mundo (placa, nº de série).

    Preenche também `marca`/`modelo` quando vierem vazios: são colunas NOT NULL
    herdadas do desenho de veículo/equipamento, e numa serigrafia a "marca" da
    arte, no caso comum, é o próprio cliente que está pedindo. Exigir que ele
    redigite o nome do cliente ali seria atrito sem informação nova.

    Isso só vale para segmento que DECLARA um campo na coluna `marca` (a
    serigrafia declara "Empresa / Marca da estampa"). Quem não declara — a
    marcenaria — não tem o que mostrar ali: `marca` fica vazia, e a via
    impressa (que só imprime a linha quando há valor) não diz "Marca: Dona
    Marta" num closet. A coluna é NOT NULL, e string vazia satisfaz.
    """
    segmento = get_segmento_atual(db)
    if not reg.identificador_e_gerado(segmento):
        return

    if not (objeto_data.get("numero_serie") or "").strip():
        objeto_data["numero_serie"] = reg.gerar_identificador(segmento, numero_os)

    if not (objeto_data.get("marca") or "").strip():
        if reg.segmento_declara_coluna(segmento, "marca"):
            objeto_data["marca"] = (getattr(cliente, "nome", None) or "").strip() or "—"
        else:
            objeto_data["marca"] = ""

    if not (objeto_data.get("modelo") or "").strip():
        objeto_data["modelo"] = objeto_data["numero_serie"]


def _exigir_campos_do_objeto(db: Session, objeto_data: dict) -> None:
    """Repõe, no serviço, as exigências que saíram do schema.

    `marca`, `modelo` e `numero_serie` viraram opcionais no schema para o
    segmento que gera o próprio identificador e preenche o resto. Sem esta
    guarda, informática e oficina — que contavam com o `Field(...)` obrigatório
    — passariam a aceitar OS sem esses dados, e o objeto do cliente ficaria
    inencontrável. São colunas NOT NULL, então o banco explodiria com um 500
    feio em vez de um 422 explicando o que falta.

    Esta função é o que protege os dois segmentos que já estão em produção.
    Coberta por test/api/v1/test_os_identificador_gerado.py.
    """
    segmento = get_segmento_atual(db)
    identificador = reg.get_identificador_segmento(segmento) or {}

    # `marca` só é exigida de quem a usa. Oficina e informática continuam
    # exigindo (não geram identificador, então nem passam pelo preenchimento);
    # segmento com identificador gerado e sem campo na coluna (marcenaria)
    # a recebe vazia de propósito — ver _preencher_o_que_o_usuario_nao_sabe.
    dispensa_marca = (
        reg.identificador_e_gerado(segmento)
        and not reg.segmento_declara_coluna(segmento, "marca")
    )

    faltando = [
        rotulo
        for campo, rotulo in (
            ("marca", "Marca"),
            ("modelo", "Modelo"),
            ("numero_serie", identificador.get("label") or "Número de série"),
        )
        if not (campo == "marca" and dispensa_marca)
        and not (objeto_data.get(campo) or "").strip()
    ]
    if not faltando:
        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=f"{', '.join(faltando)}: obrigatório para abrir uma OS.",
    )


def create_ordem_servico(
    db: Session,
    os_to_create: OrdemServicoCreate,
    *,
    origem_orcamento: bool = False,  # só a Spec 08A passa True; o endpoint nunca expõe (D7)
) -> OSModel:
    """
    Cria uma nova OS com equipamento e itens em uma única transação.

    Valida: cliente existe, funcionário existe (se informado), e se o tipo de
    trabalho pode nascer por aqui (Spec 03A).
    Gera: número sequencial, valor_bruto e valor_total.
    """
    # Primeira coisa: nada é gravado se a OS não puder nascer por este caminho.
    _assert_tipo_pode_ser_criado(db, os_to_create.dados_adicionais, origem_orcamento)

    cliente_in_db = cliente_crud.get_cliente_by_id(db, cliente_id=os_to_create.cliente_id)
    if not cliente_in_db:
        raise cliente_not_found_exce

    funcionario_in_db = None
    if os_to_create.funcionario_id:
        funcionario_in_db = funcionario_crud.get_funcionario_by_id(db, funcionario_id=os_to_create.funcionario_id)
        if not funcionario_in_db:
            raise funcionario_not_found_exce

    next_number = os_crud.get_next_numero(db)
    valor_bruto_os = 0
    itens_model = []

    for item in os_to_create.itens:
        valor_item = round(item.quantidade * item.valor_unitario)
        # Itens REPROVADO não entram no total (default APROVADO conta, como hoje).
        if _item_conta_no_total(item.status_aprovacao):
            valor_bruto_os += valor_item
        item_data = item.model_dump(exclude={"item_id"}, exclude_unset=True)
        itens_model.append(OSItemModel(
            **item_data,
            produto_id=item.item_id if item.item_id and item.tipo == OrdemServicoItemTipo.PRODUTO else None,
            servico_id=item.item_id if item.item_id and item.tipo == OrdemServicoItemTipo.SERVICO else None,
            valor_total=valor_item
        ))

    desconto = os_to_create.desconto or 0
    # Mesma fórmula de _recalcular_valor_total_os (inclui taxa de entrega e acréscimo),
    # para o total na criação bater com o total após qualquer recálculo posterior.
    valor_total_os = max(
        0,
        valor_bruto_os - desconto
        + (os_to_create.taxa_entrega or 0)
        + (os_to_create.acrescimo or 0),
    )

    # Suporta tanto 'objeto' quanto 'equipamento' (para retrocompatibilidade)
    objeto_schema = os_to_create.objeto or os_to_create.equipamento
    if not objeto_schema:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer os dados do objeto/equipamento de serviço."
        )

    objeto_data = objeto_schema.model_dump(exclude_unset=True)

    # Extrai campos legados do objeto/equipamento e move para dados_adicionais
    obj_dados_adicionais = objeto_data.get("dados_adicionais") or {}
    for legacy_field in ["tipo_equipamento", "imei"]:
        if legacy_field in objeto_data:
            val = objeto_data.pop(legacy_field)
            if val:
                obj_dados_adicionais[legacy_field] = val.value if hasattr(val, 'value') else val

    objeto_data["dados_adicionais"] = obj_dados_adicionais

    # --- Identificador gerado pelo sistema (ex: serigrafia) ---
    # Placa e numero de serie existem no mundo: estao escritos no bem, e o
    # atendente so copia. Codigo de arte nao existe ate alguem inventar -- e
    # campo obrigatorio que o usuario nao tem como preencher vira lixo ("1",
    # "teste"), que e como dois notebooks ja colapsaram num cadastro so.
    #
    # Aqui o codigo nasce do numero da OS, que ja e sequencial e unico: nao ha
    # contador novo para manter nem corrida entre terminais para tratar.
    _preencher_identificador_gerado(db, objeto_data, next_number, cliente_in_db)
    _exigir_campos_do_objeto(db, objeto_data)

    # Validacao especifica de segmento (ex: placa para oficina). Gated: e no-op
    # para segmentos sem regra dedicada, entao o fluxo de informatica permanece intacto.
    validar_objeto_por_segmento(
        db,
        numero_serie=objeto_data.get("numero_serie"),
        dados_adicionais=obj_dados_adicionais,
    )

    # Reutiliza o objeto existente do cliente (mesma placa/serial) em vez de duplicar:
    # um bem físico é UM registro que acumula histórico (KM, revisão) entre as OSs.
    # Se não existir, cria um novo. Agnóstico de segmento.
    #
    # Só vale como chave um identificador de verdade: `numero_serie` é obrigatório,
    # então quem não tem o dado digita "S/N" — e por igualdade crua dois bens
    # distintos do mesmo cliente colapsavam em UM registro, com o segundo
    # sobrescrevendo marca/modelo do primeiro. Ver identificador_pesquisavel().
    numero_serie = objeto_data.get("numero_serie")
    equipamento_existente = (
        os_crud.get_objeto_ativo_by_cliente_e_serie(db, cliente_in_db.id, numero_serie)
        if numero_serie and identificador_pesquisavel_atual(db, numero_serie) else None
    )
    if equipamento_existente:
        # Atualiza os detalhes informados, mas PRESERVA a próxima revisão já agendada.
        for campo in ("marca", "modelo", "cor"):
            valor = objeto_data.get(campo)
            if valor:
                setattr(equipamento_existente, campo, valor)
        novos_dados = objeto_data.get("dados_adicionais") or {}
        if novos_dados:
            equipamento_existente.dados_adicionais = {
                **(equipamento_existente.dados_adicionais or {}),
                **novos_dados,
            }
        equipamento_to_db = equipamento_existente
    else:
        equipamento_to_db = OSEquipamentoModel(**objeto_data, cliente=cliente_in_db)

    valor_entrada = os_to_create.valor_entrada or 0
    _assert_forma_pagamento_entrada(db, os_to_create.forma_pagamento_entrada_id)
    if os_to_create.usar_credito_cliente and valor_entrada > 0:
        if (cliente_in_db.saldo_credito or 0) < valor_entrada:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Saldo de crédito insuficiente para cobrir o valor de entrada informado"
            )
        cliente_in_db.saldo_credito = (cliente_in_db.saldo_credito or 0) - valor_entrada

    os_data = os_to_create.model_dump(
        exclude={"cliente_id", "itens", "objeto", "equipamento", "valor_bruto", "usar_credito_cliente"},
        exclude_unset=True
    )

    # Extrai campos legados da OS e move para dados_adicionais
    dados_adicionais = os_data.get("dados_adicionais") or {}
    for legacy_field in ["senha_aparelho", "acessorios", "condicoes_aparelho"]:
        if legacy_field in os_data:
            val = os_data.pop(legacy_field)
            if val:
                dados_adicionais[legacy_field] = val

    os_data["dados_adicionais"] = dados_adicionais

    os_to_db = OSModel(
        **os_data,
        # Marcenaria-fábrica: nulo em toda OS que não for Planejados com o
        # modo fábrica ligado (services/fabrica/modo.py).
        fase_fabrica=fase_inicial_fabrica(db, dados_adicionais),
        status=OrdemServicoStatus.ABERTA,
        valor_total=valor_total_os,
        valor_bruto=valor_bruto_os,
        numero_os=next_number,
        objeto=equipamento_to_db,
        itens=itens_model,
        funcionario=funcionario_in_db,
    )

    return os_crud.create_ordem_servico(db, os_to_add=os_to_db)
