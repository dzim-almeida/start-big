# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/orcamento_arvore.py
# DESCRICAO: Ambientes e moveis do orcamento de marcenaria: incluir, editar,
#            remover, reordenar, duplicar e simular (Spec 06A, §6.1, §6.4, §6.6).
# ---------------------------------------------------------------------------
"""
Toda escrita aqui so vale em RASCUNHO (D11) e confere a revisao (D20); o fecho
(motor, resumo, revisao + 1, commit) e o mesmo de sempre (`fechar_escrita`).

Regra dos insumos (secao 6.4):
- insumo COM `id`: mantem custo, origem, descricao e `sofre_perda` gravados
  (O3); so a quantidade e a ordem mudam;
- insumo SEM `id`: copia do produto (D2, D3);
- `custo_unit_centavos` enviado: custo manual (MANUAL), exige view_custos (D24);
- insumo que nao veio na lista e removido.

D24a: chave de custo AUSENTE no movel (`mao_obra`, `terceirizado_centavos`)
MANTEM o valor gravado. O vendedor sem custos salva o movel sem essas chaves e
nao apaga, sem saber, a mao de obra que o dono lancou.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.fornecedor import Fornecedor
from app.db.models.marcenaria.ambiente import MarcenariaAmbiente, MarcenariaMovel, MarcenariaMovelInsumo
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento
from app.schemas.marcenaria.orcamento import AmbienteEntrada, MovelEntrada, OrdemEntrada, SimularEntrada
from app.services.marcenaria import erros
from app.services.marcenaria import orcamento_precos as precos
from app.services.marcenaria.calculo import (
    AVISO_HORAS_SEM_CUSTO_HORA,
    AVISO_INSUMO_SEM_CUSTO,
    AmbienteCalc,
    InsumoCalc,
    MovelCalc,
    OrcamentoCalc,
)
from app.services.marcenaria.orcamento import copiar_movel
from app.services.marcenaria.orcamento_calculo import calcular, soma_rt_bp
from app.services.marcenaria.orcamento_comum import (
    carregar,
    carregar_para_editar,
    exigir_custos,
    fechar_escrita,
)
from app.services.marcenaria.orcamento_detalhe import recortar_simulacao
from app.services.marcenaria.permissoes import pode_ver_custos_marcenaria

# Limites de tamanho (secao 5.1): protecao, nenhum projeto real chega perto.
LIMITE_AMBIENTES = 50
LIMITE_MOVEIS = 300
LIMITE_INSUMOS = 100

SUFIXO_COPIA = " (cópia)"


# ===========================================================================
# ACHAR NO ORCAMENTO
# ===========================================================================

def _ambiente(orc: MarcenariaOrcamento, ambiente_id: int) -> MarcenariaAmbiente:
    """O ambiente, so se for DESTE orcamento (id de outro da 404)."""
    for amb in orc.ambientes:
        if amb.id == ambiente_id:
            return amb
    erros.nao_encontrado("Ambiente não encontrado.")


def _movel(orc: MarcenariaOrcamento, movel_id: int) -> MarcenariaMovel:
    """O movel, so se for DESTE orcamento."""
    for amb in orc.ambientes:
        for movel in amb.moveis:
            if movel.id == movel_id:
                return movel
    erros.nao_encontrado("Móvel não encontrado.")


def _total_de_moveis(orc: MarcenariaOrcamento) -> int:
    return sum(len(amb.moveis) for amb in orc.ambientes)


def _proxima_ordem(itens) -> int:
    """Ordem de quem entra no fim da lista."""
    return max((item.ordem for item in itens), default=0) + 1


# ===========================================================================
# AMBIENTES
# ===========================================================================

def criar_ambiente(db: Session, orcamento_id: int, revisao: int, dados: AmbienteEntrada) -> None:
    """Novo ambiente no fim da lista."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    if len(orc.ambientes) >= LIMITE_AMBIENTES:
        erros.limite_atingido(LIMITE_AMBIENTES, "ambientes")
    orc.ambientes.append(MarcenariaAmbiente(nome=dados.nome, ordem=_proxima_ordem(orc.ambientes)))
    fechar_escrita(db, orc)


def renomear_ambiente(db: Session, orcamento_id: int, ambiente_id: int, revisao: int, dados: AmbienteEntrada) -> None:
    orc = carregar_para_editar(db, orcamento_id, revisao)
    _ambiente(orc, ambiente_id).nome = dados.nome
    fechar_escrita(db, orc)


def remover_ambiente(db: Session, orcamento_id: int, ambiente_id: int, revisao: int) -> None:
    """Remove o ambiente com os moveis e insumos (cascade)."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    orc.ambientes.remove(_ambiente(orc, ambiente_id))      # delete-orphan apaga a linha
    fechar_escrita(db, orc)


def _reordenar(itens, ids: list[int], nome: str) -> None:
    """Aplica a ordem nova. A lista tem de ter TODOS os ids, sem repetir."""
    if sorted(ids) != sorted(item.id for item in itens):
        erros.invalido(f"A lista deve ter todos os {nome} deste orçamento, sem repetir.")
    posicao = {item_id: indice + 1 for indice, item_id in enumerate(ids)}   # 1, 2, 3...
    for item in itens:
        item.ordem = posicao[item.id]


def ordenar_ambientes(db: Session, orcamento_id: int, revisao: int, dados: OrdemEntrada) -> None:
    orc = carregar_para_editar(db, orcamento_id, revisao)
    _reordenar(orc.ambientes, dados.ids, "ambientes")
    fechar_escrita(db, orc)


def ordenar_moveis(db: Session, orcamento_id: int, ambiente_id: int, revisao: int, dados: OrdemEntrada) -> None:
    orc = carregar_para_editar(db, orcamento_id, revisao)
    _reordenar(_ambiente(orc, ambiente_id).moveis, dados.ids, "móveis do ambiente")
    fechar_escrita(db, orc)


# ===========================================================================
# MOVEL: do corpo recebido para os valores a gravar
# ===========================================================================

def _resolver_insumos(
    db: Session,
    existente: Optional[MarcenariaMovel],
    dados: MovelEntrada,
    usuario_token: dict,
) -> list[dict]:
    """Os insumos como vao ficar (dicionarios), sem gravar nada.

    Serve ao salvar E ao simular: a simulacao bate com o que sera gravado.
    """
    if len(dados.insumos) > LIMITE_INSUMOS:
        erros.limite_atingido(LIMITE_INSUMOS, "insumos por móvel")
    if any(i.custo_unit_centavos is not None for i in dados.insumos):
        exigir_custos(usuario_token)                       # custo manual (D24)

    gravados = {i.id: i for i in existente.insumos} if existente is not None else {}
    ids_enviados = [i.id for i in dados.insumos if i.id is not None]
    if len(set(ids_enviados)) != len(ids_enviados):
        erros.invalido("O mesmo insumo aparece duas vezes.")
    if any(i not in gravados for i in ids_enviados):
        erros.invalido("Insumo não encontrado neste móvel.")

    # Produtos dos insumos NOVOS, numa consulta so.
    produtos = precos.carregar_produtos(db, [i.produto_id for i in dados.insumos if i.id is None])

    resolvidos = []
    for ordem, entrada in enumerate(dados.insumos, start=1):
        if entrada.id is not None:
            antigo = gravados[entrada.id]
            item = {
                "id": antigo.id,
                "produto_id": antigo.produto_id,
                "descricao": antigo.descricao,
                "codigo": antigo.codigo,
                "unidade": antigo.unidade,
                "custo_unit_centavos": antigo.custo_unit_centavos,   # mantem a copia (O3)
                "custo_origem": antigo.custo_origem,
                "sofre_perda": antigo.sofre_perda,
            }
            # Custo digitado diferente do gravado: vira MANUAL. Igual: nada muda
            # (a tela de quem ve custos manda o valor de volta a cada salvamento).
            if entrada.custo_unit_centavos is not None and entrada.custo_unit_centavos != antigo.custo_unit_centavos:
                item["custo_unit_centavos"] = entrada.custo_unit_centavos
                item["custo_origem"] = precos.ORIGEM_MANUAL
        else:
            item = {"id": None, **precos.copiar_do_produto(produtos[entrada.produto_id], entrada.custo_unit_centavos)}
        item["quantidade_milesimos"] = entrada.quantidade_milesimos
        item["ordem"] = ordem
        resolvidos.append(item)
    return resolvidos


def _resolver_movel(db: Session, existente: Optional[MarcenariaMovel], dados: MovelEntrada, usuario_token: dict) -> dict:
    """Os campos do movel como vao ficar (sem os insumos), com a D24a."""
    custos_enviados = dados.mao_obra is not None or dados.terceirizado_centavos is not None
    if custos_enviados:
        exigir_custos(usuario_token)                        # D24

    central_id = dados.central_fornecedor_id if dados.tipo_producao == "TERCEIRIZADA" else None
    if central_id is not None:
        central = db.get(Fornecedor, central_id)
        if central is None or not central.ativo:
            erros.invalido("Central parceira não encontrada.")

    campos = {
        "nome": dados.nome,
        "descricao": dados.descricao,
        "largura_mm": dados.largura_mm,
        "altura_mm": dados.altura_mm,
        "profundidade_mm": dados.profundidade_mm,
        "quantidade": dados.quantidade,
        "tipo_producao": dados.tipo_producao,
        "central_fornecedor_id": central_id,
    }
    # D24a: ausente = mantem o gravado (ou o padrao, no movel novo).
    if dados.terceirizado_centavos is not None:
        campos["terceirizado_centavos"] = dados.terceirizado_centavos
    else:
        campos["terceirizado_centavos"] = existente.terceirizado_centavos if existente else 0
    if dados.mao_obra is not None:
        campos["mao_obra_modo"] = dados.mao_obra.modo
        campos["mao_obra_centavos"] = dados.mao_obra.centavos
        campos["mao_obra_horas_centesimos"] = dados.mao_obra.horas_centesimos
    elif existente is not None:
        campos["mao_obra_modo"] = existente.mao_obra_modo
        campos["mao_obra_centavos"] = existente.mao_obra_centavos
        campos["mao_obra_horas_centesimos"] = existente.mao_obra_horas_centesimos
    else:
        campos["mao_obra_modo"], campos["mao_obra_centavos"], campos["mao_obra_horas_centesimos"] = "NENHUMA", 0, 0
    return campos


def _gravar_insumos(movel: MarcenariaMovel, resolvidos: list[dict]) -> None:
    """Substitui a lista de insumos do movel pelos resolvidos."""
    gravados = {i.id: i for i in movel.insumos}
    nova_lista = []
    for item in resolvidos:
        valores = {k: v for k, v in item.items() if k != "id"}
        if item["id"] is not None:
            insumo = gravados[item["id"]]
            for campo, valor in valores.items():
                setattr(insumo, campo, valor)
        else:
            insumo = MarcenariaMovelInsumo(**valores)
        nova_lista.append(insumo)
    movel.insumos = nova_lista            # quem nao veio sai (delete-orphan)


# ===========================================================================
# MOVEL: incluir, editar, remover, duplicar
# ===========================================================================

def criar_movel(
    db: Session, orcamento_id: int, ambiente_id: int, revisao: int, dados: MovelEntrada, usuario_token: dict,
) -> None:
    """Movel completo, com insumos, no fim do ambiente."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    ambiente = _ambiente(orc, ambiente_id)
    if _total_de_moveis(orc) >= LIMITE_MOVEIS:
        erros.limite_atingido(LIMITE_MOVEIS, "móveis")
    campos = _resolver_movel(db, None, dados, usuario_token)
    insumos = _resolver_insumos(db, None, dados, usuario_token)
    movel = MarcenariaMovel(**campos, ordem=_proxima_ordem(ambiente.moveis))
    _gravar_insumos(movel, insumos)
    ambiente.moveis.append(movel)
    fechar_escrita(db, orc)


def atualizar_movel(
    db: Session, orcamento_id: int, movel_id: int, revisao: int, dados: MovelEntrada, usuario_token: dict,
) -> None:
    """PUT: movel completo (substitui os insumos); pode trocar de ambiente."""
    orc = carregar_para_editar(db, orcamento_id, revisao)
    movel = _movel(orc, movel_id)
    campos = _resolver_movel(db, movel, dados, usuario_token)
    insumos = _resolver_insumos(db, movel, dados, usuario_token)
    for campo, valor in campos.items():
        setattr(movel, campo, valor)
    _gravar_insumos(movel, insumos)

    if dados.ambiente_id is not None and dados.ambiente_id != movel.ambiente_id:
        destino = _ambiente(orc, dados.ambiente_id)
        movel.ordem = _proxima_ordem(destino.moveis)        # entra no fim do outro ambiente
        movel.ambiente = destino                            # troca de pai (nao e orfao)
    fechar_escrita(db, orc)


def remover_movel(db: Session, orcamento_id: int, movel_id: int, revisao: int) -> None:
    orc = carregar_para_editar(db, orcamento_id, revisao)
    movel = _movel(orc, movel_id)
    movel.ambiente.moveis.remove(movel)                     # delete-orphan apaga movel e insumos
    fechar_escrita(db, orc)


def duplicar_movel(db: Session, orcamento_id: int, movel_id: int, revisao: int) -> None:
    """Copia logo abaixo do original, com " (cópia)" no nome (T4).

    Os insumos vao com os MESMOS custos copiados (nao os de hoje).
    """
    orc = carregar_para_editar(db, orcamento_id, revisao)
    original = _movel(orc, movel_id)
    if _total_de_moveis(orc) >= LIMITE_MOVEIS:
        erros.limite_atingido(LIMITE_MOVEIS, "móveis")
    ambiente = original.ambiente
    for outro in ambiente.moveis:                           # abre espaco logo abaixo
        if outro.ordem > original.ordem:
            outro.ordem += 1
    copia = copiar_movel(original)
    copia.nome = original.nome[: 120 - len(SUFIXO_COPIA)] + SUFIXO_COPIA   # cabe na coluna
    copia.ordem = original.ordem + 1
    ambiente.moveis.append(copia)
    fechar_escrita(db, orc)


# ===========================================================================
# SIMULAR (secao 6.6): calcula sem gravar
# ===========================================================================

def simular_movel(db: Session, orcamento_id: int, dados: SimularEntrada, usuario_token: dict) -> dict:
    """O preco do movel com os parametros do orcamento, SEM gravar e sem mexer
    na revisao. Funciona em qualquer status.

    O preco de um movel depende so dele e dos parametros (Spec 05), entao a
    simulacao bate com o que sera gravado. O RT por linha nao sai: depende do
    orcamento inteiro.
    """
    orc = carregar(db, orcamento_id)
    existente = _movel(orc, dados.movel_id) if dados.movel_id is not None else None
    campos = _resolver_movel(db, existente, dados, usuario_token)
    insumos = _resolver_insumos(db, existente, dados, usuario_token)

    movel_calc = MovelCalc(
        id="simulacao",
        quantidade=campos["quantidade"],
        insumos=tuple(
            InsumoCalc(i["quantidade_milesimos"], i["custo_unit_centavos"], i["sofre_perda"]) for i in insumos
        ),
        mao_obra_modo=campos["mao_obra_modo"],
        mao_obra_centavos=campos["mao_obra_centavos"],
        mao_obra_horas_centesimos=campos["mao_obra_horas_centesimos"],
        terceirizado_centavos=campos["terceirizado_centavos"],
    )
    # Um orcamento de mentira com so este movel, nos parametros do de verdade.
    entrada = OrcamentoCalc(
        ambientes=(AmbienteCalc(id="simulacao", moveis=(movel_calc,)),),
        markup_bp=orc.markup_bp,
        perda_bp=orc.perda_bp,
        custo_hora_centavos=orc.custo_hora_centavos,
        rt_bp=soma_rt_bp(orc),
        rt_modo=orc.rt_modo,
        instalacao_custo_centavos=None,
    )
    resultado = calcular(entrada)
    # So os avisos do MOVEL (margem do orcamento de mentira nao interessa).
    avisos = [a for a in resultado.avisos if a in (AVISO_INSUMO_SEM_CUSTO, AVISO_HORAS_SEM_CUSTO_HORA)]
    novos = [
        {"produto_id": i["produto_id"], "custo_unit_centavos": i["custo_unit_centavos"],
         "custo_origem": i["custo_origem"], "sofre_perda": i["sofre_perda"]}
        for i in insumos if i["id"] is None
    ]
    return recortar_simulacao(resultado.ambientes[0].moveis[0], novos, avisos, pode_ver_custos_marcenaria(usuario_token))
