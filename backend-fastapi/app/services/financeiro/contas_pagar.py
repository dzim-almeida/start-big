# ---------------------------------------------------------------------------
# ARQUIVO: services/financeiro/contas_pagar.py
# DESCRICAO: Financeiro - contas a pagar: leitura, criacao, edicao (com
#            auditoria e propagacao para as proximas parcelas), reativar e cancelar.
# ---------------------------------------------------------------------------

from datetime import date
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.enum import (
    ContaPagarStatus,
)
from app.core.tempo import hoje_local
from app.db.crud import financeiro as financeiro_crud
from app.db.models.conta_pagar import ContaPagar
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.schemas.financeiro import (
    ContaPagarCreate,
    ContaPagarUpdate,
)
from app.services.financeiro.comum import _funcionario_do_token, _somar_meses


ENTIDADE_CONTA_PAGAR = "CONTA_PAGAR"


# ===========================================================================
# CONTAS A PAGAR — leitura
# ===========================================================================

def _serializar_conta(conta: ContaPagar, hoje: date) -> Dict[str, Any]:
    """Monta o dicionário da tela, com os campos derivados de hoje.

    `vencida` e `dias_para_vencer` são calculados na leitura, nunca guardados:
    uma coluna "está vencida" precisaria de alguém rodando à meia-noite para
    acertá-la, e ficaria errada em toda máquina que passou a noite desligada --
    que é o caso de praticamente toda loja.
    """
    pendente = conta.status == ContaPagarStatus.PENDENTE.value
    dias = (conta.vencimento - hoje).days if pendente else None

    return {
        "id": conta.id,
        "descricao": conta.descricao,
        "valor": conta.valor,
        "vencimento": conta.vencimento,
        "status": conta.status,
        "plano_conta_id": conta.plano_conta_id,
        "plano_conta_nome": conta.plano_conta.nome if conta.plano_conta else None,
        "fornecedor_id": conta.fornecedor_id,
        "fornecedor_nome": getattr(conta.fornecedor, "nome", None),
        "valor_pago": conta.valor_pago,
        "pago_em": conta.pago_em,
        "conta_bancaria_id": conta.conta_bancaria_id,
        "conta_bancaria_nome": conta.conta_bancaria.nome if conta.conta_bancaria else None,
        "forma_pagamento_id": conta.forma_pagamento_id,
        "recorrente": conta.recorrente,
        "parcelamento_id": conta.parcelamento_id,
        "parcela_numero": conta.parcela_numero,
        "parcela_total": conta.parcela_total,
        "observacao": conta.observacao,
        "criado_em": conta.criado_em,
        "vencida": bool(pendente and conta.vencimento < hoje),
        "dias_para_vencer": dias,
    }


def listar_contas_pagar(
    db: Session,
    empresa_id: int,
    *,
    status: Optional[str] = None,
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    plano_conta_id: Optional[int] = None,
    fornecedor_id: Optional[int] = None,
    busca: Optional[str] = None,
    vencidas: bool = False,
    sem_categoria: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    hoje = hoje_local()

    # OS RECORTES DO PAINEL IGNORAM O MÊS, e essa é a parte que importa.
    #
    # `vencidas`: dívida vencida costuma ser de um mês que já passou.
    #
    # `sem_categoria`: a listagem filtra por VENCIMENTO, e o alerta nasce do que
    # foi PAGO no mês -- eixos diferentes. A Energia Solar paga em agosto vence
    # em setembro; com o recorte do mês, o atalho "Classificar" abriria uma
    # lista VAZIA. Um alerta que leva a lugar nenhum é pior que alerta nenhum.
    if vencidas or sem_categoria:
        inicio = fim = None

    itens, total_itens = financeiro_crud.listar_contas_pagar(
        db, empresa_id, status=status, inicio=inicio, fim=fim,
        plano_conta_id=plano_conta_id, fornecedor_id=fornecedor_id, busca=busca,
        vencidas=vencidas, sem_categoria=sem_categoria,
        limit=limit, offset=offset,
    )
    pendente, pago, vencido = financeiro_crud.totais_contas_pagar(
        db, empresa_id, hoje=hoje, inicio=inicio, fim=fim,
        plano_conta_id=plano_conta_id, fornecedor_id=fornecedor_id, busca=busca,
        vencidas=vencidas, sem_categoria=sem_categoria,
    )

    return {
        "itens": [_serializar_conta(c, hoje) for c in itens],
        "total_itens": total_itens,
        "total_pendente": pendente,
        "total_pago": pago,
        "total_vencido": vencido,
    }


def get_conta_pagar(db: Session, empresa_id: int, conta_id: int) -> Dict[str, Any]:
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    return _serializar_conta(conta, hoje_local())


def listar_historico_da_conta(db: Session, empresa_id: int, conta_id: int):
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    return financeiro_crud.listar_historico(
        db, empresa_id, ENTIDADE_CONTA_PAGAR, conta_id
    )


def _validar_referencias(
    db: Session, empresa_id: int, plano_conta_id: Optional[int]
) -> None:
    """Impede pendurar a conta numa categoria de OUTRA empresa.

    A FK do banco garante que o ID existe, não que ele é desta loja. Sem esta
    checagem, um ID chutado vazaria o nome da categoria alheia na listagem.
    """
    if plano_conta_id is not None:
        if not financeiro_crud.get_plano_conta(db, empresa_id, plano_conta_id):
            raise BadRequestException(detail="Categoria não encontrada")


def criar_conta_pagar(
    db: Session, empresa_id: int, dados: ContaPagarCreate, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Cria a conta — ou TODAS as parcelas, quando `parcelas > 1`.

    Parcelamento gera tudo de uma vez, e não uma parcela por baixa como faz a
    recorrência. O motivo é que as dez parcelas JÁ SÃO dívida hoje: se nascessem
    conforme o pagamento, o fluxo de caixa de dezembro ficaria cego para a
    parcela de dezembro e diria que sobra dinheiro já comprometido.

    É também o que os ERPs fazem — o Odoo gera "um item contábil para cada data
    de vencimento" no momento em que a fatura é lançada.

    Devolve a PRIMEIRA parcela: é ela que a tela acabou de criar do ponto de
    vista do usuário, e é o começo do grupo.
    """
    _validar_referencias(db, empresa_id, dados.plano_conta_id)
    func_id, func_nome = _funcionario_do_token(usuario_token)

    descricao = dados.descricao.strip()
    total = dados.parcelas
    parcelado = total > 1

    primeira: Optional[ContaPagar] = None

    for numero in range(1, total + 1):
        # Sempre a partir do vencimento ORIGINAL, nunca da parcela anterior:
        # ancorar é o que impede o dia encolhido de ficar encolhido.
        vencimento = _somar_meses(dados.vencimento, numero - 1)

        conta = financeiro_crud.criar_conta_pagar(
            db,
            ContaPagar(
                empresa_id=empresa_id,
                descricao=descricao,
                valor=dados.valor,
                vencimento=vencimento,
                plano_conta_id=dados.plano_conta_id,
                fornecedor_id=dados.fornecedor_id,
                recorrente=dados.recorrente,
                observacao=dados.observacao,
                status=ContaPagarStatus.PENDENTE.value,
                parcela_numero=numero if parcelado else None,
                parcela_total=total if parcelado else None,
                # A primeira parcela aponta para si mesma; as demais para ela.
                # É o que dispensa tabela-pai e sequência — o grupo é o id da
                # primeira linha, que o flush do CRUD já devolveu.
                parcelamento_id=(primeira.id if primeira else None) if parcelado else None,
            ),
        )

        if primeira is None:
            primeira = conta
            if parcelado:
                conta.parcelamento_id = conta.id
                db.flush()

        # Só a primeira entra na auditoria: dez linhas de "criação" para uma
        # única compra afogariam a trilha, e o grupo já diz que são a mesma.
        if numero == 1:
            financeiro_crud.registrar_historico(
                db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR,
                entidade_id=conta.id, campo="criacao", valor_antigo=None,
                valor_novo=f"{descricao} ({total}x)" if parcelado else descricao,
                funcionario_id=func_id, funcionario_nome=func_nome,
            )


    db.refresh(primeira)
    return _serializar_conta(primeira, hoje_local())


# Campos cuja alteração o histórico registra. Descrição e observação ficam de
# fora: corrigir uma vírgula na descrição não é fato financeiro, e encher a
# trilha de ruído faz ninguém ler a trilha.
CAMPOS_AUDITADOS = ("valor", "vencimento", "plano_conta_id", "fornecedor_id")


# O ÚNICO campo que ainda muda depois do pagamento: a categoria.
#
# Ela nunca entrou no livro do dinheiro, então corrigi-la não faz documento e
# lançamento discordarem -- e classificar despesa depois de paga é rotina em
# qualquer escritório de contabilidade.
#
# A lista é curta de propósito. Fornecedor e observação também não estão no
# livro e poderiam entrar aqui, mas nenhuma tela os edita hoje: backend que
# aceita mais do que a interface oferece é surpresa esperando para acontecer.
CAMPOS_LIVRES_APOS_PAGAMENTO = ("plano_conta_id",)


def atualizar_conta_pagar(
    db: Session,
    empresa_id: int,
    conta_id: int,
    dados: ContaPagarUpdate,
    usuario_token: Dict[str, Any],
) -> Dict[str, Any]:
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")

    # CONTA PAGA: o dinheiro está congelado, a CLASSIFICAÇÃO não.
    #
    # Valor e vencimento já viraram lançamento no livro, e mexer neles faria a
    # despesa do relatório discordar do movimento -- para isso, estorna-se
    # primeiro. Mas categoria, fornecedor e observação nunca entraram no livro:
    # são a leitura contábil do documento, e corrigi-las depois do pagamento é
    # rotina em qualquer escritório.
    #
    # A regra larga de antes criava um laço fechado com o painel de atenção: o
    # alerta "gastos sem categoria" conta despesa PAGA, e conta paga não podia
    # ser classificada. O aviso não teria como sair da tela nunca.
    if conta.status == ContaPagarStatus.PAGA.value:
        mexidos = set(dados.model_dump(exclude_unset=True))
        congelados = mexidos - set(CAMPOS_LIVRES_APOS_PAGAMENTO)
        if congelados:
            raise BadRequestException(
                detail=(
                    "Esta conta já foi paga: só a categoria ainda pode ser corrigida. "
                    "Para mudar valor ou vencimento, estorne o pagamento antes."
                )
            )

    _validar_referencias(db, empresa_id, dados.plano_conta_id)
    func_id, func_nome = _funcionario_do_token(usuario_token)

    alteracoes = dados.model_dump(exclude_unset=True)
    propagar = bool(alteracoes.pop("aplicar_nas_proximas", False))

    for campo, novo in alteracoes.items():
        antigo = getattr(conta, campo)
        if antigo == novo:
            continue

        if campo in CAMPOS_AUDITADOS:
            financeiro_crud.registrar_historico(
                db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR,
                entidade_id=conta.id, campo=campo,
                valor_antigo=str(antigo) if antigo is not None else None,
                valor_novo=str(novo) if novo is not None else None,
                funcionario_id=func_id, funcionario_nome=func_nome,
            )

        setattr(conta, campo, novo.strip() if isinstance(novo, str) else novo)

    if propagar:
        _propagar_nas_proximas_parcelas(
            db, empresa_id, conta, alteracoes, func_id, func_nome
        )

    db.flush()
    db.refresh(conta)
    return _serializar_conta(conta, hoje_local())


# Só estes se repetem. `descricao` fica de fora porque ela carrega o "9/72" da
# parcela; `recorrente` porque parcelado e recorrente se excluem (ver o modelo).
CAMPOS_PROPAGAVEIS = ("valor", "vencimento", "plano_conta_id", "fornecedor_id", "observacao")


def _propagar_nas_proximas_parcelas(
    db: Session,
    empresa_id: int,
    conta,
    alteracoes: Dict[str, Any],
    func_id: Optional[int],
    func_nome: Optional[str],
) -> int:
    """Repete a correção nas parcelas seguintes que ainda estão em aberto.

    Nasceu de um empréstimo em 30x cadastrado com a data errada: corrigir mês a
    mês são 30 telas, e em 72x ninguém corrige -- desiste do módulo.

    TRÊS RECORTES, e cada um evita um estrago:
      - só o MESMO parcelamento (nunca outra dívida do mesmo fornecedor);
      - só as parcelas DEPOIS desta (o passado não se reescreve);
      - só as PENDENTES -- parcela paga já virou lançamento no livro, e mexer
        nela faria o relatório do mês discordar do movimento.

    O VENCIMENTO RE-ANCORA em vez de copiar. Copiar a data faria as 63 parcelas
    restantes vencerem todas no mesmo dia; aqui cada uma recebe o mesmo DIA do
    novo vencimento, mês a mês, pela mesma `_somar_meses` que criou o
    parcelamento -- e por isso dia 30 continua encolhendo só em fevereiro e
    voltando para 30 em março.
    """
    if not conta.parcelamento_id or not conta.parcela_numero:
        return 0

    campos = {c: v for c, v in alteracoes.items() if c in CAMPOS_PROPAGAVEIS}
    if not campos:
        return 0

    seguintes = financeiro_crud.listar_parcelas_seguintes(
        db, empresa_id, conta.parcelamento_id, conta.parcela_numero
    )

    for parcela in seguintes:
        for campo, novo in campos.items():
            if campo == "vencimento":
                novo = _somar_meses(
                    conta.vencimento, (parcela.parcela_numero or 0) - conta.parcela_numero
                )
            antigo = getattr(parcela, campo)
            if antigo == novo:
                continue
            if campo in CAMPOS_AUDITADOS:
                financeiro_crud.registrar_historico(
                    db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR,
                    entidade_id=parcela.id, campo=campo,
                    valor_antigo=str(antigo) if antigo is not None else None,
                    valor_novo=str(novo) if novo is not None else None,
                    funcionario_id=func_id, funcionario_nome=func_nome,
                )
            setattr(parcela, campo, novo.strip() if isinstance(novo, str) else novo)

    db.flush()
    return len(seguintes)


def reativar_conta_pagar(
    db: Session, empresa_id: int, conta_id: int, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Desfaz um cancelamento -- CANCELADA volta para PENDENTE.

    Faltava, e o buraco aparecia na primeira vez que alguém errava o clique: o
    cancelamento era porta de mão única, e a conta ficava para sempre fora da
    lista de "em aberto" sem forma de voltar. Numa parcela de um empréstimo em
    72x isso significava perder a linha 9/72 do controle inteiro.

    NÃO cancela recorrência nem recria nada: a conta é a mesma linha, com o
    mesmo id, vencimento e valor. Só o status volta.

    O rastro fica: cancelar gravou uma linha no histórico e reativar grava
    outra. "Cancelaram e voltaram atrás" continua sendo uma pergunta que o
    módulo responde.
    """
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status != ContaPagarStatus.CANCELADA.value:
        raise BadRequestException(
            detail="Só uma conta cancelada pode ser reativada."
        )

    func_id, func_nome = _funcionario_do_token(usuario_token)
    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR, entidade_id=conta.id,
        campo="status", valor_antigo=ContaPagarStatus.CANCELADA.value,
        valor_novo=ContaPagarStatus.PENDENTE.value,
        funcionario_id=func_id, funcionario_nome=func_nome,
    )
    conta.status = ContaPagarStatus.PENDENTE.value
    db.flush()
    db.refresh(conta)
    return _serializar_conta(conta, hoje_local())


def cancelar_conta_pagar(
    db: Session, empresa_id: int, conta_id: int, usuario_token: Dict[str, Any]
) -> Dict[str, Any]:
    """Cancela em vez de excluir.

    Excluir apagaria o rastro de que a conta existiu, e "sumiu uma conta de
    R$ 3.000" é exatamente o tipo de pergunta que o módulo tem que responder.
    """
    conta = financeiro_crud.get_conta_pagar(db, empresa_id, conta_id)
    if not conta:
        raise NotFoundException(detail="Conta não encontrada")
    if conta.status == ContaPagarStatus.PAGA.value:
        raise BadRequestException(
            detail="Esta conta já foi paga. Estorne o pagamento antes de cancelá-la."
        )

    func_id, func_nome = _funcionario_do_token(usuario_token)
    financeiro_crud.registrar_historico(
        db, empresa_id=empresa_id, entidade=ENTIDADE_CONTA_PAGAR, entidade_id=conta.id,
        campo="status", valor_antigo=conta.status,
        valor_novo=ContaPagarStatus.CANCELADA.value,
        funcionario_id=func_id, funcionario_nome=func_nome,
    )
    conta.status = ContaPagarStatus.CANCELADA.value
    db.flush()
    db.refresh(conta)
    return _serializar_conta(conta, hoje_local())
