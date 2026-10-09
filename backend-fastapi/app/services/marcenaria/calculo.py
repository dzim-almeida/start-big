# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/calculo.py
# DESCRICAO: Motor de calculo do orcamento de marcenaria (Spec 05, SPEC-00 C1-C9).
#
# O UNICO lugar do sistema que calcula preco, custo, margem, RT, desconto, sinal
# e saldo do orcamento de marcenaria (C8). Todas as outras partes (orcamento,
# aprovacao, OS, RT, telas) usam o resultado daqui e nunca refazem a conta.
#
# REGRAS DE ESCRITA (Spec 05, §6.8):
#   - Funcoes PURAS: recebem numeros, devolvem numeros. Nao leem banco, nao
#     gravam nada, nao sabem de HTTP (um teste confere os imports).
#   - Nada de ponto flutuante: dinheiro em centavos (int), percentuais em basis
#     points (int, 9000 = 90%), quantidade de insumo em milesimos (int, 1,4
#     chapa = 1400), horas em centesimos (int, 2,5 h = 250). Contas
#     intermediarias em Decimal, arredondadas "meio centavo para cima".
#   - So DOIS arredondamentos por movel: o custo unitario e o preco unitario
#     (D3). Tudo acima disso e soma de inteiros, por isso ambiente e total
#     sempre fecham.
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

# --- Constantes de escala ---------------------------------------------------
_BP = Decimal(10000)          # 100% em basis points
_MILESIMOS = Decimal(1000)    # 1 unidade de insumo em milesimos
_CENTESIMOS = Decimal(100)    # 1 hora em centesimos

# --- Limites (os mesmos da Spec 04A §4.1) -----------------------------------
_MARKUP_MAXIMO_BP = 100_000   # 1000%
_PERDA_MAXIMA_BP = 5_000      # 50%
_RT_MAXIMO_BP = 3_000         # 30%

# --- Codigos de aviso (§6.7). As telas traduzem o codigo num texto. ---------
AVISO_INSUMO_SEM_CUSTO = "INSUMO_SEM_CUSTO"
AVISO_HORAS_SEM_CUSTO_HORA = "HORAS_SEM_CUSTO_HORA"
AVISO_MARGEM_NEGATIVA = "MARGEM_NEGATIVA"
AVISO_ORCAMENTO_VAZIO = "ORCAMENTO_VAZIO"


# ===========================================================================
# ENTRADA (§5.1)
# ===========================================================================

@dataclass(frozen=True)
class InsumoCalc:
    """Um insumo do movel, POR UNIDADE do movel."""
    quantidade_milesimos: int        # 1,4 chapa = 1400; deve ser > 0
    custo_unit_centavos: int         # custo de 1 unidade do produto (O3a); >= 0
    sofre_perda: bool                # copiado do produto (Spec 04A)


@dataclass(frozen=True)
class MovelCalc:
    """Um movel do orcamento (ja so os incluidos; D13)."""
    id: str                          # devolvido como veio, para quem chamou se achar
    quantidade: int                  # unidades do movel; >= 1
    insumos: tuple[InsumoCalc, ...]  # pode ser vazio (movel so de terceirizado, por exemplo)
    mao_obra_modo: Literal["FIXA", "HORAS", "NENHUMA"]
    mao_obra_centavos: int = 0           # usado em FIXA, por unidade; >= 0
    mao_obra_horas_centesimos: int = 0   # usado em HORAS, por unidade; >= 0
    terceirizado_centavos: int = 0       # custo do pedido externo, por unidade (E6); >= 0


@dataclass(frozen=True)
class AmbienteCalc:
    """Um ambiente (Cozinha, Dormitorio...) com os moveis incluidos."""
    id: str
    moveis: tuple[MovelCalc, ...]


@dataclass(frozen=True)
class AjusteCalc:
    """Desconto ou sinal: percentual OU valor (D8, D12)."""
    modo: Literal["PERCENTUAL", "VALOR"]
    valor: int                       # bp em PERCENTUAL, centavos em VALOR; >= 0


@dataclass(frozen=True)
class OrcamentoCalc:
    """O orcamento inteiro, com os parametros copiados da configuracao (Spec 04A)."""
    ambientes: tuple[AmbienteCalc, ...]
    markup_bp: int                   # 0 a 100000
    perda_bp: int                    # 0 a 5000
    custo_hora_centavos: int         # >= 0
    rt_bp: int                       # 0 a 3000
    rt_modo: Literal["MARGEM", "PRECO"]
    instalacao_custo_centavos: int | None   # None = sem linha de instalacao (ou nao incluida)
    desconto: AjusteCalc = AjusteCalc("PERCENTUAL", 0)
    sinal: AjusteCalc = AjusteCalc("PERCENTUAL", 0)


# ===========================================================================
# SAIDA (§5.2)
# ===========================================================================

@dataclass(frozen=True)
class MovelResultado:
    id: str
    quantidade: int
    material_centavos: Decimal       # por unidade, sem arredondar (exibicao pode arredondar)
    perda_centavos: Decimal          # por unidade, sem arredondar
    mao_obra_centavos: Decimal       # por unidade, sem arredondar
    terceirizado_centavos: int       # por unidade
    custo_unit_centavos: int         # 1o arredondamento (D3)
    preco_unit_centavos: int         # 2o arredondamento (D3)
    custo_total_centavos: int        # custo_unit x quantidade
    preco_total_centavos: int        # preco_unit x quantidade (bruto, antes do desconto)
    rt_linha_centavos: int           # parte do RT desta linha (D10)
    rt_unit_centavos: int            # rt_linha // quantidade (D11)
    custo_os_unit_centavos: int      # custo_unit + rt_unit -> custo_unitario do item da OS (C5d)


@dataclass(frozen=True)
class AmbienteResultado:
    id: str
    moveis: tuple[MovelResultado, ...]
    subtotal_centavos: int           # soma dos preco_total (bruto); e o que a proposta mostra
    custo_centavos: int              # soma dos custo_total


@dataclass(frozen=True)
class InstalacaoResultado:
    custo_centavos: int
    preco_centavos: int
    rt_linha_centavos: int
    custo_os_centavos: int           # custo + rt_linha (quantidade 1)


@dataclass(frozen=True)
class OrcamentoResultado:
    ambientes: tuple[AmbienteResultado, ...]
    instalacao: InstalacaoResultado | None
    bruto_centavos: int              # soma dos subtotais + instalacao
    desconto_centavos: int
    total_centavos: int              # bruto - desconto (o que o cliente paga)
    custo_total_centavos: int        # soma dos custos + custo da instalacao
    margem_bruta_centavos: int       # total - custo_total
    rt_total_centavos: int           # arred(total x RT) (D9)
    margem_liquida_centavos: int     # margem_bruta - rt_total
    margem_liquida_bp: int           # D14
    sinal_centavos: int
    saldo_centavos: int              # total - sinal
    desconto_bp_efetivo: int         # so exibicao: o % equivalente ao desconto
    sinal_bp_efetivo: int            # so exibicao: o % equivalente ao sinal
    avisos: tuple[str, ...]          # codigos da §6.7


# ===========================================================================
# FUNCOES PUBLICAS AUXILIARES
# ===========================================================================

def arredondar(valor: Decimal) -> int:
    """Arredonda para o inteiro mais proximo, meio para cima (C6, D2).

    Entra: Decimal em centavos (ou bp). Sai: int na mesma unidade.
    10.5 -> 11; 10.4999 -> 10; -0 -> 0.
    """
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def fator_preco(markup_bp: int, rt_bp: int, rt_modo: str) -> Decimal:
    """Multiplicador que leva o custo ao preco (D7, C5c).

    Entra: markup e RT em basis points, modo do RT. Sai: Decimal sem unidade.
      MARGEM: (1 + markup)            -> o RT sai da margem da loja;
      PRECO:  (1 + markup) / (1 - RT) -> depois de pagar o RT sobre o preco,
                                         sobra o mesmo que sobraria sem arquiteto.
    """
    com_markup = 1 + Decimal(markup_bp) / _BP                   # ex.: 9000 bp -> 1,9
    if rt_modo == "PRECO":
        return com_markup / (1 - Decimal(rt_bp) / _BP)          # ex.: 1,9 / 0,92
    return com_markup


def repartir_maior_resto(total: int, pesos: list[int]) -> list[int]:
    """Divide `total` centavos proporcionalmente aos `pesos`, com soma EXATA (D10).

    Entra: total em centavos e os pesos (precos brutos das linhas, em centavos).
    Sai: uma parte inteira por peso, em centavos, que somam exatamente `total`.

    1. Cada parte recebe o piso da sua fracao.
    2. Os centavos que sobram vao, um a um, para as maiores fracoes perdidas;
       empate: a linha que vem primeiro.
    """
    soma_pesos = sum(pesos)
    if total == 0 or soma_pesos == 0:
        return [0] * len(pesos)                                      # nada a repartir
    exatas = [Decimal(total) * p / soma_pesos for p in pesos]        # fracao ideal de cada linha
    partes = [int(x) for x in exatas]                                # piso (valores >= 0)
    sobra = total - sum(partes)                                      # centavos ainda sem dono
    # Maior resto primeiro; em empate, a linha que vem antes (indice menor).
    ordem = sorted(range(len(pesos)), key=lambda i: (-(exatas[i] - partes[i]), i))
    for i in ordem[:sobra]:
        partes[i] += 1
    return partes


# ===========================================================================
# VALIDACOES (§6.6) — erros bloqueiam; avisos (§6.7) nao
# ===========================================================================

def _nao_negativo(*valores: int) -> None:
    """Centavos, horas e bp nunca podem ser negativos."""
    if any(v < 0 for v in valores):
        raise ValueError("Valores não podem ser negativos.")


def _validar_ajuste(ajuste: AjusteCalc) -> None:
    """Desconto ou sinal: modo conhecido, valor >= 0, percentual ate 100%."""
    if ajuste.modo not in ("PERCENTUAL", "VALOR"):
        raise ValueError("Forma de desconto ou sinal inválida.")
    _nao_negativo(ajuste.valor)
    if ajuste.modo == "PERCENTUAL" and ajuste.valor > 10_000:
        raise ValueError("O percentual não pode passar de 100%.")


def _validar(orcamento: OrcamentoCalc) -> None:
    """Confere a entrada inteira antes de calcular qualquer coisa."""
    _nao_negativo(orcamento.markup_bp, orcamento.perda_bp, orcamento.custo_hora_centavos, orcamento.rt_bp)
    if orcamento.markup_bp > _MARKUP_MAXIMO_BP:
        raise ValueError("O markup deve ficar entre 0% e 1000%.")
    if orcamento.perda_bp > _PERDA_MAXIMA_BP:
        raise ValueError("A perda deve ficar entre 0% e 50%.")
    if orcamento.rt_bp > _RT_MAXIMO_BP:
        raise ValueError("O RT deve ficar entre 0% e 30%.")
    if orcamento.rt_modo not in ("MARGEM", "PRECO"):
        raise ValueError("Modo do RT inválido.")
    if orcamento.instalacao_custo_centavos is not None:
        _nao_negativo(orcamento.instalacao_custo_centavos)
    _validar_ajuste(orcamento.desconto)
    _validar_ajuste(orcamento.sinal)

    for ambiente in orcamento.ambientes:
        for movel in ambiente.moveis:
            if movel.quantidade < 1:
                raise ValueError("A quantidade do móvel deve ser pelo menos 1.")
            if movel.mao_obra_modo not in ("FIXA", "HORAS", "NENHUMA"):
                raise ValueError("Forma de mão de obra inválida.")
            _nao_negativo(movel.mao_obra_centavos, movel.mao_obra_horas_centesimos, movel.terceirizado_centavos)
            for insumo in movel.insumos:
                if insumo.quantidade_milesimos <= 0:
                    raise ValueError("A quantidade do insumo deve ser maior que zero.")
                _nao_negativo(insumo.custo_unit_centavos)


# ===========================================================================
# CALCULO
# ===========================================================================

def _custos_do_movel(movel: MovelCalc, perda_bp: int, custo_hora_centavos: int) -> tuple[Decimal, Decimal, Decimal]:
    """Passos 1 e 2 (§6.1, §6.2), POR UNIDADE do movel, sem arredondar.

    Sai: (material, perda, mao_de_obra), todos em centavos (Decimal).
    """
    material = Decimal(0)
    perda = Decimal(0)
    for insumo in movel.insumos:
        quantidade = Decimal(insumo.quantidade_milesimos) / _MILESIMOS     # 1400 -> 1,4 chapa
        custo_insumo = quantidade * insumo.custo_unit_centavos              # 1,4 x R$ 280,00
        material += custo_insumo
        if insumo.sofre_perda:                                              # MDF e fita sim; ferragem nao (C2)
            perda += custo_insumo * perda_bp / _BP
    if movel.mao_obra_modo == "FIXA":
        mao_obra = Decimal(movel.mao_obra_centavos)                         # valor por unidade
    elif movel.mao_obra_modo == "HORAS":
        horas = Decimal(movel.mao_obra_horas_centesimos) / _CENTESIMOS      # 400 -> 4,00 h
        mao_obra = horas * custo_hora_centavos                              # 4,00 h x R$ 45,00
    else:
        mao_obra = Decimal(0)                                               # NENHUMA
    return material, perda, mao_obra


def calcular_orcamento(orcamento: OrcamentoCalc) -> OrcamentoResultado:
    """Calcula o orcamento inteiro (Spec 05, §6).

    Entra: OrcamentoCalc (centavos, bp, milesimos e centesimos, todos int).
    Sai: OrcamentoResultado (centavos e bp em int; so os detalhes de custo
    por movel ficam em Decimal, sem arredondar, para exibicao).
    Levanta ValueError (mensagem em portugues) se a entrada for invalida.
    """
    _validar(orcamento)
    avisos: list[str] = []

    def avisar(codigo: str) -> None:
        if codigo not in avisos:                                            # cada aviso uma vez so
            avisos.append(codigo)

    fator = fator_preco(orcamento.markup_bp, orcamento.rt_bp, orcamento.rt_modo)

    # --- Passos 1 a 3: cada movel (custo e preco unitarios, totais da linha) ---
    # Guardamos o "rascunho" de cada movel; o RT da linha so vem no passo 5.
    rascunhos: list[list[dict]] = []
    for ambiente in orcamento.ambientes:
        do_ambiente = []
        for movel in ambiente.moveis:
            if any(i.custo_unit_centavos == 0 for i in movel.insumos):
                avisar(AVISO_INSUMO_SEM_CUSTO)                              # O3a: custo nao copiado
            if (movel.mao_obra_modo == "HORAS" and movel.mao_obra_horas_centesimos > 0
                    and orcamento.custo_hora_centavos == 0):
                avisar(AVISO_HORAS_SEM_CUSTO_HORA)                          # mao de obra sai zerada

            material, perda, mao_obra = _custos_do_movel(movel, orcamento.perda_bp, orcamento.custo_hora_centavos)
            # 1o arredondamento: custo direto unitario (vira custo_unitario da OS).
            custo_unit = arredondar(material + perda + mao_obra + movel.terceirizado_centavos)
            # 2o arredondamento: preco unitario (vira valor_unitario da OS).
            preco_unit = arredondar(custo_unit * fator)
            do_ambiente.append({
                "movel": movel, "material": material, "perda": perda, "mao_obra": mao_obra,
                "custo_unit": custo_unit, "preco_unit": preco_unit,
                "custo_total": custo_unit * movel.quantidade,               # soma de inteiros
                "preco_total": preco_unit * movel.quantidade,
            })
        rascunhos.append(do_ambiente)

    # Instalacao: linha propria, com o mesmo fator dos moveis (C3, C3a).
    tem_instalacao = orcamento.instalacao_custo_centavos is not None
    instalacao_custo = orcamento.instalacao_custo_centavos or 0
    instalacao_preco = arredondar(instalacao_custo * fator) if tem_instalacao else 0

    if not any(rascunhos_do_ambiente for rascunhos_do_ambiente in rascunhos) and not tem_instalacao:
        avisar(AVISO_ORCAMENTO_VAZIO)

    # --- Passo 4: totais, desconto, RT, margem e sinal (§6.4) ------------------
    subtotais = [sum(r["preco_total"] for r in amb) for amb in rascunhos]
    bruto = sum(subtotais) + instalacao_preco
    if orcamento.desconto.modo == "PERCENTUAL":
        desconto = arredondar(Decimal(bruto) * orcamento.desconto.valor / _BP)
    else:
        desconto = orcamento.desconto.valor
        if desconto > bruto:
            raise ValueError("O desconto não pode ser maior que o total do orçamento.")
    total = bruto - desconto                                                # o que o cliente paga
    custo_total = sum(r["custo_total"] for amb in rascunhos for r in amb) + instalacao_custo
    margem_bruta = total - custo_total
    rt_total = arredondar(Decimal(total) * orcamento.rt_bp / _BP)          # RT sobre o liquido (D9)
    margem_liquida = margem_bruta - rt_total
    margem_liquida_bp = arredondar(Decimal(margem_liquida) / total * _BP) if total else 0   # D14
    if margem_liquida < 0:
        avisar(AVISO_MARGEM_NEGATIVA)

    if orcamento.sinal.modo == "PERCENTUAL":
        sinal = arredondar(Decimal(total) * orcamento.sinal.valor / _BP)
    else:
        sinal = orcamento.sinal.valor
        if sinal > total:
            raise ValueError("O sinal não pode ser maior que o total do orçamento.")
    saldo = total - sinal

    # Percentuais "efetivos": SO exibicao (a tela mostra o % do valor digitado).
    desconto_bp_efetivo = arredondar(Decimal(desconto) / bruto * _BP) if bruto else 0
    sinal_bp_efetivo = arredondar(Decimal(sinal) / total * _BP) if total else 0

    # --- Passo 5: repartir o RT pelas linhas, pelo maior resto (§6.5) ----------
    # Linhas: moveis na ordem recebida (ambiente por ambiente), instalacao por ultimo.
    pesos = [r["preco_total"] for amb in rascunhos for r in amb]
    if tem_instalacao:
        pesos.append(instalacao_preco)
    partes = repartir_maior_resto(rt_total, pesos)

    ambientes_resultado = []
    indice = 0                                                             # posicao em `partes`
    for ambiente, do_ambiente, subtotal in zip(orcamento.ambientes, rascunhos, subtotais):
        moveis_resultado = []
        for r in do_ambiente:
            movel = r["movel"]
            rt_linha = partes[indice]
            indice += 1
            rt_unit = rt_linha // movel.quantidade                          # por baixo (D11)
            moveis_resultado.append(MovelResultado(
                id=movel.id,
                quantidade=movel.quantidade,
                material_centavos=r["material"],
                perda_centavos=r["perda"],
                mao_obra_centavos=r["mao_obra"],
                terceirizado_centavos=movel.terceirizado_centavos,
                custo_unit_centavos=r["custo_unit"],
                preco_unit_centavos=r["preco_unit"],
                custo_total_centavos=r["custo_total"],
                preco_total_centavos=r["preco_total"],
                rt_linha_centavos=rt_linha,
                rt_unit_centavos=rt_unit,
                custo_os_unit_centavos=r["custo_unit"] + rt_unit,           # custo_unitario do item da OS
            ))
        ambientes_resultado.append(AmbienteResultado(
            id=ambiente.id,
            moveis=tuple(moveis_resultado),
            subtotal_centavos=subtotal,
            custo_centavos=sum(m.custo_total_centavos for m in moveis_resultado),
        ))

    instalacao_resultado = None
    if tem_instalacao:
        rt_instalacao = partes[indice]                                     # a ultima linha
        instalacao_resultado = InstalacaoResultado(
            custo_centavos=instalacao_custo,
            preco_centavos=instalacao_preco,
            rt_linha_centavos=rt_instalacao,
            custo_os_centavos=instalacao_custo + rt_instalacao,
        )

    return OrcamentoResultado(
        ambientes=tuple(ambientes_resultado),
        instalacao=instalacao_resultado,
        bruto_centavos=bruto,
        desconto_centavos=desconto,
        total_centavos=total,
        custo_total_centavos=custo_total,
        margem_bruta_centavos=margem_bruta,
        rt_total_centavos=rt_total,
        margem_liquida_centavos=margem_liquida,
        margem_liquida_bp=margem_liquida_bp,
        sinal_centavos=sinal,
        saldo_centavos=saldo,
        desconto_bp_efetivo=desconto_bp_efetivo,
        sinal_bp_efetivo=sinal_bp_efetivo,
        avisos=tuple(avisos),
    )
