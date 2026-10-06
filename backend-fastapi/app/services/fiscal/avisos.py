# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/avisos.py
# DESCRIÇÃO: Avisos de cadastro que CONTAM mas NÃO travam a emissão.
#
# Nasceu da primeira NF-e real em produção (06/10/2026): um MEI cadastrado com
# Natureza Jurídica "MEI" e Regime Tributário "1 - Simples Nacional" gastou três
# números com a Rejeição 481 ("CRT diverge do cadastro na SEFAZ"), e um cliente
# PJ sem IE saiu como não contribuinte sem ninguém perceber.
#
# POR QUE AVISO E NÃO PENDÊNCIA: pendência é gate, recusa a nota. A contradição
# MEI × regime tem um caso legítimo — a empresa deixou de ser MEI e o cadastro
# ficou com a natureza antiga —, e nesse caso o regime está CERTO e a nota sai.
# Travar ali pararia uma loja que emite bem. Quem decide qual dos dois campos
# está errado é o lojista ou o contador; o sistema só não deixa passar calado.
#
# Módulo próprio de propósito: `emissao.py` e `payload_builder.py` estão perto
# do teto de bytecode do PyArmor.
# ---------------------------------------------------------------------------

from typing import Optional

from app.services.fiscal.helpers import CRT_MEI, obter_crt

_NOME_CRT = {
    1: "1 - Simples Nacional",
    2: "2 - Simples Nacional (Excesso de Sublimite)",
    3: "3 - Regime Normal",
    4: "4 - MEI",
}


def aviso_regime_mei(empresa) -> Optional[str]:
    """Natureza Jurídica e Regime Tributário discordando sobre ser MEI."""
    if empresa is None:
        return None

    natureza = (getattr(empresa, "natureza_juridica", None) or "").strip().upper()
    crt = obter_crt(empresa)

    if natureza == "MEI" and crt != CRT_MEI:
        return (
            f"Natureza Jurídica está como MEI, mas o Regime Tributário é "
            f"'{_NOME_CRT.get(crt, crt)}' — e é o regime que vai na nota. Se a "
            f"empresa é MEI, troque o regime para '4 - MEI' em Dados da Empresa, "
            f"senão a SEFAZ recusa com a Rejeição 481. Se ela deixou de ser MEI, "
            f"corrija a Natureza Jurídica."
        )

    if crt == CRT_MEI and natureza and natureza != "MEI":
        return (
            f"Regime Tributário está como '4 - MEI', mas a Natureza Jurídica é "
            f"'{natureza}'. Confira com o contador qual dos dois está certo: se a "
            f"empresa não é MEI, a SEFAZ recusa a nota com a Rejeição 481."
        )

    return None


def aviso_destinatario_sem_ie(cliente) -> Optional[str]:
    """Cliente PJ sem IE: a nota sai como não contribuinte (indIEDest 9)."""
    from app.db.models.cliente import ClientePJ

    if not isinstance(cliente, ClientePJ):
        return None
    if not getattr(cliente, "cnpj", None) or getattr(cliente, "ie", None):
        return None

    nome = cliente.razao_social or "este cliente"
    return (
        f"{nome} é pessoa jurídica e não tem Inscrição Estadual cadastrada, então "
        f"a nota vai sair como NÃO contribuinte. Se a empresa tem IE (comprando "
        f"para revender, por exemplo), cadastre a IE no cliente antes de emitir."
    )


def avisos_da_emissao(empresa, cliente) -> list[str]:
    """Tudo o que a prévia da NF-e deve mostrar antes de gastar um número."""
    return [a for a in (aviso_regime_mei(empresa), aviso_destinatario_sem_ie(cliente)) if a]
