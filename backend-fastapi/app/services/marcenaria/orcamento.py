# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento.py
# DESCRICAO: Regras do orcamento de marcenaria: criar, cabecalho, arquitetos,
#            transicoes de status, versoes, exclusao, lista e historico
#            (Spec 06A, secoes 4.2, 6 e 7).
#
# A arvore (ambientes e moveis) fica em orcamento_arvore.py; os precos em
# orcamento_precos.py; os anexos em orcamento_anexos.py. Arquivos separados
# para nenhum passar do teto de bytecode do PyArmor (PR7).
# ---------------------------------------------------------------------------

from datetime import timedelta
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.regras_preco import reais
from app.core.tempo import agora_utc, hoje_local
from app.db.crud.marcenaria import evento as crud_evento
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.cliente import Cliente
from app.db.models.fornecedor import Fornecedor
from app.db.models.funcionario import Funcionario
from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel, MarcenariaMovelInsumo
from app.db.models.marcenaria.orcamento import (
    MarcenariaOrcamento,
    MarcenariaOrcamentoRT,
    StatusOrcamento,
)
from app.db.models.objeto_servico import ObjetoServico
from app.schemas.marcenaria.orcamento import (
    ArquitetosEntrada,
    AtualizarPrecosEntrada,
    OrcamentoAtualizar,
    OrcamentoCriar,
)
from app.services import configuracao_marcenaria as configuracao_service
from app.services.marcenaria import erros
from app.services.marcenaria import orcamento_precos as precos
from app.services.marcenaria.aprovacao_bloqueios import motivos_que_impedem_desfazer, os_cancelada
from app.services.marcenaria.calculo import calcular_orcamento
from app.services.marcenaria.orcamento_anexos import apagar_anexos_do_codigo
from app.services.marcenaria.orcamento_calculo import (
    calcular,
    calcular_orcamento_do_banco,
    montar_entrada_motor,
)
from app.services.marcenaria.orcamento_comum import (
    carregar,
    carregar_para_editar,
    conferir_revisao,
    exigir_custos,
    exigir_orcamento_tecnico,
    fechar_escrita,
    marcar_vencidos,
    registrar_evento,
)
from app.services.marcenaria.orcamento_detalhe import (
    montar_detalhe,
    montar_item_lista,
    montar_versao,
)
from app.services.marcenaria.permissoes import pode_ver_custos_marcenaria

# Campos do PATCH que sao CUSTO (D23/D24): escrever exige view_custos.
CAMPOS_DE_CUSTO = (
    "markup_bp", "perda_bp", "custo_hora_centavos", "rt_padrao_bp", "rt_modo",
    "instalacao_custo_centavos",
)


# ===========================================================================
# RESPOSTA PADRAO (D21: toda escrita devolve o detalhe completo)
# ===========================================================================

def detalhe(db: Session, orcamento_id: int, usuario_token: dict) -> dict:
    """O detalhe com o calculo do motor (secao 6.2), recortado pela permissao."""
    orc = carregar(db, orcamento_id)
    resultado = calcular_orcamento_do_banco(orc)          # D5: sempre recalcula
    resultado_aprovado, pode_desfazer = None, False
    if orc.status == StatusOrcamento.APROVADO:            # Spec 08A: o que virou OS
        try:
            resultado_aprovado = calcular_orcamento(montar_entrada_motor(orc, so_aprovados=True))
        except ValueError:
            resultado_aprovado = None                     # nunca deve acontecer: aprovou porque fechava
        pode_desfazer = not motivos_que_impedem_desfazer(db, orc)
    return montar_detalhe(
        orc, resultado, usuario_token, pode_ver_custos_marcenaria(usuario_token),
        resultado_aprovado=resultado_aprovado, pode_desfazer=pode_desfazer,
    )


# ===========================================================================
# CRIAR (secao 7.1)
# ===========================================================================

def proximo_codigo(db: Session) -> str:
    """ORC-AAAA-NNNNNN: o proximo da sequencia do ano (como o numero da OS)."""
    prefixo = f"ORC-{hoje_local().year}-"
    ultimo = crud.ultimo_codigo_com_prefixo(db, prefixo)
    sequencia = int(ultimo.replace(prefixo, "")) + 1 if ultimo else 1
    return f"{prefixo}{sequencia:06d}"


def _cliente_valido(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None or not cliente.ativo:
        erros.invalido("Cliente não encontrado.")
    return cliente


def _vendedor_valido(db: Session, funcionario_id: int) -> Funcionario:
    funcionario = db.get(Funcionario, funcionario_id)
    if funcionario is None:
        erros.invalido("Vendedor não encontrado.")
    return funcionario


def _projeto_do_cliente(db: Session, objeto_id: int, cliente_id: Optional[int]) -> ObjetoServico:
    """O projeto (objeto) escolhido tem de ser ativo e DESTE cliente (D6)."""
    objeto = db.get(ObjetoServico, objeto_id)
    if objeto is None or not objeto.ativo or objeto.cliente_id != cliente_id:
        erros.invalido("Projeto não encontrado para este cliente.")
    return objeto


def _endereco_do_objeto(objeto: ObjetoServico) -> Optional[str]:
    """O endereco da obra gravado no projeto (campo dinamico da marcenaria)."""
    return (objeto.dados_adicionais or {}).get("endereco_obra") or None


def criar_orcamento(db: Session, dados: OrcamentoCriar, usuario_token: dict) -> int:
    """Cria em RASCUNHO, com os parametros COPIADOS da configuracao (D4).

    Dois computadores podem pedir o mesmo numero ao mesmo tempo: o segundo
    bate no unico (codigo, versao) e tenta de novo com o seguinte (7.1).
    Devolve o id do orcamento novo.
    """
    exigir_orcamento_tecnico(db)
    config = configuracao_service.obter_configuracao(db, int(usuario_token.get("empresa_id")))

    # Referencias conferidas antes (erro claro em vez de chave estrangeira quebrada).
    if dados.cliente_id is not None:
        _cliente_valido(db, dados.cliente_id)
    if dados.objeto_id is not None:
        objeto = _projeto_do_cliente(db, dados.objeto_id, dados.cliente_id)
    else:
        objeto = None
    # Vendedor: o informado; sem ele, o funcionario do usuario logado (Revisao 1).
    funcionario_id = dados.funcionario_id or usuario_token.get("funcionario_id")
    if dados.funcionario_id is not None:
        _vendedor_valido(db, dados.funcionario_id)
    elif funcionario_id is not None and db.get(Funcionario, funcionario_id) is None:
        funcionario_id = None                                # token antigo: sem vendedor

    for tentativa in (1, 2):
        try:
            orc = MarcenariaOrcamento(
                codigo=proximo_codigo(db),
                versao=1,
                status=StatusOrcamento.RASCUNHO,
                revisao=1,
                cliente_id=dados.cliente_id,
                funcionario_id=funcionario_id,
                objeto_id=dados.objeto_id,
                projeto_nome=dados.projeto_nome or (objeto.modelo if objeto else None),
                endereco_obra=dados.endereco_obra or (_endereco_do_objeto(objeto) if objeto else None),
                # --- copia dos parametros (D4) ---
                markup_bp=config.markup_padrao_bp,
                perda_bp=config.perda_padrao_bp,
                custo_hora_centavos=config.custo_hora_centavos,
                rt_padrao_bp=config.rt_padrao_bp,
                rt_modo=config.rt_modo,
                validade_dias=config.validade_dias,
                prazo_entrega_dias=config.prazo_entrega_dias,
            )
            db.add(orc)
            db.flush()                                        # aqui o unico pode bater
            registrar_evento(db, orc, "ORCAMENTO_CRIADO", "Orçamento criado.", usuario_token,
                             {"codigo": orc.codigo})
            db.commit()
            return orc.id
        except IntegrityError:
            db.rollback()                                     # desfaz e tenta o proximo numero
            if tentativa == 2:
                raise
    raise RuntimeError("inalcancavel")                        # o laco sempre retorna ou levanta


# ===========================================================================
# CABECALHO (PATCH) E ARQUITETOS (PUT /rt)
# ===========================================================================

def atualizar_cabecalho(
    db: Session, orcamento_id: int, revisao: int, dados: OrcamentoAtualizar, usuario_token: dict,
) -> None:
    """PATCH: so os campos enviados mudam. Campos de custo exigem view_custos (D24)."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    enviados = dados.model_dump(exclude_unset=True)            # o que veio no corpo

    if any(campo in enviados for campo in CAMPOS_DE_CUSTO):
        exigir_custos(usuario_token)

    # --- Cliente, vendedor e projeto ---
    if "cliente_id" in enviados:
        if dados.cliente_id is not None:
            _cliente_valido(db, dados.cliente_id)
        if dados.cliente_id != orc.cliente_id and "objeto_id" not in enviados:
            orc.objeto_id = None                              # o projeto era do cliente antigo
        orc.cliente_id = dados.cliente_id
    if "funcionario_id" in enviados:
        if dados.funcionario_id is not None:
            _vendedor_valido(db, dados.funcionario_id)
        orc.funcionario_id = dados.funcionario_id
    if "objeto_id" in enviados:
        if dados.objeto_id is not None:
            objeto = _projeto_do_cliente(db, dados.objeto_id, orc.cliente_id)
            # Escolher o projeto traz o nome e o endereco dele, se nao vieram.
            if "projeto_nome" not in enviados:
                orc.projeto_nome = objeto.modelo
            if "endereco_obra" not in enviados:
                orc.endereco_obra = _endereco_do_objeto(objeto)
        orc.objeto_id = dados.objeto_id

    # --- Campos simples: copia direta do que veio ---
    for campo in (
        "projeto_nome", "endereco_obra", "medicao_observacoes", "observacoes_proposta",
        "markup_bp", "perda_bp", "custo_hora_centavos", "rt_padrao_bp", "rt_modo",
        "instalacao_custo_centavos", "validade_dias", "prazo_entrega_dias",
    ):
        if campo in enviados:
            setattr(orc, campo, enviados[campo])

    # --- Desconto e sinal (os limites sao do motor, com `campo`) ---
    if dados.desconto is not None:
        orc.desconto_modo, orc.desconto_valor = dados.desconto.modo, dados.desconto.valor
    if dados.sinal is not None:
        orc.sinal_modo, orc.sinal_valor = dados.sinal.modo, dados.sinal.valor

    fechar_escrita(db, orc)


def substituir_arquitetos(
    db: Session, orcamento_id: int, revisao: int, dados: ArquitetosEntrada, usuario_token: dict,
) -> None:
    """PUT /rt: substitui a lista (Revisao 3).

    Sem `rt_bp`: o arquiteto que ja estava mantem o % gravado; o novo recebe o
    `rt_padrao_bp` do orcamento (mesma regra da D24a). Enviar `rt_bp` exige
    view_custos; trocar QUEM e o arquiteto, so `manage`.
    """
    orc = carregar_para_editar(db, orcamento_id, revisao)
    if any(a.rt_bp is not None for a in dados.arquitetos):
        exigir_custos(usuario_token)

    # Arquiteto e um fornecedor ativo do cadastro.
    ids = [a.fornecedor_id for a in dados.arquitetos]
    fornecedores = crud.buscar_por_ids(db, Fornecedor, ids)
    if any(f not in fornecedores or not fornecedores[f].ativo for f in ids):
        erros.invalido("Arquiteto não encontrado.")

    gravados = {rt.fornecedor_id: rt.rt_bp for rt in orc.rts}   # % de quem ja estava
    orc.rts.clear()                                               # delete-orphan apaga as linhas
    db.flush()
    for a in dados.arquitetos:
        if a.rt_bp is not None:
            rt_bp = a.rt_bp                                       # enviado (com view_custos)
        else:
            rt_bp = gravados.get(a.fornecedor_id, orc.rt_padrao_bp)   # mantem, ou o padrao
        orc.rts.append(MarcenariaOrcamentoRT(fornecedor_id=a.fornecedor_id, rt_bp=rt_bp))

    fechar_escrita(db, orc)


# ===========================================================================
# TRANSICOES (D12-D19)
# ===========================================================================

def _carregar_para_transicao(db: Session, orcamento_id: int, revisao: int, permitidos: tuple) -> MarcenariaOrcamento:
    """Carrega, confere a revisao e se o status atual permite a acao."""
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    if orc.status not in permitidos:
        erros.transicao_invalida(orc.status)
    return orc


def _o_que_falta_para_enviar(orc: MarcenariaOrcamento) -> list[str]:
    """D13: cliente, nome do projeto e pelo menos um movel."""
    faltando = []
    if orc.cliente_id is None:
        faltando.append("o cliente")
    if not (orc.projeto_nome or "").strip():
        faltando.append("o nome do projeto")
    if not any(amb.moveis for amb in orc.ambientes):
        faltando.append("pelo menos um móvel")
    return faltando


def _juntar(itens: list[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b e c'."""
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def exigir_completo_para_enviar(orc: MarcenariaOrcamento, verbo: str = "enviar") -> None:
    """422 dizendo SO o que falta (D13). A 08A reaproveita com verbo="aprovar"."""
    faltando = _o_que_falta_para_enviar(orc)
    if faltando:
        erros.invalido(f"Para {verbo}, informe {_juntar(faltando)}.")


def registrar_envio(db: Session, orc: MarcenariaOrcamento, usuario_token: dict) -> None:
    """Grava envio e validade (D13) e o evento com os valores (Revisao 2).

    O evento guarda o que o cliente RECEBEU (total, sinal, validade), mesmo
    que o orcamento volte a ser editado depois. A 08A usa no envio implicito.
    """
    resultado = calcular_orcamento_do_banco(orc)
    orc.status = StatusOrcamento.ENVIADO
    orc.data_envio = agora_utc()
    orc.data_validade = hoje_local() + timedelta(days=orc.validade_dias)   # conta do envio
    qtd_moveis = sum(len(amb.moveis) for amb in orc.ambientes)
    registrar_evento(
        db, orc, "ORCAMENTO_ENVIADO",
        f"Enviado com total de {reais(resultado.total_centavos)}, válido até {orc.data_validade:%d/%m/%Y}.",
        usuario_token,
        {
            "total_centavos": resultado.total_centavos,
            "sinal_centavos": resultado.sinal_centavos,
            "data_validade": orc.data_validade.isoformat(),
            "qtd_moveis": qtd_moveis,
        },
    )


def enviar(db: Session, orcamento_id: int, revisao: int, usuario_token: dict) -> None:
    """RASCUNHO -> ENVIADO (D13)."""
    orc = _carregar_para_transicao(db, orcamento_id, revisao, (StatusOrcamento.RASCUNHO,))
    exigir_completo_para_enviar(orc)
    registrar_envio(db, orc, usuario_token)
    fechar_escrita(db, orc)


def voltar_a_editar(db: Session, orcamento_id: int, revisao: int, usuario_token: dict) -> None:
    """ENVIADO -> RASCUNHO (D12). A tela ja avisou "o cliente recebeu R$ X"."""
    orc = _carregar_para_transicao(db, orcamento_id, revisao, (StatusOrcamento.ENVIADO,))
    orc.status = StatusOrcamento.RASCUNHO
    registrar_evento(db, orc, "ORCAMENTO_VOLTOU_A_EDITAR", "Voltou para rascunho para ser editado.",
                     usuario_token, {"status_anterior": StatusOrcamento.ENVIADO})
    fechar_escrita(db, orc)


def recusar(db: Session, orcamento_id: int, revisao: int, motivo: str, usuario_token: dict) -> None:
    """ENVIADO ou VENCIDO -> RECUSADO, com motivo (D17)."""
    orc = _carregar_para_transicao(
        db, orcamento_id, revisao, (StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO),
    )
    anterior = orc.status
    orc.status = StatusOrcamento.RECUSADO
    orc.data_recusa = agora_utc()
    orc.motivo_recusa = motivo
    registrar_evento(db, orc, "ORCAMENTO_RECUSADO", f"Recusado pelo cliente: {motivo}",
                     usuario_token, {"motivo": motivo, "status_anterior": anterior})
    fechar_escrita(db, orc)


def renovar(db: Session, orcamento_id: int, revisao: int, usuario_token: dict) -> None:
    """VENCIDO -> RASCUNHO, mesma versao, sem validade (D15)."""
    orc = _carregar_para_transicao(db, orcamento_id, revisao, (StatusOrcamento.VENCIDO,))
    validade_antiga = orc.data_validade
    orc.status = StatusOrcamento.RASCUNHO
    orc.data_validade = None
    registrar_evento(
        db, orc, "ORCAMENTO_RENOVADO", "Renovado: voltou para rascunho para ser reenviado.", usuario_token,
        {"validade_anterior": validade_antiga.isoformat() if validade_antiga else None},
    )
    fechar_escrita(db, orc)


# ===========================================================================
# NOVA VERSAO (D16, secao 7.5)
# ===========================================================================

# Campos do cabecalho que passam para a versao nova (sem datas nem status).
_CAMPOS_COPIADOS = (
    "codigo", "cliente_id", "funcionario_id", "objeto_id", "projeto_nome", "endereco_obra",
    "medicao_observacoes", "markup_bp", "perda_bp", "custo_hora_centavos", "rt_padrao_bp",
    "rt_modo", "validade_dias", "prazo_entrega_dias", "instalacao_custo_centavos",
    "desconto_modo", "desconto_valor", "sinal_modo", "sinal_valor", "observacoes_proposta",
)
_CAMPOS_DO_MOVEL = (
    "nome", "descricao", "largura_mm", "altura_mm", "profundidade_mm", "quantidade",
    "tipo_producao", "central_fornecedor_id", "terceirizado_centavos", "mao_obra_modo",
    "mao_obra_centavos", "mao_obra_horas_centesimos", "ordem",
)
_CAMPOS_DO_INSUMO = (
    "produto_id", "descricao", "codigo", "unidade", "quantidade_milesimos",
    "custo_unit_centavos", "custo_origem", "sofre_perda", "ordem",
)


def copiar_movel(origem: MarcenariaMovel) -> MarcenariaMovel:
    """Copia de um movel com os insumos e os custos COPIADOS (nao os de hoje).

    `aprovado` nao passa: volta a NULL (secao 7.5). Usado pela nova versao e
    pelo duplicar.
    """
    novo = MarcenariaMovel(**{c: getattr(origem, c) for c in _CAMPOS_DO_MOVEL})
    novo.insumos = [
        MarcenariaMovelInsumo(**{c: getattr(i, c) for c in _CAMPOS_DO_INSUMO}) for i in origem.insumos
    ]
    return novo


def nova_versao(db: Session, orcamento_id: int, revisao: int, usuario_token: dict) -> int:
    """Copia a arvore para a versao n+1 em RASCUNHO; a anterior vira SUBSTITUIDO.

    Tudo numa transacao. Devolve o id da versao nova.
    """
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    permitido = orc.status in (StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO, StatusOrcamento.RECUSADO)
    # 08A D21: aprovado com a OS cancelada pela tela de OS -> o cliente voltou.
    if not permitido and not (orc.status == StatusOrcamento.APROVADO and os_cancelada(orc)):
        erros.transicao_invalida(orc.status)
    nova = MarcenariaOrcamento(
        **{c: getattr(orc, c) for c in _CAMPOS_COPIADOS},
        versao=orc.versao + 1,
        status=StatusOrcamento.RASCUNHO,
        revisao=1,
    )
    nova.rts = [MarcenariaOrcamentoRT(fornecedor_id=rt.fornecedor_id, rt_bp=rt.rt_bp) for rt in orc.rts]
    for amb in orc.ambientes:
        novo_amb = MarcenariaAmbiente(nome=amb.nome, ordem=amb.ordem)
        novo_amb.moveis = [copiar_movel(m) for m in amb.moveis]
        nova.ambientes.append(novo_amb)
    db.add(nova)

    orc.status = StatusOrcamento.SUBSTITUIDO                 # a anterior fica so leitura
    orc.revisao += 1                                         # quem estava nela precisa recarregar
    db.flush()                                               # a nova ganha id
    dados = {"versao_anterior": orc.versao, "versao_nova": nova.versao}
    registrar_evento(db, orc, "NOVA_VERSAO", f"Substituído pela versão {nova.versao}.", usuario_token, dados)
    registrar_evento(db, nova, "NOVA_VERSAO", f"Versão {nova.versao} criada a partir da versão {orc.versao}.",
                     usuario_token, dados)
    fechar_escrita(db, nova, somar_revisao=False)            # resumo da nova; ela nasce com revisao 1
    return nova.id


# ===========================================================================
# EXCLUIR (D18)
# ===========================================================================

def excluir(db: Session, orcamento_id: int, revisao: int, usuario_token: dict) -> None:
    """Apaga so a versao 1 em RASCUNHO que nunca foi enviada.

    Os eventos ficam (soltos do orcamento), com mais um registrando a exclusao.
    Os anexos do codigo saem junto: ninguem mais chega a eles.
    """
    orc = carregar(db, orcamento_id)
    conferir_revisao(orc, revisao)
    if not (orc.status == StatusOrcamento.RASCUNHO and orc.versao == 1 and orc.data_envio is None):
        erros.conflito(erros.EXCLUSAO_NAO_PERMITIDA, erros.MSG_EXCLUSAO)

    codigo = orc.codigo
    crud_evento.desligar_eventos_do_orcamento(db, orc.id)
    registrar_evento(db, None, "ORCAMENTO_EXCLUIDO", f"Orçamento {codigo} excluído.", usuario_token,
                     {"codigo": codigo, "versao": orc.versao})
    arquivos = apagar_anexos_do_codigo(db, codigo)            # linhas saem agora; arquivos depois do commit
    db.delete(orc)                                            # cascade: ambientes, moveis, insumos, RT
    db.commit()
    for remover in arquivos:
        remover()                                             # so apaga do disco depois de gravar


# ===========================================================================
# PRECOS (secao 6.5)
# ===========================================================================

def precos_desatualizados(db: Session, orcamento_id: int) -> dict:
    """Insumos com custo ou `sofre_perda` diferentes do produto hoje, e o efeito no total."""
    orc = carregar(db, orcamento_id)
    itens = precos.itens_desatualizados(db, orc)
    total_atual = calcular_orcamento_do_banco(orc).total_centavos
    trocas = precos.substituicoes_para(itens, None)          # previa: todos com o preco de hoje
    total_novo = calcular(montar_entrada_motor(orc, trocas=trocas)).total_centavos
    return {
        "itens": itens,
        "total_atual_centavos": total_atual,
        "total_com_precos_novos_centavos": total_novo,
        "diferenca_centavos": total_novo - total_atual,
    }


def atualizar_precos(
    db: Session, orcamento_id: int, revisao: int, dados: AtualizarPrecosEntrada, usuario_token: dict,
) -> None:
    """Grava os custos de hoje nos insumos escolhidos, com evento (O3). So em RASCUNHO."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    total_antes = calcular_orcamento_do_banco(orc).total_centavos
    itens = precos.itens_desatualizados(db, orc)
    escolhidos = None if dados.todos else set(dados.insumo_ids)
    trocas = precos.substituicoes_para(itens, escolhidos)
    quantidade = precos.aplicar_substituicoes(orc, trocas)
    db.flush()
    db.expire_all()
    total_depois = calcular_orcamento_do_banco(orc).total_centavos
    diferenca = total_depois - total_antes
    sinal = "+" if diferenca >= 0 else "-"
    registrar_evento(
        db, orc, "PRECOS_ATUALIZADOS",
        f"Preços atualizados em {quantidade} insumo(s); total {sinal}{reais(abs(diferenca))}.",
        usuario_token, {"qtd_itens": quantidade, "diferenca_centavos": diferenca},
    )
    fechar_escrita(db, orc)


# ===========================================================================
# LEITURAS: lista, contagens, versoes, projetos, historico
# ===========================================================================

def listar(db: Session, filtros: dict[str, Any], page: int, limit: int, usuario_token: dict) -> dict:
    """Lista paginada (secao 6.3), no formato PaginationBase."""
    exigir_orcamento_tecnico(db)
    marcar_vencidos(db)
    itens, total = crud.listar_orcamentos(db, filtros, hoje_local(), (page - 1) * limit, limit)
    custos = pode_ver_custos_marcenaria(usuario_token)
    return {
        "items": [montar_item_lista(orc, custos) for orc in itens],
        "total_items": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total else 0,
        "links": None,
    }


def contagens(db: Session) -> dict:
    """Quantos por status (so a versao mais recente) e quantos vencem em 3 dias (6.8)."""
    exigir_orcamento_tecnico(db)
    marcar_vencidos(db)
    por_status = crud.contar_por_status(db)
    resposta = {s: por_status.get(s, 0) for s in (
        StatusOrcamento.RASCUNHO, StatusOrcamento.ENVIADO, StatusOrcamento.VENCIDO,
        StatusOrcamento.RECUSADO, StatusOrcamento.APROVADO,
    )}
    resposta["vence_em_3_dias"] = crud.contar_vencendo(db, hoje_local(), 3)
    resposta["total"] = sum(por_status.values())
    return resposta


def versoes(db: Session, orcamento_id: int) -> list[dict]:
    """Todas as versoes do mesmo codigo (numero, status, total, datas)."""
    orc = carregar(db, orcamento_id)
    return [montar_versao(v) for v in crud.listar_versoes(db, orc.codigo)]


def projetos_do_cliente(db: Session, cliente_id: int) -> list[dict]:
    """Projetos (objetos) ativos do cliente para escolher (6.7)."""
    exigir_orcamento_tecnico(db)
    resposta = []
    for objeto, ultimo_uso in crud.listar_projetos_do_cliente(db, cliente_id):
        resposta.append({
            "objeto_id": objeto.id,
            "identificador": objeto.numero_serie,
            "nome": objeto.modelo,
            "endereco_obra": _endereco_do_objeto(objeto),
            # `ultimo_uso` vem do banco como data e hora; a tela mostra so a data.
            "ultimo_uso": ultimo_uso.date().isoformat() if hasattr(ultimo_uso, "date") else str(ultimo_uso)[:10],
        })
    return resposta


def historico(db: Session, orcamento_id: int) -> list[dict]:
    """Eventos de todas as versoes do codigo, do mais novo ao mais antigo."""
    orc = carregar(db, orcamento_id)
    return [
        {
            "id": ev.id,
            "orcamento_id": ev.orcamento_id,
            "tipo": ev.tipo,
            "descricao": ev.descricao,
            "dados": ev.dados,
            "usuario_nome": ev.usuario_nome,
            "ocorrido_em": ev.ocorrido_em,
        }
        for ev in crud_evento.listar_eventos_do_codigo(db, orc.codigo)
    ]
