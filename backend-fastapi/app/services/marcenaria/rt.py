# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/rt.py
# DESCRICAO: Conta a pagar do RT (reserva tecnica) do arquiteto
#            (Spec 09A, secoes 4.1, 4.2 e 6). Ganchos da OS.
# ---------------------------------------------------------------------------
"""
O arquiteto que indicou a venda recebe um percentual (RT). A conta a pagar dele
nasce quando a OS do orcamento e FINALIZADA (nao se paga RT de obra que nao
terminou), uma por arquiteto, na categoria "Comissao de arquitetos (RT)".

Estas tres funcoes sao GANCHOS da OS (app/services/ordem_servico_ganchos.py):
o servico da OS as chama sem saber o que e marcenaria. Cada uma comeca
procurando o orcamento da OS (consulta por indice) e SAI NA HORA se nao houver
-- e o caso de toda OS de outro segmento.

Rodam DENTRO da transacao da OS: um erro aqui desfaz a finalizacao inteira.
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enum import ContaPagarStatus, PlanoContaTipo
from app.core.regras_preco import reais
from app.core.tempo import hoje_local
from app.db.crud import empresa as empresa_crud
from app.db.crud import financeiro as financeiro_crud
from app.db.crud.configuracao_marcenaria import get_configuracao_marcenaria
from app.db.crud.marcenaria import orcamento as crud
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.db.models.marcenaria.orcamento import MarcenariaOrcamento, MarcenariaOrcamentoRT
from app.db.models.plano_conta import PlanoConta
from app.schemas.conta_pagar import ContaPagarCreate
from app.services import financeiro as financeiro_service
from app.services.marcenaria.calculo import repartir_maior_resto
from app.services.marcenaria.orcamento_calculo import calcular, montar_entrada_motor
from app.services.marcenaria.orcamento_comum import exigir_orcamento_tecnico, registrar_evento

NOME_CATEGORIA_RT = "Comissão de arquitetos (RT)"     # D5: o dono pode renomear depois


def arquitetos_para_escolher(db: Session) -> list[dict]:
    """Arquitetos ativos para o select "Quem indicou" do orcamento (Spec 09B D1, D4).

    Vale a permissao de VER orcamentos: o vendedor escolhe quem indicou mesmo
    sem acesso ao cadastro de fornecedores. Por isso so vai o necessario para
    escolher (id, nome e escritorio) -- PIX e dados bancarios ficam no
    GET /fornecedores, com a permissao de fornecedores.
    """
    exigir_orcamento_tecnico(db)                      # fora da marcenaria: 404, como o resto
    return [
        {"id": f.id, "nome": f.nome, "nome_fantasia": f.nome_fantasia}
        for f in crud.listar_arquitetos_ativos(db)
    ]


# ===========================================================================
# APOIO
# ===========================================================================

def _empresa_da_os(db: Session, os_) -> int:
    """A empresa da OS: a do responsavel; sem ele, a empresa da instalacao."""
    if os_.funcionario is not None and os_.funcionario.empresa_id:
        return os_.funcionario.empresa_id
    return empresa_crud.get_empresa_atual(db).id


def _configuracao(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria:
    """A configuracao da marcenaria, SEM commit (estamos dentro da transacao da OS).

    Ela ja existe: nasceu quando o orcamento foi criado. O "cria" aqui so
    protege um banco montado a mao.
    """
    config = get_configuracao_marcenaria(db, empresa_id)
    if config is None:
        config = ConfiguracaoMarcenaria(empresa_id=empresa_id)
        db.add(config)
        db.flush()
    return config


def _plano_do_rt(db: Session, config: ConfiguracaoMarcenaria, empresa_id: int) -> int:
    """A categoria do RT (D5): a guardada; senao, pelo nome; senao, cria. Guarda o id.

    "Apagar" categoria no sistema e DESATIVAR (o nome e unico por empresa):
    - guardada e ativa -> usa (mesmo renomeada);
    - desativada com o nome padrao -> reativa (o RT precisa de um lugar);
    - renomeada e desativada -> nasce uma nova com o nome padrao.
    """
    if config.rt_plano_conta_id is not None:
        guardada = financeiro_crud.get_plano_conta(db, empresa_id, config.rt_plano_conta_id)
        if guardada is not None and guardada.ativo:
            return guardada.id

    # As categorias padrao da loja nascem na primeira listagem (financeiro).
    # Semeia ANTES, senao a nossa categoria faria a loja parecer "ja configurada"
    # e as padrao nunca nasceriam.
    financeiro_service._semear_plano_padrao(db, empresa_id)

    plano = financeiro_crud.get_plano_conta_por_nome(db, empresa_id, NOME_CATEGORIA_RT)
    if plano is None:
        plano = financeiro_crud.criar_plano_conta(db, PlanoConta(
            empresa_id=empresa_id, nome=NOME_CATEGORIA_RT,
            tipo=PlanoContaTipo.DESPESA.value,            # despesa de venda, nao custo de mercadoria
            padrao=False, ativo=True,
        ))
    elif not plano.ativo:
        plano.ativo = True
    config.rt_plano_conta_id = plano.id
    return plano.id


def _descricao(rt: MarcenariaOrcamentoRT, os_, orc: MarcenariaOrcamento) -> str:
    """D4: 'RT arquiteto — Studio Renascer — OS-2026-000512 (ORC-2026-000084)'."""
    nome = rt.fornecedor.nome if rt.fornecedor else f"fornecedor {rt.fornecedor_id}"
    return f"RT arquiteto — {nome} — {os_.numero_os} ({orc.codigo})"[:255]


def _observacao_de_divergencia(os_, total_aprovado: int) -> Optional[str]:
    """D3: a OS mudou depois da aprovacao (desconto, frete, item manual)."""
    if (os_.valor_total or 0) == total_aprovado:
        return None
    return (f"Total aprovado {reais(total_aprovado)}; OS finalizada com {reais(os_.valor_total or 0)}. "
            "RT calculado sobre o aprovado.")


def _rts_com_conta(orc: MarcenariaOrcamento) -> list[MarcenariaOrcamentoRT]:
    return [rt for rt in orc.rts if rt.conta_pagar is not None]


# ===========================================================================
# GANCHOS
# ===========================================================================

def criar_contas_ao_finalizar(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """Uma conta a pagar por arquiteto, na finalizacao da OS (D1-D7, D9)."""
    orc = crud.get_orcamento_por_os(db, os_.id)
    if orc is None or not orc.rts:                    # OS sem orcamento, ou orcamento sem arquiteto
        return

    # D2: o RT do APROVADO, repartido pelo maior resto (a soma e exata).
    resultado = calcular(montar_entrada_motor(orc, so_aprovados=True))
    linhas = [rt for rt in orc.rts if rt.rt_bp > 0]
    if not linhas:
        return
    valores = repartir_maior_resto(resultado.rt_total_centavos, [rt.rt_bp for rt in linhas])

    empresa_id = _empresa_da_os(db, os_)
    config = _configuracao(db, empresa_id)
    plano_id = None
    vencimento = hoje_local() + timedelta(days=config.rt_vencimento_dias)    # D6
    observacao = _observacao_de_divergencia(os_, resultado.total_centavos)

    criadas = []
    for rt, valor in zip(linhas, valores):
        if valor <= 0:
            continue                                   # percentual tao pequeno que deu zero
        atual = rt.conta_pagar
        if atual is not None and atual.status in (ContaPagarStatus.PAGA.value, ContaPagarStatus.PENDENTE.value):
            continue                                   # D9: reabrir e refinalizar nao duplica
        if plano_id is None:
            plano_id = _plano_do_rt(db, config, empresa_id)
        conta = financeiro_service.criar_conta_pagar(  # o caminho de sempre (auditoria inclusa)
            db, empresa_id,
            ContaPagarCreate(
                descricao=_descricao(rt, os_, orc),
                valor=valor,
                vencimento=vencimento,
                plano_conta_id=plano_id,
                fornecedor_id=rt.fornecedor_id,
                observacao=observacao,
            ),
            usuario or {},
        )
        rt.conta_pagar_id = conta["id"]                # D11: a conta atual
        criadas.append({"fornecedor_id": rt.fornecedor_id,
                        "nome": rt.fornecedor.nome if rt.fornecedor else None,
                        "valor_centavos": valor, "conta_id": conta["id"]})

    if criadas:
        frase = "; ".join(f"RT de {reais(c['valor_centavos'])} para {c['nome']}" for c in criadas) + "."
        if observacao:
            frase = f"{frase} {observacao}"
        registrar_evento(db, orc, "RT_CONTAS_CRIADAS", frase, usuario,
                         {"contas": criadas, "total_aprovado_centavos": resultado.total_centavos,
                          "total_os_centavos": os_.valor_total},
                         os_id=os_.id)


def cancelar_pendentes_ao_reabrir(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """D8: a obra voltou a estar aberta; o RT PENDENTE sai e volta na proxima finalizacao.

    Conta PAGA fica: o que ja foi pago ao arquiteto nao se desfaz sozinho.
    """
    orc = crud.get_orcamento_por_os(db, os_.id)
    if orc is None:
        return
    empresa_id = _empresa_da_os(db, os_)
    for rt in _rts_com_conta(orc):
        if rt.conta_pagar.status == ContaPagarStatus.PENDENTE.value:
            financeiro_service.cancelar_conta_pagar(db, empresa_id, rt.conta_pagar_id, usuario or {})


def tratar_cancelamento(db: Session, os_, usuario: Optional[dict], contexto: Optional[dict] = None) -> None:
    """D10: so importa se a OS estava FINALIZADA (so ai existe conta de RT)."""
    if (contexto or {}).get("status_anterior") != "FINALIZADA":
        return
    orc = crud.get_orcamento_por_os(db, os_.id)
    if orc is None:                                    # OS que nao veio de orcamento
        return
    cancelar_pendentes_ao_reabrir(db, os_, usuario)    # mesma regra para as pendentes
    pagas = [rt for rt in _rts_com_conta(orc) if rt.conta_pagar.status == ContaPagarStatus.PAGA.value]
    if pagas:                                          # a loja precisa saber que ha dinheiro com o arquiteto
        frase = " ".join(
            f"RT já pago ao arquiteto {rt.fornecedor.nome if rt.fornecedor else rt.fornecedor_id} "
            f"({reais(rt.conta_pagar.valor)})." for rt in pagas
        ) + " Combine a devolução por fora."
        registrar_evento(db, orc, "RT_PAGO_EM_OS_CANCELADA", frase, usuario,
                         {"contas": [rt.conta_pagar_id for rt in pagas]}, os_id=os_.id)
