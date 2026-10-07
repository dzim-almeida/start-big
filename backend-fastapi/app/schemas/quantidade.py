# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/quantidade.py
# DESCRIÇÃO: O tipo da quantidade de uma linha de venda/orçamento.
#
# Venda fracionada (docs/venda-fracionada-plano.md, F1): a linha aceita 3,5 kg.
# Duas regras moram aqui, e só aqui:
#   - 3 casas decimais (D2): 3,5 kg = 3,500; o que passar disso é arredondado
#     na ENTRADA, para o ponto flutuante não acumular 0,30000000000000004;
#   - inteiro continua inteiro: 3.0 vira 3. A coluna passou a Float, mas a
#     venda em UN não pode mudar nem no JSON — "3.0 UN" no cupom é regressão.
#
# QUEM pode vender quebrado (KG sim, UN não) depende do produto e mora no
# serviço (`services/quantidade_venda.py`): o schema não conhece o cadastro.
# ---------------------------------------------------------------------------

from typing import Annotated, Union

from pydantic import AfterValidator

CASAS_DECIMAIS = 3


def normalizar_quantidade(valor: Union[int, float]) -> Union[int, float]:
    """3 casas; inteiro volta inteiro. Não valida o sinal (ver `_positiva`)."""
    arredondado = round(float(valor), CASAS_DECIMAIS)
    return int(arredondado) if arredondado.is_integer() else arredondado


def _positiva(valor: Union[int, float]) -> Union[int, float]:
    normalizado = normalizar_quantidade(valor)
    if normalizado <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")
    return normalizado


# Entrada (criar/alterar item): positiva, 3 casas, inteiro volta inteiro.
Quantidade = Annotated[Union[int, float], AfterValidator(_positiva)]

# Saída (leitura): só normaliza — o banco devolve 3.0 para a linha em UN.
QuantidadeLida = Annotated[Union[int, float], AfterValidator(normalizar_quantidade)]
