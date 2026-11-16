# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/municipio.py
# DESCRIÇÃO: Código IBGE do município a partir de cidade + UF.
# ---------------------------------------------------------------------------
"""
A NFS-e Nacional exige o código IBGE (7 dígitos) do município emissor e do
local da prestação. A NF-e nunca precisou dele: a Focus resolve o par
município/UF sozinha. Por isso o banco das lojas não o guarda — a tela da
empresa até mostra o código, mas calculado na hora pela API do IBGE, e o
backend descarta o que ela envia.

Em vez de uma coluna nova (e de pedir a cada loja que reabra o cadastro), o
código sai do que as lojas JÁ têm, cidade + UF, cruzado com o Anexo A do
portal da NFS-e embarcado em `app/data/municipios_ibge.csv.gz`. Sem internet.

A UF é obrigatória na chave: há duas Iguatu (CE 2305506, PR 4110052).
"""

from functools import lru_cache
from typing import Optional

from app.core.busca import normalizar
from app.core.seed_nfse import ler_csv_gz


@lru_cache(maxsize=1)
def _indice() -> dict[tuple[str, str], str]:
    """(cidade normalizada, UF) → código. 5.570 linhas, lidas uma vez por processo."""
    return {
        (normalizar(linha["nome"]), linha["uf"]): linha["codigo"]
        for linha in ler_csv_gz("municipios_ibge.csv.gz")
    }


def codigo_ibge(cidade: Optional[str], uf: Optional[str]) -> Optional[str]:
    """
    O código IBGE da cidade, ou None quando não há como saber.

    Compara sem acento, sem caixa e sem pontuação ("SAO PAULO" = "São Paulo",
    "Alta Floresta D'Oeste" = "alta floresta d oeste"). None não é erro aqui:
    quem precisa do código (a completude da NFS-e) transforma a ausência em
    pendência com a mensagem certa.
    """
    if not cidade or not uf:
        return None
    return _indice().get((normalizar(cidade), uf.strip().upper()))
