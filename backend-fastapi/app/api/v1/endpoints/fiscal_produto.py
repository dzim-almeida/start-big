# ---------------------------------------------------------------------------
# ARQUIVO: api/v1/endpoints/fiscal_produto.py
# DESCRIÇÃO: O lado fiscal do CADASTRO DE PRODUTO — sugestão de campos, mapa de
#            campos por regime, busca de NCM e pré-validação. Nada aqui emite.
#
# POR QUE É UM ARQUIVO À PARTE
# ----------------------------
# Saiu de `fiscal.py` em 19/09/2026 por dois motivos, um técnico e um de
# desenho, e o técnico foi o gatilho:
#
# 1. O PyArmor (licença trial) tem um teto de tamanho por módulo. `fiscal.py`
#    passou de ~53 KB para 58 KB com os endpoints de perfil tributário da
#    rodada interestadual e o `build:sidecar` parou com "out of license" -- o
#    mesmo que já tinha derrubado o CRUD financeiro em 02/09 (`41a2f8f`,
#    resolvido dividindo o arquivo). Este corte devolve ~10 KB de folga.
#
# 2. Estas rotas servem ao CADASTRO, não ao Centro Fiscal: quem as chama é a
#    tela de produto. A docstring de `sugerir_campos_fiscais_produto` já pedia
#    para "mover a rota para fora deste router" -- para o catálogo poder ficar
#    pronto ANTES de a loja contratar o módulo. O gate abaixo é o MESMO do
#    `fiscal.py` de propósito (comportamento idêntico ao de antes); liberar o
#    cadastro sem o módulo é agora uma linha, e uma decisão de produto.
#
# Registrado em `api.py` sob o MESMO prefixo `/fiscal`: nenhuma URL mudou, o
# frontend não sabe da divisão.
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.depends import get_current_active_user, get_db
from app.core.modulos import requer_modulo
from app.db.crud import fiscal as fiscal_crud
from app.schemas.produto_fiscal import ProdutoFiscalUpdate

# Mesmo gate do fiscal.py -- ver o item 2 do cabeçalho.
router = APIRouter(dependencies=[Depends(requer_modulo("NFE"))])


# ===========================================================================
# SUGESTÃO DE CAMPOS FISCAIS
# ===========================================================================

@router.get(
    "/sugestao/produto",
    summary="Sugerir Campos Fiscais de Produto",
    description=(
        "Devolve os campos fiscais que o sistema consegue deduzir para um "
        "produto novo, com procedência e fundamentação. NÃO persiste nada: "
        "quem decide o que aplicar é o formulário."
    ),
)
def sugerir_campos_fiscais_produto(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    """
    Sugestões para o cadastro de produto.

    Camada de leitura: sugerir não emite nada.

    ATENÇÃO: o router inteiro de `/fiscal` exige o módulo NFE
    (`APIRouter(dependencies=[requer_modulo("NFE")])`), então esta rota TAMBÉM
    exige — ao contrário do que esta docstring afirmava. Deixar o catálogo
    pronto antes de contratar depende de mover a rota para fora deste router,
    o que não foi feito.

    Cada campo vem com `fundamentacao` (o "por quê?" que a tela mostra ao lado)
    e `exige_confirmacao`, ligado onde errar produz nota aceita e errada.
    """
    from app.services.fiscal.derivacao import derivar_produto
    from app.services.fiscal.derivacao.resolver_db import contexto_do_cadastro

    contexto = contexto_do_cadastro(db, user_token["empresa_id"])
    return {"sugestoes": [s.model_dump() for s in derivar_produto(contexto)]}


@router.get(
    "/campos/produto",
    summary="Campos Fiscais Aplicáveis ao Produto",
    description=(
        "Diz quais campos fiscais o cadastro de produto deve mostrar e exigir, "
        "conforme o regime tributário da empresa. Empresa do Simples não vê "
        "CST nem alíquota de ICMS; empresa do regime normal não vê CSOSN."
    ),
)
def campos_fiscais_produto(
    user_token: dict = Depends(get_current_active_user),
    *,
    db: Session = Depends(get_db),
):
    """
    O mapa de campos da tela de produto.

    Quem responde é o mesmo `obter_crt` que decide na hora de emitir — é essa
    a razão de a pergunta vir ao servidor em vez de virar `v-if` na tela.

    Exige o módulo NFE, como todo este router. A tela trata a recusa mostrando
    TODOS os campos: esconder campo obrigatório por falha de consulta produz
    cadastro incompleto que ninguém consegue explicar.
    """
    from app.db.crud import fiscal as crud
    from app.services.fiscal.campos_produto import mapa_campos_da_empresa

    empresa = crud.get_empresa(db, user_token["empresa_id"])
    return mapa_campos_da_empresa(empresa)


# ===========================================================================
# TABELA NCM (achar o código pela descrição)
# ===========================================================================


@router.get(
    "/ncm",
    summary="Buscar NCM por Código ou Descrição",
    description=(
        "Procura na tabela NCM embarcada. Aceita o código (com ou sem pontos) "
        "e a descrição — 'mouse', 'caneta esferográfica'. Funciona sem internet."
    ),
)
def buscar_ncm(
    user_token: dict = Depends(get_current_active_user),
    *,
    buscar: str = Query("", max_length=120),
    limite: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    A busca de NCM.

    Reusa `core/busca.py`, o mesmo motor de produto, cliente e serviço — quatro
    camadas: contém, palavras soltas, acentos com relevância e erro de
    digitação. Filtrar CSV em Python seria um segundo mecanismo de busca, com
    outro comportamento, na mesma tela.

    Varre a `descricao_completa` porque a descrição própria costuma ser um
    fragmento: a do 9608.10.00 é só "Canetas esferográficas", e quem digita
    "caneta para escrever" não a encontraria.
    """
    from app.core import busca as motor_busca
    from app.db.models.ncm import Ncm

    termo = (buscar or "").strip()
    if not termo:
        return {"resultados": [], "total_na_base": db.query(Ncm).count()}

    # Código digitado com pontos ("9608.10.00") casa com o gravado sem eles.
    so_digitos = "".join(c for c in termo if c.isdigit())
    if so_digitos and so_digitos == termo.replace(".", "").replace(" ", "") and len(so_digitos) >= 2:
        resultados = (
            db.query(Ncm)
            .filter(Ncm.codigo.startswith(so_digitos))
            .order_by(Ncm.codigo)
            .limit(limite)
            .all()
        )
        return {
            "resultados": [
                {"codigo": n.codigo, "descricao": n.descricao,
                 "descricao_completa": n.descricao_completa}
                for n in resultados
            ],
            "total_na_base": db.query(Ncm).count(),
        }

    # BUSCA EM DUAS PASSADAS, e as duas razões são igualmente importantes.
    #
    # RELEVÂNCIA: "caneta" tem de trazer 9608.10.00, não um fichário cujo
    # CAPÍTULO menciona canetas. Quem casa na descrição própria vem primeiro.
    #
    # VELOCIDADE: `descricao_completa` guarda a hierarquia inteira (até 2000
    # caracteres) e `LIKE %termo%` não usa índice — varrer as 10.437 linhas
    # custava ~600 ms no pior caso, lento demais para busca enquanto se digita.
    # A primeira passada olha só campos curtos e resolve a maioria das buscas.
    def _consultar(campos):
        consulta = db.query(Ncm)
        filtro = motor_busca.filtro_busca(termo, campos)
        if filtro is None:
            return []
        consulta = consulta.filter(filtro)
        ordem = motor_busca.ordenacao_relevancia(termo, Ncm.descricao, (Ncm.codigo,))
        if ordem is not None:
            consulta = consulta.order_by(ordem)
        return consulta.limit(limite).all()

    resultados = _consultar((Ncm.codigo, Ncm.descricao))

    # Segunda passada só quando a primeira NÃO ACHOU NADA — e não quando ela
    # achou menos que o limite.
    #
    # A diferença é de meio segundo: completar 12 achados bons com 8 fracos
    # obrigava a varrer a hierarquia em TODA busca. Doze resultados relevantes
    # valem mais que vinte com enchimento.
    #
    # A passada existe para o caso do pneu: a descrição própria do 4011.10.00 é
    # "Dos tipos utilizados em automóveis de passageiros", e "pneumáticos" só
    # aparece no ancestral.
    if not resultados:
        vistos = {n.codigo for n in resultados}
        complemento = [
            n for n in _consultar((Ncm.descricao_completa,)) if n.codigo not in vistos
        ]
        resultados = (resultados + complemento)[:limite]

    return {
        "resultados": [
            {
                "codigo": n.codigo,
                "descricao": n.descricao,
                "descricao_completa": n.descricao_completa,
            }
            for n in resultados
        ],
        "total_na_base": db.query(Ncm).count(),
    }



# ===========================================================================
# PRÉ-VALIDAÇÃO DO CADASTRO DE PRODUTO
# ===========================================================================


@router.post(
    "/validar/produto",
    summary="Conferir os Dados Fiscais Antes de Salvar",
    description=(
        "Diz o que a SEFAZ recusaria neste produto, campo a campo, SEM emitir "
        "nada. Aplica a mesma cascata da emissão (produto → regra por NCM → "
        "padrão da loja) e roda a MESMA regra do gate."
    ),
)
def validar_produto_fiscal(
    user_token: dict = Depends(get_current_active_user),
    *,
    dados: ProdutoFiscalUpdate,
    nome_produto: str = Query("Este produto", max_length=120),
    db: Session = Depends(get_db),
):
    """
    A pré-validação do cadastro.

    POR QUE PASSA PELO SERVIDOR, E NÃO É UM ZOD NA TELA
    ---------------------------------------------------
    Porque a regra já existe no `validators.py`, e ela é mais esperta do que
    "campo obrigatório": CEST só é exigido sob substituição tributária, a
    redução de base só com CST 20, e há códigos que o motor ainda não calcula.
    Reescrever isso em Zod criaria um segundo lugar para desatualizar — e
    quando os dois discordam, o cadastro aprova o que a emissão recusa.

    E POR QUE APLICA A CASCATA
    --------------------------
    Sem ela, um produto cadastrado só com NCM apareceria cheio de pendências,
    quando na verdade a loja já respondeu tudo na tributação padrão. A tela
    mostraria erro onde não há.
    """
    from types import SimpleNamespace

    from app.db.crud import tributacao as tributacao_crud
    from app.services.fiscal.helpers import obter_crt, usa_csosn
    from app.services.fiscal.tributacao import mesclar
    from app.services.fiscal.validators import conferir_fiscal_do_produto

    empresa_id = user_token["empresa_id"]
    empresa = fiscal_crud.get_empresa(db, empresa_id)

    rascunho = SimpleNamespace(**dados.model_dump())

    padrao = tributacao_crud.get_tributacao_padrao(db, empresa_id)
    regra = (
        tributacao_crud.get_regra_ncm(db, empresa_id, dados.ncm)
        if dados.ncm else None
    )
    efetivo = mesclar(produto_fiscal=rascunho, regra_ncm=regra, padrao=padrao)

    pendencias = conferir_fiscal_do_produto(
        efetivo,
        nome=nome_produto,
        simples_nacional=usa_csosn(obter_crt(empresa)),
    )

    return {
        "pode_emitir": not pendencias,
        "pendencias": [
            {"campo": p.campo, "mensagem": p.mensagem} for p in pendencias
        ],
        # De onde veio cada valor conferido — a tela diz "CSOSN 102, da
        # tributação padrão da loja" em vez de mostrar campo preenchido sem
        # explicação.
        "procedencia": getattr(efetivo, "procedencia", {}) or {},
    }
