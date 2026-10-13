# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/pagamentos.py
# DESCRICAO: Caixa - o que entra no caixa pelas vendas e OS, e o estorno da OS.
# ---------------------------------------------------------------------------

from typing import Optional
from sqlalchemy.orm import Session
from app.core.enum import (
    JurosResponsavel,
    MovimentacaoFinanceiraOrigem,
    MovimentacaoFinanceiraTipo,
)
from app.db.crud import sessao_caixa as caixa_crud


# ===========================================================================
# INTEGRAÇÃO COM A VENDA
# ===========================================================================

def valor_que_entra(pagamento) -> int:
    """Do valor cobrado do cliente, quanto de fato chega na loja.

    O juros de parcelamento REPASSADO (`juros_responsavel == CLIENTE`) esta
    embutido em `pagamento.valor`, mas quem fica com ele e a operadora. Nas
    palavras do dono: "vendo 1.000, o juros da 150, o cliente paga 1.150 e so
    cai 1.000 na minha conta, pois a empresa do cartao ja desconta o dela".
    Lancar 1.150 no livro fazia o Extrato e o "Entrou de fato" mostrarem
    dinheiro que a conta bancaria nunca viu.

    Com `LOJA` o valor ja vem sem o juros (a loja absorveu, o cliente pagou o
    preco combinado) e nao ha nada a descontar -- por isso o filtro e pelo
    responsavel, e nao por `juros_valor > 0`.

    NAO ENCOSTA NA QUEBRA DE CAIXA: ela soma apenas as formas em especie
    (`somar_dinheiro_em_especie`), e juros de parcelamento so existe em cartao.
    O que muda no fechamento e a linha "por forma", que passa a mostrar o
    liquido -- decisao do dono em 05/09/2026, por coerencia com o resto da tela.

    A REGRA JA EXISTIA no sistema, so nao aqui: `juros_destino == OPERADORA` no
    recebimento em atraso ja fazia o caixa receber `valor_recebido - juros`
    (services/financeiro_receber.py). Isto e a mesma regra no fechamento.
    """
    valor = pagamento.valor or 0
    if getattr(pagamento, "juros_responsavel", None) == JurosResponsavel.CLIENTE.value:
        valor -= pagamento.juros_valor or 0
    # Piso em zero: um juros maior que o proprio valor so sairia de dado
    # corrompido, mas um movimento negativo viraria "saida" na leitura do
    # Extrato e sujaria o saldo em vez de acusar o problema.
    return max(0, valor)


def registrar_pagamentos_de_venda(
    db: Session,
    venda,
    operador_funcionario_id: Optional[int] = None,
) -> None:
    """Lança no livro os pagamentos de uma venda finalizada.

    LANÇA SEMPRE, com o controle de caixa ligado ou desligado. Era o contrário
    até 29/08/2026, e a razão de mudar veio do uso: loja que trabalha sem
    gaveta -- e é como boa parte trabalha -- ficava com o Extrato sem nenhuma
    venda, como se o dinheiro nunca tivesse entrado. "Não uso caixa" nunca quis
    dizer "não quero registro do meu dinheiro".

    O que MUDA sem turno é só o `sessao_caixa_id`, que fica nulo. Todo leitor do
    fechamento filtra por turno, então nada disso encosta na quebra de caixa das
    lojas que usam gaveta.

    QUEM RECEBE ≠ QUEM VENDE. `operador_funcionario_id` é quem está no caixa
    finalizando; `venda.funcionario_id` é o VENDEDOR, que existe para a comissão.
    Numa loja onde um atende e outro recebe, o dinheiro tem que cair no turno de
    quem recebeu — senão some do fechamento de quem está com a gaveta na mão.
    O vendedor fica como reserva para a loja de uma pessoa só, em que os dois
    são a mesma.

    SÓ ENTRA O QUE FOI RECEBIDO. Pagamento com vencimento no futuro (boleto,
    prazo, fiado) é promessa, não dinheiro: vira conta a receber e o movimento
    nasce no dia em que for pago de fato. Sem essa regra, o fechamento acusaria
    sobra em toda venda a prazo.
    """
    funcionario = getattr(venda, "funcionario", None)
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return

    # SESSÃO É OPCIONAL. Sem turno aberto -- ou com o controle de caixa
    # desligado, que é como boa parte das lojas trabalha -- o movimento nasce
    # com `sessao_caixa_id` NULO: o dinheiro entrou, mas não pela gaveta.
    #
    # Todo leitor do fechamento filtra por `sessao_caixa_id == <turno>` (ver
    # crud/sessao_caixa.py), então linha nula não entra em turno nenhum e a
    # quebra de caixa continua idêntica. Quem lê estas linhas é o Extrato.
    sessao = None
    if operador_funcionario_id:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, operador_funcionario_id)
    if not sessao:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, venda.funcionario_id)

    from app.core.tempo import hoje_local

    hoje = hoje_local()
    if sessao:
        venda.sessao_caixa_id = sessao.id

    conta_id = _conta_do_dinheiro(db, empresa_id)

    for pagamento in venda.pagamentos:
        if pagamento.vencimento and pagamento.vencimento > hoje:
            continue  # promessa: é conta a receber, não gaveta
        if sessao:
            pagamento.sessao_caixa_id = sessao.id
        caixa_crud.registrar_movimento(
            db,
            tipo=MovimentacaoFinanceiraTipo.ENTRADA,
            origem=MovimentacaoFinanceiraOrigem.VENDA,
            valor=valor_que_entra(pagamento),
            sessao_caixa_id=sessao.id if sessao else None,
            conta_bancaria_id=conta_id,
            forma_pagamento_id=pagamento.forma_pagamento_id,
            venda_pagamento_id=pagamento.id,
            funcionario_id=venda.funcionario_id,
            funcionario_nome=getattr(funcionario, "nome", None),
        )


def _conta_do_dinheiro(db: Session, empresa_id: int) -> Optional[int]:
    """Em que conta cai o dinheiro de uma venda ou OS.

    A principal da loja, sempre. NÃO se pergunta ao operador: no balcão, com o
    cliente esperando, ninguém escolhe conta bancária -- e uma pergunta a mais
    na finalização é a diferença entre o sistema ser usado e ser contornado.

    Se um dia a loja precisar separar "cartão cai no banco, dinheiro fica na
    gaveta", o lugar é aqui, olhando a forma de pagamento. Hoje seria adivinhar:
    `formas_pagamento` não guarda para onde o dinheiro daquela forma vai.

    SEMEIA A GAVETA se a loja não tiver conta nenhuma -- e ela não tem enquanto
    ninguém abrir o módulo Financeiro, porque a semeadura mora na listagem de
    contas. Sem isto, a loja que só vende (e nunca abriu o Financeiro) gravaria
    todas as vendas sem endereço, e o saldo do primeiro dia em que ela olhasse a
    tela nasceria sem elas.

    Import local para não amarrar o módulo do caixa ao do financeiro no topo:
    a dependência aqui é pontual, e o arquivo já usa esse recurso.
    """
    from app.services.financeiro.contas_bancarias import _conta_padrao_id

    return _conta_padrao_id(db, empresa_id)


def registrar_pagamentos_de_os(
    db: Session,
    ordem_servico,
    pagamentos,
    operador_funcionario_id: Optional[int] = None,
) -> None:
    """Lança no livro os pagamentos recebidos ao finalizar uma OS.

    GÊMEA de `registrar_pagamentos_de_venda`, e existe porque faltava: o
    fechamento de caixa SOMA a origem ORDEM_SERVICO (ver
    `crud/sessao_caixa.py`), mas nada nunca escreveu com ela. Havia leitor sem
    escritor -- e numa loja com o caixa ligado, receber uma OS em dinheiro
    enchia a gaveta sem o sistema saber, fazendo o turno fechar com SOBRA todo
    dia.

    `pagamentos` são os criados NESTA finalização, nunca `os.pagamentos`
    inteiro: uma OS reaberta e refinalizada carrega os pagamentos antigos junto,
    e relançá-los duplicaria dinheiro que já entrou.

    Mesma regra da venda, e pela mesma razão: lança SEMPRE, e sem turno aberto
    o movimento nasce com `sessao_caixa_id` nulo. A única guarda que sobrou é a
    da promessa -- pagamento com vencimento futuro é conta a receber, e o
    movimento nasce no dia em que o cliente pagar.

    O ADIANTAMENTO (`valor_entrada`) NÃO entra aqui, de propósito: ele é
    recebido quando a OS é ABERTA, e lançá-lo na finalização o jogaria no turno
    e no dia errados -- às vezes semanas depois. Fechar essa parte exige um
    gancho no momento da abertura, e é trabalho à parte.
    """
    if not pagamentos:
        return

    funcionario = getattr(ordem_servico, "funcionario", None)
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return

    # Sessão opcional, como na gêmea da venda: sem turno o movimento nasce com
    # `sessao_caixa_id` nulo e não entra em fechamento nenhum.
    sessao = None
    if operador_funcionario_id:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, operador_funcionario_id)
    if not sessao and ordem_servico.funcionario_id:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, ordem_servico.funcionario_id)

    from app.core.tempo import hoje_local

    hoje = hoje_local()
    conta_id = _conta_do_dinheiro(db, empresa_id)

    for pagamento in pagamentos:
        if pagamento.vencimento and pagamento.vencimento > hoje:
            continue  # promessa: é conta a receber, não gaveta
        if sessao:
            pagamento.sessao_caixa_id = sessao.id
        caixa_crud.registrar_movimento(
            db,
            tipo=MovimentacaoFinanceiraTipo.ENTRADA,
            origem=MovimentacaoFinanceiraOrigem.ORDEM_SERVICO,
            valor=valor_que_entra(pagamento),
            sessao_caixa_id=sessao.id if sessao else None,
            conta_bancaria_id=conta_id,
            forma_pagamento_id=pagamento.forma_pagamento_id,
            ordem_servico_pagamento_id=pagamento.id,
            funcionario_id=ordem_servico.funcionario_id,
            funcionario_nome=getattr(funcionario, "nome", None),
        )


def estornar_pagamentos_de_os(
    db: Session,
    ordem_servico,
    pagamentos,
    operador_funcionario_id: Optional[int] = None,
) -> None:
    """Devolve ao livro o dinheiro de uma OS reaberta SEM pagamento real.

    Reabrir com `cliente_pagou=False` significa que o pagamento nunca
    aconteceu, e a OS apaga os registros. Sem esta função, as linhas do livro
    ficariam para trás contando dinheiro que não entrou -- o turno passaria a
    fechar com FALTA, o espelho exato do defeito que esta onda veio corrigir.

    NÃO apaga nada: lança o movimento CONTRÁRIO, com a data de hoje. Mesma
    regra do estorno de conta a pagar, e pela mesma razão -- `sessao_caixa`
    persiste o saldo esperado, e mexer num turno fechado faria a quebra gravada
    discordar da recalculada.
    """
    if not pagamentos:
        return

    funcionario = getattr(ordem_servico, "funcionario", None)
    empresa_id = getattr(funcionario, "empresa_id", None)
    if not empresa_id:
        return

    sessao = None
    if operador_funcionario_id:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, operador_funcionario_id)
    if not sessao:
        sessao = caixa_crud.get_sessao_aberta_do_funcionario(db, ordem_servico.funcionario_id)

    for pagamento in pagamentos:
        # Só devolve o que chegou a entrar, e quem responde isso é o LIVRO.
        #
        # Antes a prova era `pagamento.sessao_caixa_id is None` -- "não passou
        # por turno, logo não virou movimento". Isso valia enquanto só existia
        # linha com turno. Agora que a venda e a OS lançam também sem caixa
        # aberto, essa pergunta responderia "não entrou" para dinheiro que
        # entrou, e o estorno deixaria a entrada sem a saída no extrato.
        if not caixa_crud.existe_movimento_do_pagamento(
            db, ordem_servico_pagamento_id=pagamento.id
        ):
            continue
        caixa_crud.registrar_movimento(
            db,
            tipo=MovimentacaoFinanceiraTipo.SAIDA,
            origem=MovimentacaoFinanceiraOrigem.ORDEM_SERVICO,
            valor=valor_que_entra(pagamento),
            sessao_caixa_id=sessao.id if sessao else None,
            # A MESMA conta em que a entrada caiu. Devolver noutro lugar deixaria
            # o saldo derivado com sobra numa conta e falta na outra.
            conta_bancaria_id=_conta_do_dinheiro(db, empresa_id),
            forma_pagamento_id=pagamento.forma_pagamento_id,
            funcionario_id=ordem_servico.funcionario_id,
            funcionario_nome=getattr(funcionario, "nome", None),
            motivo=f"Estorno: OS {ordem_servico.numero_os} reaberta sem pagamento",
        )
