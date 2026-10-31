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
from app.services.fiscal.nfse.rota import extensao_municipal
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

    tomador.update(_endereco_tomador(cliente))
    return tomador


def _endereco_tomador(cliente) -> dict:
    """O endereço do tomador vai inteiro ou não vai.

    Na DPS ele é opcional, mas o `endNac` exige CEP e município: mandar a rua
    sem CEP derruba a nota no schema ("endNac: Missing child element CEP" —
    OS-2026-000158, 31/10). Cadastro sem CEP válido ou com cidade que não
    achamos no IBGE: a nota sai sem o endereço do tomador.
    """
    enderecos = getattr(cliente, "endereco", None) or []
    if not enderecos:
        return {}
    end = enderecos[0]
    uf = end.estado.value if hasattr(end.estado, "value") else end.estado
    cep = _so_digitos(end.cep)
    municipio = codigo_ibge(end.cidade, uf)
    if not cep or len(cep) != 8 or not municipio:
        return {}
    return {
        "logradouro_tomador": end.logradouro,
        "numero_tomador": end.numero,
        "complemento_tomador": end.complemento,
        "bairro_tomador": end.bairro,
        "cep_tomador": cep,
        "codigo_municipio_tomador": municipio,
    }


def _dps_comum(
    empresa, endereco_empresa, fiscal_settings, fiscal_servico, *,
    descricao: str, base: int, desconto: int, tomador: dict, tomador_pj: bool,
    informacoes: Optional[str], agora: Optional[datetime],
    municipio_prestacao: Optional[str] = None,
    rota=None,
) -> dict:
    """A DPS com o que é igual para a NFS-e da OS e a avulsa (G4).

    `fiscal_servico` é qualquer objeto com os campos do `ServicoFiscal`
    (`codigo_tributacao_nacional`, `codigo_nbs`, `aliquota_iss`...).

    `rota` (G6, `nfse/rota.py`): na municipal a DPS leva `_municipal{}` (CNAE e
    item da LC 116), que a plataforma usa na tradução e nunca repassa à Nacional.
    """
    # Fuso da loja (core/tempo.py): sem `tzdata` no Windows, ZoneInfo("America/Sao_Paulo") quebra.
    agora = (agora or datetime.now(fuso_local())).astimezone(fuso_local())
    uf = endereco_empresa.estado.value if hasattr(endereco_empresa.estado, "value") else endereco_empresa.estado
    municipio = codigo_ibge(endereco_empresa.cidade, uf)
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
        # Onde o serviço foi prestado: a loja, salvo quando a nota diz outro
        # lugar (a instalação da marcenaria é na OBRA, G5).
        "codigo_municipio_prestacao": municipio_prestacao or municipio,
        "codigo_tributacao_nacional_iss": fiscal_servico.codigo_tributacao_nacional,
        "codigo_tributacao_municipal_iss": (getattr(fiscal_servico, "codigo_tributacao_municipio", None) or None),
        "codigo_nbs": fiscal_servico.codigo_nbs,
        "descricao_servico": descricao[:1000],
        "valor_servico": _centavos_para_reais(base),
        "desconto_incondicionado": _centavos_para_reais(desconto) if desconto else None,
        "tributacao_iss": "1",
        # G3: retenção só com a opção ligada E tomador PJ (pessoa física não retém).
        "tipo_retencao_iss": "2" if (tomador_pj and getattr(fiscal_settings, "nfse_reter_iss_pj", False)) else "1",
        "finalidade_emissao": "0",
        # Serviço para empresa não é para consumidor final.
        "consumidor_final": "0" if tomador_pj else "1",
        "indicador_destinatario": "0",
        "informacoes_complementares": informacoes,
        **tomador,
    }

    aliquota = getattr(fiscal_servico, "aliquota_iss", None)
    if opcao_sn == "1" and aliquota:
        dps["percentual_aliquota_relativa_municipio"] = aliquota / 100

    # IBS/CBS: o do serviço; sem ele, o padrão da configuração (G3); sem os dois, nada.
    cst = getattr(fiscal_servico, "cst_ibs_cbs", None) or getattr(fiscal_settings, "nfse_ibs_cbs_cst", None)
    cclass = getattr(fiscal_servico, "c_class_trib", None) or getattr(fiscal_settings, "nfse_ibs_cbs_cclass", None)
    if cst and cclass:
        dps["ibs_cbs_situacao_tributaria"] = cst
        dps["ibs_cbs_classificacao_tributaria"] = cclass

    dps = expurgar_nulos(dps)
    extensao = extensao_municipal(rota, fiscal_servico)
    if extensao:
        dps["_municipal"] = extensao
    return dps


def montar_dps_os(
    empresa, endereco_empresa, fiscal_settings, os_obj, fiscal_servico,
    agora: Optional[datetime] = None,
    itens: Optional[list] = None,
    rota=None,
) -> dict:
    """A DPS da mão de obra da OS. `fiscal_servico` é o `ServicoFiscal` comum aos itens.

    `itens`: só estes serviços (G3, uma nota por código); sem ele, todos os da OS.
    O desconto da OS entra na proporção dos itens desta nota.
    """
    itens = servicos_da_os(os_obj) if itens is None else itens
    cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
    base = sum(i.valor_total for i in itens)
    descricao = "; ".join(
        f"{i.quantidade:g} x {i.nome}" if i.quantidade and i.quantidade != 1 else i.nome
        for i in itens
    )
    return _dps_comum(
        empresa, endereco_empresa, fiscal_settings, fiscal_servico,
        descricao=descricao, base=base, desconto=desconto_dos_servicos(os_obj, base),
        tomador=_tomador(cliente), tomador_pj=isinstance(cliente, ClientePJ),
        informacoes=f"OS {os_obj.numero_os}", agora=agora, rota=rota,
    )


def tomador_digitado(documento: Optional[str], nome: Optional[str], email: Optional[str]) -> dict:
    """O tomador da NFS-e avulsa, digitado na tela (G4). Sem documento, sem tomador."""
    digitos = _so_digitos(documento) or ""
    if not digitos:
        return {}
    chave = "cnpj_tomador" if len(digitos) == 14 else "cpf_tomador"
    return {chave: digitos, "razao_social_tomador": (nome or "")[:150] or None, "email_tomador": (email or "")[:80] or None}


def montar_dps_avulsa(
    empresa, endereco_empresa, fiscal_settings, fiscal_servico, *,
    descricao: str, valor: int, desconto: int = 0, tomador: Optional[dict] = None,
    agora: Optional[datetime] = None, rota=None,
) -> dict:
    """A DPS de um serviço que não passou por OS (G4). Valores em centavos."""
    tomador = tomador or {}
    return _dps_comum(
        empresa, endereco_empresa, fiscal_settings, fiscal_servico,
        descricao=descricao, base=valor, desconto=desconto,
        tomador=tomador, tomador_pj="cnpj_tomador" in tomador,
        informacoes=None, agora=agora, rota=rota,
    )


def montar_dps_instalacao(
    empresa, endereco_empresa, fiscal_settings, fiscal_servico, os_obj, *,
    valor: int, desconto: int, municipio_obra: Optional[str], agora: Optional[datetime] = None,
    rota=None,
) -> dict:
    """A DPS da instalação dos móveis da marcenaria (G5): uma por OS, com o local
    da prestação na cidade da OBRA. Valores em centavos."""
    cliente = getattr(os_obj.objeto, "cliente", None) if os_obj.objeto else None
    return _dps_comum(
        empresa, endereco_empresa, fiscal_settings, fiscal_servico,
        descricao=f"Instalação e montagem de móveis planejados - OS {os_obj.numero_os}",
        base=valor, desconto=desconto,
        tomador=_tomador(cliente), tomador_pj=isinstance(cliente, ClientePJ),
        informacoes=f"OS {os_obj.numero_os}", agora=agora,
        municipio_prestacao=municipio_obra, rota=rota,
    )
