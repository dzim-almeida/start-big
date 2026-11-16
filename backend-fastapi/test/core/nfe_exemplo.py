# ---------------------------------------------------------------------------
# ARQUIVO: test/core/nfe_exemplo.py
# DESCRIÇÃO: Uma NF-e de compra montada como as de verdade, para os testes da
#            entrada por XML. Os valores batem entre si (vProd = qCom × vUnCom).
# ---------------------------------------------------------------------------

CHAVE = "35261012345678000199550010000012341000012345"
CNPJ_FORNECEDOR = "12345678000199"
CNPJ_LOJA = "98765432000110"


def item_cerveja(n: int = 1, ean: str = "17891000000008", ean_trib: str = "7891000000001",
                 codigo: str = "CERV-CX12") -> str:
    """2 CX de 12 a R$ 48,00, −6,00 de desconto, +2,00 de frete, ST de 12,00."""
    return f"""
    <det nItem="{n}">
      <prod>
        <cProd>{codigo}</cProd><cEAN>{ean}</cEAN><xProd>CERVEJA LATA 350ML CX 12</xProd>
        <NCM>22030000</NCM><CEST>0302100</CEST><CFOP>5405</CFOP>
        <uCom>CX</uCom><qCom>2.0000</qCom><vUnCom>48.0000000000</vUnCom><vProd>96.00</vProd>
        <cEANTrib>{ean_trib}</cEANTrib><uTrib>UN</uTrib><qTrib>24.0000</qTrib><vUnTrib>4.0000000000</vUnTrib>
        <vFrete>2.00</vFrete><vDesc>6.00</vDesc><indTot>1</indTot>
      </prod>
      <imposto>
        <ICMS><ICMS10><orig>0</orig><CST>10</CST><vBC>90.00</vBC><pICMS>18.00</pICMS><vICMS>16.20</vICMS>
          <vBCST>156.00</vBCST><pICMSST>18.00</pICMSST><vICMSST>12.00</vICMSST></ICMS10></ICMS>
        <PIS><PISAliq><CST>02</CST><vBC>90.00</vBC><pPIS>2.32</pPIS><vPIS>2.09</vPIS></PISAliq></PIS>
      </imposto>
    </det>"""


def item_biscoito(n: int = 2) -> str:
    """10 UN a R$ 2,50, SEM GTIN, IPI de 1,00, fornecedor do Simples sem ST."""
    return f"""
    <det nItem="{n}">
      <prod>
        <cProd>BISC-01</cProd><cEAN>SEM GTIN</cEAN><xProd>BISCOITO RECHEADO 140G</xProd>
        <NCM>19053100</NCM><CFOP>5102</CFOP>
        <uCom>UN</uCom><qCom>10.0000</qCom><vUnCom>2.5000000000</vUnCom><vProd>25.00</vProd>
        <cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>10.0000</qTrib><vUnTrib>2.5000000000</vUnTrib>
        <indTot>1</indTot>
      </prod>
      <imposto>
        <ICMS><ICMSSN102><orig>0</orig><CSOSN>102</CSOSN></ICMSSN102></ICMS>
        <IPI><cEnq>999</cEnq><IPITrib><CST>50</CST><vBC>25.00</vBC><pIPI>4.00</pIPI><vIPI>1.00</vIPI></IPITrib></IPI>
        <PIS><PISOutr><CST>49</CST><vBC>0.00</vBC><pPIS>0.00</pPIS><vPIS>0.00</vPIS></PISOutr></PIS>
      </imposto>
    </det>"""


def item_caixa_sem_fator(n: int = 1, unidade: str = "CX") -> str:
    """2 CX a R$ 60,00 — a nota NÃO diz quantas vêm na caixa (uTrib também CX)."""
    return f"""
    <det nItem="{n}">
      <prod>
        <cProd>REFRI-CX</cProd><cEAN>SEM GTIN</cEAN><xProd>REFRIGERANTE 2L</xProd>
        <NCM>22021000</NCM><CFOP>5405</CFOP>
        <uCom>{unidade}</uCom><qCom>2.0000</qCom><vUnCom>60.0000000000</vUnCom><vProd>120.00</vProd>
        <cEANTrib>SEM GTIN</cEANTrib><uTrib>{unidade}</uTrib><qTrib>2.0000</qTrib><vUnTrib>60.0000000000</vUnTrib>
        <indTot>1</indTot>
      </prod>
      <imposto><ICMS><ICMSSN500><orig>0</orig><CSOSN>500</CSOSN></ICMSSN500></ICMS></imposto>
    </det>"""


def nota(itens: str | None = None, *, modelo: str = "55", tp_nf: str = "1", chave: str = CHAVE,
         duplicatas: bool = True, proc: bool = True, destinatario: str = CNPJ_LOJA) -> str:
    itens = itens if itens is not None else item_cerveja() + item_biscoito()
    cobr = """
    <cobr>
      <fat><nFat>1234</nFat><vOrig>126.00</vOrig><vLiq>126.00</vLiq></fat>
      <dup><nDup>001</nDup><dVenc>2026-10-31</dVenc><vDup>63.00</vDup></dup>
      <dup><nDup>002</nDup><dVenc>2026-11-30</dVenc><vDup>63.00</vDup></dup>
    </cobr>""" if duplicatas else ""
    nfe = f"""<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe versao="4.00" Id="NFe{chave}">
    <ide><cUF>35</cUF><natOp>VENDA DE MERCADORIA</natOp><mod>{modelo}</mod><serie>1</serie><nNF>1234</nNF>
      <dhEmi>2026-09-30T10:15:00-03:00</dhEmi><tpNF>{tp_nf}</tpNF></ide>
    <emit><CNPJ>{CNPJ_FORNECEDOR}</CNPJ><xNome>DISTRIBUIDORA DE BEBIDAS LTDA</xNome><xFant>DISTRIBEB</xFant>
      <enderEmit><xLgr>RUA DAS INDUSTRIAS</xLgr><nro>100</nro><xBairro>DISTRITO</xBairro><cMun>3550308</cMun>
        <xMun>SAO PAULO</xMun><UF>SP</UF><CEP>01000000</CEP><fone>1133334444</fone></enderEmit>
      <IE>123456789110</IE><CRT>3</CRT></emit>
    <dest><CNPJ>{destinatario}</CNPJ><xNome>ADEGA TESTE</xNome></dest>
    {itens}
    <total><ICMSTot><vProd>121.00</vProd><vFrete>2.00</vFrete><vDesc>6.00</vDesc><vST>12.00</vST>
      <vIPI>1.00</vIPI><vNF>130.00</vNF></ICMSTot></total>
    {cobr}
  </infNFe>
</NFe>"""
    if not proc:
        return nfe
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">{nfe}
  <protNFe versao="4.00"><infProt><chNFe>{chave}</chNFe><cStat>100</cStat></infProt></protNFe>
</nfeProc>"""
