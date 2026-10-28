# ---------------------------------------------------------------------------
# ARQUIVO: services/fiscal/nfse/payload.py
# DESCRIÇÃO: Monta a DPS (NFS-e Nacional) da mão de obra de uma OS, já no
#            formato plano da Focus (`/v2/nfsen`). docs/nfse-plano.md, F3.
# ---------------------------------------------------------------------------
"""
A plataforma repassa este corpo à Focus SEM tradução (diferente da NF-e), então
os nomes aqui são os da Focus: campos.focusnfe.com.br/nfse_nacional.

DECISÕES QUE ESTE ARQUIVO CODIFICA (plano, §4):
- D2: a DPS tem UM serviço. Uma OS vira uma nota com a soma dos serviços
  aprovados, todos com o mesmo código nacional — a emissão recusa antes de
  chegar aqui se houver códigos diferentes (`servicos_da_os`).
- D3: sem `serie_dps`/`numero_dps`: a Focus numera (`proximo_numero_nfsen_*`).
  A série do portal não pode colidir — conferir no XML do Alan (F0).
- D4: o desconto da OS entra rateado na proporção dos serviços, como
  `desconto_incondicionado` (o mesmo rateio da NF-e das peças, ao contrário).
- D5: ISS não retido (`tipo_retencao_iss` 1) até alguém pedir retenção.
- Alíquota: MEI e Simples não informam (o ISS vai no DAS e o Sistema Nacional
  completa quando o município aderiu). Regime normal manda a do serviço.
- IBS/CBS: só quando o serviço tem CST e classificação no cadastro. O que o
  Sistema Nacional exige em 2026 para cada regime se confirma na F0.
"""

from datetime import datetime
from typing import Optional

from app.core.enum import OrdemServicoItemAprovacao, OrdemServicoItemTipo
from app.core.tempo import fuso_local
from app.db.models.cliente import ClientePF, ClientePJ
from app.services.fiscal.helpers import CRT_MEI, CRT_SIMPLES_EXCESSO, CRT_SIMPLES_NACIONAL, obter_crt
from app.services.fiscal.nfse.municipio import codigo_ibge
from app.services.fiscal.payload.comum import _centavos_para_reais, _so_digitos, expurgar_nulos


# Regime especial do ISS: o cadastro guarda o código ABRASF (o das NFS-e
# municipais); a DPS nacional usa outra tabela. 5 (MEI) e 6 (ME/EPP do Simples)
# não são regime especial no Sistema Nacional — o Simples já vai em
# `codigo_opcao_simples_nacional`.
REGIME_ESPECIAL_ABRASF_PARA_NACIONAL = {1: "3", 2: "2", 3: "6", 4: "1", 5: "0", 6: "0"}


def servicos_da_os(os_obj) -> list:
    """Itens que entram na NFS-e: serviço, e não reprovados.

    É o espelho de `adaptador_os.itens_de_produto` (a NF-e da OS leva o outro
    lado). Mesmo filtro de `verificar_itens_os_nfse` no gate.
    """
    return [
        i for i in os_obj.itens
        if i.tipo == OrdemServicoItemTipo.SERVICO
        and i.status_aprovacao != OrdemServicoItemAprovacao.REPROVADO
    ]


def desconto_dos_servicos(os_obj, base_servicos: int) -> int:
    """A parte do desconto da OS que cabe aos serviços (centavos)."""
    desconto = os_obj.desconto or 0
    bruto = os_obj.valor_bruto or 0
    if desconto <= 0 or bruto <= 0 or base_servicos <= 0:
        return 0
    return min(base_servicos, round(desconto * base_servicos / bruto))


def opcao_simples_nacional(empresa) -> str:
    """1 = não optante, 2 = MEI, 3 = ME/EPP (tabela `opSimpNac`)."""
    crt = obter_crt(empresa)
    if crt == CRT_MEI:
        return "2"
    if crt in (CRT_SIMPLES_NACIONAL, CRT_SIMPLES_EXCESSO):
        return "3"
    return "1"


def _tomador(cliente) -> dict:
    if cliente is None:
        return {}
    tomador: dict = {}
    if isinstance(cliente, ClientePJ):
        tomador["cnpj_tomador"] = _so_digitos(cliente.cnpj)
        tomador["razao_social_tomador"] = (cliente.razao_social or "")[:150] or None
        tomador["inscricao_municipal_tomador"] = _so_digitos(cliente.im)
    elif isinstance(cliente, ClientePF):
        tomador["cpf_tomador"] = _so_digitos(cliente.cpf)
        tomador["razao_social_tomador"] = (cliente.nome or "")[:150] or None
    tomador["email_tomador"] = (cliente.email or "")[:80] or None
    tomador["telefone_tomador"] = _so_digitos(cliente.celular or cliente.telefone)

    enderecos = getattr(cliente, "endereco", None) or []
    if enderecos:
        end = enderecos[0]
        uf = end.estado.value if hasattr(end.estado, "value") else end.estado
        tomador.update({
            "logradouro_tomador": end.logradouro,
            "numero_tomador": end.numero,
            "complemento_tomador": end.complemento,
            "bairro_tomador": end.bairro,
            "cep_tomador": _so_digitos(end.cep),
            "codigo_municipio_tomador": codigo_ibge(end.cidade, uf),
        })
    return tomador


def montar_dps_os(
    empresa, endereco_empresa, fiscal_settings, os_obj, fiscal_servico,
    agora: Optional[datetime] = None,
) -> dict:
    """A DPS da mão de obra da OS. `fiscal_servico` é o `ServicoFiscal` comum aos itens."""
    # Fuso da loja (core/tempo.py): sem `tzdata` no Windows, ZoneInfo("America/Sao_Paulo") quebra.
    agora = (agora or datetime.now(fuso_local())).astimezone(fuso_local())
    uf = endereco_empresa.estado.value if hasattr(endereco_empresa.estado, "value") else endereco_empresa.estado
    municipio = codigo_ibge(endereco_empresa.cidade, uf)

    itens = servicos_da_os(os_obj)
    base = sum(i.valor_total for i in itens)
    desconto = desconto_dos_servicos(os_obj, base)

    descricao = "; ".join(
        f"{i.quantidade:g} x {i.nome}" if i.quantidade and i.quantidade != 1 else i.nome
        for i in itens
    )
    opcao_sn = opcao_simples_nacional(empresa)

    dps = {
        "data_emissao": agora.isoformat(timespec="seconds"),
        "data_competencia": agora.date().isoformat(),
        "emitente_dps": "1",
        "codigo_municipio_emissora": int(municipio) if municipio else None,
        "cnpj_prestador": _so_digitos(empresa.documento),
        "inscricao_municipal_prestador": _so_digitos(empresa.inscricao_municipal),
        "codigo_opcao_simples_nacional": opcao_sn,
        "regime_especial_tributacao": REGIME_ESPECIAL_ABRASF_PARA_NACIONAL.get(
            fiscal_settings.regime_tributacao_iss or 0, "0"
        ),
        "codigo_municipio_prestacao": municipio,
        "codigo_tributacao_nacional_iss": fiscal_servico.codigo_tributacao_nacional,
        "codigo_tributacao_municipal_iss": (fiscal_servico.codigo_tributacao_municipio or None),
        "codigo_nbs": fiscal_servico.codigo_nbs,
        "descricao_servico": descricao[:1000],
        "valor_servico": _centavos_para_reais(base),
        "desconto_incondicionado": _centavos_para_reais(desconto) if desconto else None,
        "tributacao_iss": "1",
        "tipo_retencao_iss": "1",
        "finalidade_emissao": "0",
        "consumidor_final": "1",
        "indicador_destinatario": "0",
        "informacoes_complementares": f"OS {os_obj.numero_os}",
        **_tomador(getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None),
    }

    if opcao_sn == "1" and fiscal_servico.aliquota_iss:
        dps["percentual_aliquota_relativa_municipio"] = fiscal_servico.aliquota_iss / 100

    if fiscal_servico.cst_ibs_cbs and fiscal_servico.c_class_trib:
        dps["ibs_cbs_situacao_tributaria"] = fiscal_servico.cst_ibs_cbs
        dps["ibs_cbs_classificacao_tributaria"] = fiscal_servico.c_class_trib

    return expurgar_nulos(dps)
