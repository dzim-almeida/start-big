# ---------------------------------------------------------------------------
# ARQUIVO: test_payload_fotografias.py
# DESCRIÇÃO: Fotografias do payload fiscal por cenário (F0.3 do plano
#            docs/fiscal-refatoracao-plano.md).
#
# POR QUE ISTO EXISTE
# -------------------
# A F5 do plano vai quebrar `payload_builder.py` (1120 linhas) em módulos
# menores. O payload é o que a SEFAZ autoriza: se ele mudar um byte sem querer,
# quem paga é a loja em produção. Estas fotografias travam a saída de HOJE para
# os cenários que existem nas lojas, e a refatoração só passa se elas continuarem
# idênticas.
#
# Completam os dois exemplos de `test_payload_exemplo_auditoria.py` (regime
# normal e Simples, PF na mesma UF), que continuam onde estão. Os cenários
# daqui são os que faltavam — inclusive o do primeiro cliente em produção
# (MEI vendendo para PF de outro estado) e o PJ sem IE que a SEFAZ recusou com
# a 305.
#
# O CFOP de cada item vem dado, como o resolver entregaria: aqui se fotografa
# o MONTADOR, não a derivação (que tem testes próprios em test_derivacao*.py).
#
# Mudou o payload DE PROPÓSITO? Regere e revise o diff dos .json no commit:
#     REGERAR_PAYLOAD=1 pytest test/services/fiscal/test_payload_fotografias.py
# ---------------------------------------------------------------------------

import json
import os
from pathlib import Path

from app.core.enum import State
from app.db.models.cliente import ClientePF, ClientePJ
from app.db.models.endereco import Endereco
from app.services.fiscal.payload_builder import montar_payload_nfe
from app.services.fiscal.tax_engine.engine import calcular_impostos
from app.services.fiscal.tax_engine.types import DadosNota

from test.services.fiscal.test_nfce_payload import _fiscal_settings_nfce, _montar_nfce, _venda_simples
from test.services.fiscal.test_payload_builder import (
    _empresa,
    _endereco_empresa,
    _fiscal_settings,
    _item_venda,
    _pagamento,
    _produto,
    _venda,
)
from test.services.fiscal.test_payload_interestadual import _item_entrada

PASTA = Path(__file__).resolve().parents[3] / "docs" / "payloads" / "fotografias"


def _fotografar(nome: str, payload: dict) -> None:
    """Compara com a fotografia versionada (ou grava, na primeira vez/regerando)."""
    PASTA.mkdir(parents=True, exist_ok=True)
    caminho = PASTA / nome
    atual = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
    texto = json.dumps(atual, ensure_ascii=False, indent=2, sort_keys=True)

    if os.environ.get("REGERAR_PAYLOAD") or not caminho.exists():
        caminho.write_text(texto + "\n", encoding="utf-8")

    gravado = json.loads(caminho.read_text(encoding="utf-8"))
    assert atual == gravado, (
        f"O payload de '{nome}' mudou. Se foi de propósito, rode com "
        f"REGERAR_PAYLOAD=1 e revise o diff do .json no commit; se não foi, "
        f"a mudança quebrou a nota."
    )


def _empresa_mei():
    """O emitente do primeiro cliente em produção: MEI (CRT 4) em SP."""
    empresa = _empresa("MEI")
    empresa.natureza_juridica = "MEI"
    empresa.crt = 4
    return empresa


def _endereco_mg():
    return Endereco(
        logradouro="Rua da Bahia",
        numero="1000",
        bairro="Centro",
        cidade="Belo Horizonte",
        estado=State.MINAS_GERAIS,
        cep="30160011",
    )


def _montar_nfe(venda, itens_entrada, empresa, simples=True):
    resultado = calcular_impostos(itens_entrada, DadosNota(uf_emitente="SP", simples_nacional=simples))
    return montar_payload_nfe(
        empresa=empresa,
        endereco_empresa=_endereco_empresa(),
        fiscal_settings=_fiscal_settings(),
        venda=venda,
        nota_fiscal=None,
        resultado_calculo=resultado,
    )


def test_fotografia_mei_para_pf_de_outro_estado():
    """O caso do Celso: MEI de SP vende para pessoa física em MG (CFOP 6108)."""
    cliente = ClientePF(id=10, nome="Compradora Teste", cpf="52998224725")
    cliente.endereco = [_endereco_mg()]
    iv = _item_venda(1, _produto(1, "Camiseta Algodao"), quantidade=2, valor_unitario=5000)
    venda = _venda([iv], [_pagamento(10000, codigo_sefaz="17", nome="PIX")], cliente=cliente)

    payload = _montar_nfe(venda, [_item_entrada(iv, "6108", csosn="102")], _empresa_mei())

    assert payload["emitente"]["codigo_regime_tributario"] == 4
    _fotografar("nfe-mei-pf-interestadual.json", payload)


def test_fotografia_simples_para_pj_contribuinte_de_outro_estado():
    """Revenda: PJ com IE em MG, CFOP 6102, indIEDest 1."""
    cliente = ClientePJ(id=11, razao_social="Revenda Mineira LTDA", cnpj="11444777000161", ie="0623079040081")
    cliente.endereco = [_endereco_mg()]
    iv = _item_venda(1, _produto(1, "Camiseta Algodao"), quantidade=10, valor_unitario=3000)
    venda = _venda([iv], [_pagamento(30000, codigo_sefaz="15", nome="Boleto")], cliente=cliente)

    payload = _montar_nfe(venda, [_item_entrada(iv, "6102", csosn="102")], _empresa("Simples Nacional"))

    assert payload["destinatario"]["indicador_ie"] == "1"
    _fotografar("nfe-simples-pj-contribuinte-interestadual.json", payload)


def test_fotografia_pj_sem_ie_sai_como_nao_contribuinte():
    """O caso da 305: PJ sem IE cadastrada sai com indIEDest 9."""
    cliente = ClientePJ(id=12, razao_social="Lojinha Teste LTDA", cnpj="11444777000161")
    cliente.endereco = [_endereco_mg()]
    iv = _item_venda(1, _produto(1, "Camiseta Algodao"), quantidade=1, valor_unitario=8000)
    venda = _venda([iv], [_pagamento(8000)], cliente=cliente)

    payload = _montar_nfe(venda, [_item_entrada(iv, "6108", csosn="102")], _empresa("Simples Nacional"))

    assert payload["destinatario"]["indicador_ie"] == "9"
    _fotografar("nfe-simples-pj-sem-ie.json", payload)


def test_fotografia_nfce_com_cpf():
    cliente = ClientePF(id=13, nome="Consumidor Teste", cpf="52998224725")
    payload = _montar_nfce(_venda_simples(total=2500, cliente=cliente), numero=42)
    _fotografar("nfce-com-cpf.json", payload)


def test_fotografia_nfce_consumidor_nao_identificado():
    payload = _montar_nfce(_venda_simples(total=1990), fiscal_settings=_fiscal_settings_nfce(), numero=43)
    _fotografar("nfce-consumidor-nao-identificado.json", payload)


# ── Venda fracionada (docs/venda-fracionada-plano.md, F3) ───────────────────

def _produto_kg():
    produto = _produto(1, "Sacola Kraft")
    produto.unidade_medida = "KG"
    produto.fiscal.unidade_tributavel = "KG"
    return produto


def _item_tres_e_meio_kg():
    """3,5 kg a R$ 30,01/kg = R$ 105,035 → R$ 105,04 (meio-para-cima, como o PDV)."""
    from app.services.quantidade_venda import subtotal_da_linha

    iv = _item_venda(1, _produto_kg(), quantidade=3.5, valor_unitario=3001)
    iv.subtotal = subtotal_da_linha(3.5, 3001)
    assert iv.subtotal == 10504
    return iv


def _confere_629(item):
    """Rejeição 629: vProd tem de bater com qCom × vUnCom em até R$ 0,01."""
    assert abs(item["quantidade_comercial"] * float(item["valor_unitario_comercial"]) - float(item["valor_bruto"])) <= 0.01


def test_fotografia_nfe_tres_e_meio_kg():
    cliente = ClientePF(id=14, nome="Compradora Teste", cpf="52998224725")
    cliente.endereco = [_endereco_empresa()]
    iv = _item_tres_e_meio_kg()
    venda = _venda([iv], [_pagamento(10504)], cliente=cliente)

    payload = _montar_nfe(venda, [_item_entrada(iv, "5102", csosn="102")], _empresa("Simples Nacional"))

    [item] = payload["items"]
    assert (item["quantidade_comercial"], item["unidade_comercial"], float(item["valor_bruto"])) == (3.5, "KG", 105.04)
    _confere_629(item)
    _fotografar("nfe-tres-e-meio-kg.json", payload)


def test_fotografia_nfce_tres_e_meio_kg():
    iv = _item_tres_e_meio_kg()
    venda = _venda([iv], [_pagamento(10504)])

    payload = _montar_nfce(venda, numero=44)

    [item] = payload["items"]
    assert (item["quantidade_comercial"], item["unidade_comercial"]) == (3.5, "KG")
    _confere_629(item)
    _fotografar("nfce-tres-e-meio-kg.json", payload)
