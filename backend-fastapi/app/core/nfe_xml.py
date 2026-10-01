# ---------------------------------------------------------------------------
# ARQUIVO: app/core/nfe_xml.py
# DESCRIÇÃO: Lê a XML da NF-e do fornecedor (entrada por XML, fase 1).
# ---------------------------------------------------------------------------
"""
Só leitura e conta: nada aqui toca o banco. Ver `docs/entrada-xml-nfe-plano.md`.

- Aceita a nota "pura" (`<NFe>`) e a autorizada (`<nfeProc>`), com ou sem
  prefixo de namespace: compara pelo nome local da tag.
- `defusedxml` recusa DOCTYPE/entidades (D3): o arquivo vem de fora.
- Dinheiro sai em CENTAVOS inteiros (arredondamento comercial); quantidade
  sai em Decimal, porque a nota tem até 4 casas.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException


class NotaInvalida(ValueError):
    """O arquivo não é uma NF-e de compra que dê para importar. A mensagem vai para a tela."""


# CST/CSOSN da compra que dizem "este item veio com ICMS-ST" (D7).
CST_COM_ST = frozenset({"10", "30", "60", "70", "90"})
CSOSN_COM_ST = frozenset({"201", "202", "203", "500"})
# PIS/COFINS concentrado na indústria: 02 (alíquota diferenciada), 03 (por
# unidade), 04 (monofásico na revenda).
CST_PIS_MONOFASICO = frozenset({"02", "03", "04"})

SEM_GTIN = "SEM GTIN"

# Unidades da nota que são EMBALAGEM (têm várias unidades dentro). Item numa
# delas com fator 1 é o erro clássico: "2 CX" entrando como 2 latas. A entrada
# exige que alguém diga quantas vêm em cada uma (ver `fator_a_confirmar`).
UNIDADES_DE_EMBALAGEM = frozenset({
    "CX", "CXA", "CAIXA", "FD", "FDO", "FARDO", "PCT", "PACOTE", "PAC", "PK", "PACK",
    "DP", "DISPLAY", "BD", "BDJ", "BANDEJA", "ENG", "ENGRADADO", "EMB", "EMBALAGEM", "DZ", "DUZIA",
})
# As que dizem o tamanho no próprio nome.
FATOR_PELA_UNIDADE = {"DZ": 12, "DUZIA": 12}


@dataclass
class Parte:
    documento: Optional[str] = None  # CNPJ ou CPF, só dígitos
    nome: Optional[str] = None
    fantasia: Optional[str] = None
    ie: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None


@dataclass
class ItemNota:
    indice: int  # nItem
    codigo: str  # cProd — o código do FORNECEDOR
    descricao: str
    ean: Optional[str]
    ean_tributavel: Optional[str]
    ncm: Optional[str]
    cest: Optional[str]
    cfop: Optional[str]
    unidade: str
    quantidade: Decimal
    valor_unitario: Decimal  # vUnCom, em reais (até 10 casas)
    unidade_tributavel: Optional[str]
    quantidade_tributavel: Optional[Decimal]
    valor_produtos: int  # vProd
    desconto: int = 0
    frete: int = 0
    seguro: int = 0
    outras: int = 0
    ipi: int = 0
    icms_st: int = 0  # vICMSST + vFCPST (o que a loja pagou de ST nesta nota)
    cst_icms: Optional[str] = None  # CST ou CSOSN, como veio
    tinha_st: bool = False
    cst_pis: Optional[str] = None

    @property
    def custo_total(self) -> int:
        """O que este item custou de verdade (D6), em centavos."""
        return (
            self.valor_produtos - self.desconto + self.frete + self.seguro
            + self.outras + self.ipi + self.icms_st
        )

    @property
    def monofasico(self) -> bool:
        return self.cst_pis in CST_PIS_MONOFASICO

    @property
    def unidade_de_embalagem(self) -> bool:
        return self.unidade.upper() in UNIDADES_DE_EMBALAGEM

    def fator_sugerido(self) -> int:
        """Unidades por item da nota quando a nota diz (D5): CX 1 → UN 12; DZ → 12."""
        if (
            self.quantidade_tributavel
            and self.unidade_tributavel
            and self.unidade_tributavel.upper() != self.unidade.upper()
            and self.quantidade > 0
        ):
            razao = self.quantidade_tributavel / self.quantidade
            if razao == razao.to_integral_value() and razao > 1:
                return int(razao)
        return FATOR_PELA_UNIDADE.get(self.unidade.upper(), 1)


@dataclass
class Duplicata:
    numero: str
    vencimento: date
    valor: int


@dataclass
class NotaLida:
    chave: str
    numero: str
    serie: str
    emissao: Optional[date]
    natureza: Optional[str]
    emitente: Parte
    destinatario_documento: Optional[str]
    valor_total: int
    itens: list[ItemNota] = field(default_factory=list)
    duplicatas: list[Duplicata] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _filho(no: Optional[Element], *caminho: str) -> Optional[Element]:
    """Desce pelo caminho de nomes locais; None se algum pedaço faltar."""
    atual = no
    for nome in caminho:
        if atual is None:
            return None
        atual = next((f for f in atual if _local(f.tag) == nome), None)
    return atual


def _filhos(no: Optional[Element], nome: str) -> list[Element]:
    return [f for f in no if _local(f.tag) == nome] if no is not None else []


def _texto(no: Optional[Element], *caminho: str) -> Optional[str]:
    alvo = _filho(no, *caminho)
    if alvo is None or alvo.text is None:
        return None
    return alvo.text.strip() or None


def _decimal(valor: Optional[str]) -> Decimal:
    try:
        return Decimal(valor) if valor else Decimal(0)
    except InvalidOperation:
        raise NotaInvalida(f"Valor numérico inválido na nota: {valor!r}.")


def _centavos(valor: Optional[str]) -> int:
    return int((_decimal(valor) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _data(valor: Optional[str]) -> Optional[date]:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        return None


def _ean(valor: Optional[str]) -> Optional[str]:
    if not valor or valor.upper() == SEM_GTIN:
        return None
    return valor


def _parte(no: Optional[Element], endereco: str) -> Parte:
    end = _filho(no, endereco)
    return Parte(
        documento=_texto(no, "CNPJ") or _texto(no, "CPF"),
        nome=_texto(no, "xNome"),
        fantasia=_texto(no, "xFant"),
        ie=_texto(no, "IE"),
        logradouro=_texto(end, "xLgr"),
        numero=_texto(end, "nro"),
        bairro=_texto(end, "xBairro"),
        cidade=_texto(end, "xMun"),
        uf=_texto(end, "UF"),
        cep=_texto(end, "CEP"),
        telefone=_texto(end, "fone"),
    )


def _icms(imposto: Optional[Element]) -> tuple[Optional[str], int, bool]:
    """(CST/CSOSN, ST pago nesta nota, se veio com ST) do grupo ICMS do item.

    O grupo muda de nome com o CST (ICMS00, ICMS60, ICMSSN500…): pega o
    primeiro filho de <ICMS>, seja qual for.
    """
    grupo_icms = _filho(imposto, "ICMS")
    grupo = next(iter(grupo_icms), None) if grupo_icms is not None else None
    if grupo is None:
        return None, 0, False
    cst = _texto(grupo, "CST") or _texto(grupo, "CSOSN")
    st_pago = _centavos(_texto(grupo, "vICMSST")) + _centavos(_texto(grupo, "vFCPST"))
    st_retido = _centavos(_texto(grupo, "vICMSSTRet"))
    tinha_st = st_pago > 0 or st_retido > 0 or cst in CSOSN_COM_ST or (
        cst in CST_COM_ST and cst != "90"
    )
    return cst, st_pago, tinha_st


def _item(det: Element) -> ItemNota:
    prod = _filho(det, "prod")
    imposto = _filho(det, "imposto")
    if prod is None:
        raise NotaInvalida("Item da nota sem o grupo <prod>.")
    cst, st_pago, tinha_st = _icms(imposto)
    pis = _filho(imposto, "PIS")
    grupo_pis = next(iter(pis), None) if pis is not None else None
    qtrib = _texto(prod, "qTrib")
    return ItemNota(
        indice=int(det.get("nItem") or 0),
        codigo=_texto(prod, "cProd") or "",
        descricao=_texto(prod, "xProd") or "",
        ean=_ean(_texto(prod, "cEAN")),
        ean_tributavel=_ean(_texto(prod, "cEANTrib")),
        ncm=_texto(prod, "NCM"),
        cest=_texto(prod, "CEST"),
        cfop=_texto(prod, "CFOP"),
        unidade=(_texto(prod, "uCom") or "UN").upper(),
        quantidade=_decimal(_texto(prod, "qCom")),
        valor_unitario=_decimal(_texto(prod, "vUnCom")),
        unidade_tributavel=(_texto(prod, "uTrib") or None),
        quantidade_tributavel=_decimal(qtrib) if qtrib else None,
        valor_produtos=_centavos(_texto(prod, "vProd")),
        desconto=_centavos(_texto(prod, "vDesc")),
        frete=_centavos(_texto(prod, "vFrete")),
        seguro=_centavos(_texto(prod, "vSeg")),
        outras=_centavos(_texto(prod, "vOutro")),
        ipi=_centavos(_texto(imposto, "IPI", "IPITrib", "vIPI")),
        icms_st=st_pago,
        cst_icms=cst,
        tinha_st=tinha_st,
        cst_pis=_texto(grupo_pis, "CST") if grupo_pis is not None else None,
    )


def ler_nfe(conteudo: bytes | str) -> NotaLida:
    """Lê a NF-e. Levanta `NotaInvalida` com a explicação para o lojista."""
    try:
        raiz = SafeET.fromstring(conteudo)
    except DefusedXmlException:
        raise NotaInvalida("O arquivo tem estruturas não permitidas numa NF-e.")
    except SafeET.ParseError:
        raise NotaInvalida("O arquivo não é um XML válido.")

    nfe = raiz if _local(raiz.tag) == "NFe" else _filho(raiz, "NFe")
    inf = _filho(nfe, "infNFe")
    if inf is None:
        raise NotaInvalida("O arquivo não é uma NF-e (faltou o grupo <infNFe>).")

    ide = _filho(inf, "ide")
    modelo = _texto(ide, "mod")
    if modelo != "55":
        raise NotaInvalida(
            "Este arquivo é uma NFC-e (cupom de venda ao consumidor), não uma nota de compra."
            if modelo == "65" else "Só dá para importar NF-e (modelo 55)."
        )
    if _texto(ide, "tpNF") != "1":
        raise NotaInvalida("Esta é uma nota de entrada emitida pela própria loja, não pelo fornecedor.")

    chave = (inf.get("Id") or "").removeprefix("NFe")
    if len(chave) != 44 or not chave.isdigit():
        # nfeProc traz a chave no protocolo também.
        chave = _texto(raiz, "protNFe", "infProt", "chNFe") or chave
    if len(chave) != 44 or not chave.isdigit():
        raise NotaInvalida("Não achei a chave de acesso da nota (44 dígitos).")

    itens = [_item(det) for det in _filhos(inf, "det")]
    if not itens:
        raise NotaInvalida("A nota não tem itens.")

    duplicatas = []
    for dup in _filhos(_filho(inf, "cobr"), "dup"):
        vencimento = _data(_texto(dup, "dVenc"))
        valor = _centavos(_texto(dup, "vDup"))
        if vencimento and valor > 0:
            duplicatas.append(Duplicata(numero=_texto(dup, "nDup") or "", vencimento=vencimento, valor=valor))

    dest = _filho(inf, "dest")
    return NotaLida(
        chave=chave,
        numero=_texto(ide, "nNF") or "",
        serie=_texto(ide, "serie") or "",
        emissao=_data(_texto(ide, "dhEmi") or _texto(ide, "dEmi")),
        natureza=_texto(ide, "natOp"),
        emitente=_parte(_filho(inf, "emit"), "enderEmit"),
        destinatario_documento=_texto(dest, "CNPJ") or _texto(dest, "CPF"),
        valor_total=_centavos(_texto(inf, "total", "ICMSTot", "vNF")),
        itens=itens,
        duplicatas=duplicatas,
    )


def custo_por_unidade(item: ItemNota, fator: int) -> int:
    """Custo de UMA unidade do estoque (D6): o custo do item ÷ unidades que entram."""
    unidades = item.quantidade * max(fator, 1)
    if unidades <= 0:
        return 0
    return int((Decimal(item.custo_total) / unidades).quantize(Decimal(1), rounding=ROUND_HALF_UP))
