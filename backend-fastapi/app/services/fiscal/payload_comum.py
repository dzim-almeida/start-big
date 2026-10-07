# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_comum.py
# DESCRIÇÃO: Utilitários do payload: texto aceito pela SEFAZ, NCM, GTIN, centavos.
#
# Saiu do payload_builder.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. O payload da nota não muda nem um byte
# (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

import re
from typing import Optional


def _sanitizar_texto_sefaz(texto: str, max_chars: int = 60) -> str:
    """Remove caracteres inválidos para XML da SEFAZ e trunca ao limite."""
    if not texto:
        return ""
    texto = re.sub(r"[&<>\"']", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:max_chars]


def _centavos_para_reais(centavos: int) -> float:
    """Converte centavos (int) para float com 2 decimais."""
    return round(centavos / 100, 2)


SEM_GTIN = "SEM GTIN"


def expurgar_nulos(valor):
    """Remove recursivamente chaves nulas/vazias do payload.

    A integradora e a SEFAZ recusam nós vazios — uma tag de desconto sem valor
    derruba a nota inteira. Como o payload é montado a partir de colunas
    opcionais do banco, sobra `None` em vários pontos; limpar na saída é mais
    seguro do que lembrar de cada `if` na montagem.

    O que É descartado: `None`, string vazia (ou só espaços), dict/lista que
    ficou vazia depois da limpeza.

    O que NÃO é descartado: `0`, `0.0` e `False`. São valores legítimos —
    `valor_desconto: 0.0` e `consumidor_final: 0` mudam de significado se
    sumirem, e o total deixa de fechar.
    """
    if isinstance(valor, dict):
        limpo = {}
        for chave, item in valor.items():
            item_limpo = expurgar_nulos(item)
            if item_limpo is None:
                continue
            limpo[chave] = item_limpo
        return limpo or None

    if isinstance(valor, list):
        limpa = [i for i in (expurgar_nulos(v) for v in valor) if i is not None]
        return limpa or None

    if valor is None:
        return None

    if isinstance(valor, str) and not valor.strip():
        return None

    return valor


def _sanitizar_ncm(ncm: Optional[str]) -> Optional[str]:
    """
    Remove pontuação do NCM. '8471.30.12' → '84713012'.

    O gate já recusa NCM fora do formato, mas quem cadastrou com pontos recebia
    uma pendência sem entender o motivo. Sanitizar aqui fecha o caminho para a
    SEFAZ mesmo que algum cadastro escape do gate.
    """
    if not ncm:
        return None
    return re.sub(r"\D", "", ncm) or None


def _gtin_valido(codigo: Optional[str]) -> bool:
    """
    Confere se o código é um GTIN GS1 legítimo (8, 12, 13 ou 14 dígitos com
    dígito verificador correto).

    Códigos internos de loja não são GTIN. Enviá-los em cEAN gera Rejeição 611.
    """
    if not codigo:
        return False

    digitos = codigo.strip()
    if not digitos.isdigit() or len(digitos) not in (8, 12, 13, 14):
        return False

    # Checksum GS1: pesos 3 e 1 alternados da direita para a esquerda,
    # ignorando o próprio dígito verificador.
    corpo, verificador = digitos[:-1], int(digitos[-1])
    soma = 0
    for posicao, caractere in enumerate(reversed(corpo)):
        soma += int(caractere) * (3 if posicao % 2 == 0 else 1)

    return (10 - soma % 10) % 10 == verificador


def _codigo_barras_para_sefaz(codigo: Optional[str]) -> str:
    """Devolve o GTIN quando válido; senão o literal exigido pela SEFAZ."""
    return codigo.strip() if _gtin_valido(codigo) else SEM_GTIN


def _so_digitos(valor) -> Optional[str]:
    """Remove tudo que não for dígito. Usado só na SAÍDA, nunca no banco.

    CNPJ, CPF e CEP viajam sem pontuação para a SEFAZ. Hoje o cadastro guarda
    esses campos limpos, então isto é rede de proteção e não conserto: se um dia
    entrar um documento mascarado -- por importação, por colagem, por um campo
    novo sem máscara na borda --, a nota é recusada longe daqui, com uma
    mensagem que não aponta para o cadastro.

    Normalizar na borda e não no banco é deliberado: o que o lojista digitou
    continua sendo o que ele vê na tela.
    """
    if valor is None:
        return None
    limpo = re.sub(r"\D", "", str(valor))
    return limpo or None
