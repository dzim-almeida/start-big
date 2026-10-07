# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/diagnostico_sefaz.py
# DESCRIÇÃO: O que uma rejeição da SEFAZ quer dizer, e o que o lojista faz.
#
# Até 07/10/2026 isto morava só no front (fiscalDiagnostic.ts e
# fiscalDiagnosticCodigos.ts). Veio para o backend (F5 do plano fiscal) para a
# MESMA explicação servir ao drawer, ao texto de suporte e a qualquer relatório
# — e para corrigir um conselho errado sem depender de atualizar a tela.
#
# Ordem da decisão, que não pode inverter:
#   1. o cStat, quando está na TABELA — ele identifica a regra sem ambiguidade;
#   2. só então palavras-chave na mensagem, para código que não está aqui.
# A primeira NF-e real em produção (06/10/2026) mostrou o custo do contrário:
# a 481 ("...do EMITENTE diverge...") caiu em "cadastre o certificado" por
# causa da palavra "emitente". Três rejeições, três conselhos errados.
#
# Só entra código conferido no Manual de Orientação do Contribuinte (MOC). Na
# dúvida, fica de fora: o genérico mostra a mensagem da SEFAZ, que é melhor do
# que um conselho errado.
#
# Cor e ícone NÃO estão aqui: a tela pinta pela `categoria`.
# ---------------------------------------------------------------------------

import re
from typing import Callable, Optional

# Só nestes status a tela mostra o diagnóstico.
STATUS_COM_DIAGNOSTICO = ("REJEITADA", "DENEGADA")


def ler_chave_da_mensagem(mensagem: Optional[str]) -> Optional[dict]:
    """
    Lê a chave de acesso que a SEFAZ devolve na 539 ("[chNFe:3526...]").

    Posições da chave (44 dígitos): UF(2) AAMM(4) CNPJ(14) modelo(2) série(3)
    número(9) tpEmis(1) código(8) DV(1).
    """
    achado = re.search(r"chNFe:\s*(\d{44})", mensagem or "")
    if not achado:
        return None
    chave = achado.group(1)
    return {
        "chave": chave,
        "mes": chave[4:6],
        "ano": f"20{chave[2:4]}",
        "serie": int(chave[22:25]),
        "numero": int(chave[25:34]),
    }


def _diag(categoria, rotulo, titulo, explicacao, como_resolver, acao=None) -> dict:
    return {
        "categoria": categoria,
        "rotulo": rotulo,
        "titulo": titulo,
        "explicacao": explicacao,
        "como_resolver": como_resolver,
        "acao": {"tipo": acao[0], "label": acao[1]} if acao else None,
    }


def _certificado(_msg) -> dict:
    return _diag(
        "CONFIGURACAO", "Certificado digital",
        "Problema no Certificado Digital",
        "A SEFAZ recusou o certificado digital usado para assinar a nota (vencido, revogado ou de outra empresa).",
        "Confira a validade e o CNPJ do certificado em Centro Fiscal › Configurações e envie o certificado atual.",
        ("CENTRO_FISCAL", "Abrir Centro Fiscal"),
    )


def _duplicidade_539(mensagem) -> dict:
    usada = ler_chave_da_mensagem(mensagem)
    quando = f" em {usada['mes']}/{usada['ano']}" if usada else ""
    qual = f"O nº {usada['numero']} da série {usada['serie']}" if usada else "Este número"
    return _diag(
        "DUPLICIDADE", "cStat 539 · Número já usado",
        "Número Já Usado por Outra Nota",
        f"{qual} já foi emitido{quando} com outra chave — quase sempre por outro sistema que a empresa usava antes do StartBig.",
        "Pergunte ao contador qual foi a última nota emitida nesta série pelo sistema antigo, informe abaixo e reemita. Não inutilize os números para trás: eles podem ter sido usados de verdade.",
    )


TABELA: dict[int, Callable[[Optional[str]], dict]] = {
    204: lambda _m: _diag(
        "DUPLICIDADE", "cStat 204 · Duplicidade",
        "Esta Nota Já Foi Autorizada",
        "A SEFAZ já tem esta mesma nota (mesma chave) autorizada. Ela provavelmente saiu numa tentativa anterior cuja resposta se perdeu.",
        "Consulte o status: o sistema busca a autorização que já existe. Não reemita — isso gastaria outro número.",
        ("RECONSULTAR", "Consultar Status na SEFAZ"),
    ),
    207: lambda _m: _diag(
        "CONFIGURACAO", "cStat 207 · CNPJ do emitente",
        "CNPJ da Sua Empresa Inválido",
        "O CNPJ do emitente (a sua empresa) foi recusado pela SEFAZ.",
        "Confira o CNPJ em Dados da Empresa — só os 14 dígitos, sem erro de digitação.",
        ("CONFIG_FISCAL", "Abrir Dados da Empresa"),
    ),
    208: lambda _m: _diag(
        "CLIENTE", "cStat 208 · CNPJ do cliente",
        "CNPJ do Cliente Inválido",
        "O CNPJ do destinatário (quem comprou) foi recusado pela SEFAZ.",
        "Corrija o CNPJ no cadastro do cliente e emita de novo.",
        ("EDITAR_VENDA", "Corrigir Cliente da Venda"),
    ),
    209: lambda _m: _diag(
        "CONFIGURACAO", "cStat 209 · IE do emitente",
        "Inscrição Estadual da Sua Empresa Inválida",
        "A Inscrição Estadual do emitente (a sua empresa) não confere com o cadastro da SEFAZ.",
        "Confira a Inscrição Estadual em Dados da Empresa com o cartão do Cadesp/SINTEGRA ou com o contador.",
        ("CONFIG_FISCAL", "Abrir Dados da Empresa"),
    ),
    213: lambda _m: _diag(
        "CONFIGURACAO", "cStat 213 · Certificado de outro CNPJ",
        "Certificado Digital de Outra Empresa",
        "O certificado usado para assinar é de um CNPJ diferente do emitente da nota.",
        "Envie o certificado A1 da própria empresa em Centro Fiscal › Configurações.",
        ("CENTRO_FISCAL", "Abrir Centro Fiscal"),
    ),
    237: lambda _m: _diag(
        "CLIENTE", "cStat 237 · CPF do cliente",
        "CPF do Cliente Inválido",
        "O CPF do destinatário (quem comprou) foi recusado pela SEFAZ.",
        "Corrija o CPF no cadastro do cliente e emita de novo.",
        ("EDITAR_VENDA", "Corrigir Cliente da Venda"),
    ),
    **{c: _certificado for c in (280, 281, 282, 283, 284, 285, 286)},
    301: lambda _m: _diag(
        "CONFIGURACAO", "cStat 301 · Uso denegado",
        "Nota Denegada: Irregularidade da Sua Empresa",
        "A SEFAZ registrou a nota e negou o uso por irregularidade fiscal do EMITENTE (a sua empresa). O número foi consumido.",
        "Fale com o contador para regularizar a empresa na SEFAZ. Reemitir não adianta enquanto a irregularidade existir.",
    ),
    302: lambda _m: _diag(
        "CLIENTE", "cStat 302 · Uso denegado",
        "Nota Denegada: Irregularidade do Cliente",
        "A SEFAZ registrou a nota e negou o uso por irregularidade fiscal do DESTINATÁRIO. O número foi consumido.",
        "O cliente precisa regularizar a situação dele na SEFAZ. Se for compra para uso próprio, a nota pode sair no CPF da pessoa — confirme com o contador.",
    ),
    305: lambda _m: _diag(
        "CLIENTE", "cStat 305 · Cliente bloqueado",
        "Cliente Bloqueado na SEFAZ do Estado Dele",
        "O cadastro do destinatário está bloqueado (IE suspensa, inapta ou baixada) no estado dele. Nenhum sistema consegue emitir para ele como está — não é erro do seu cadastro.",
        "Consulte o CNPJ do cliente no CCC (dfe-portal.svrs.rs.gov.br/NFE/CCC) ou no SINTEGRA. Ele precisa regularizar com o contador dele. Se a compra é para uso próprio da pessoa, a nota pode sair no CPF dela.",
        ("EDITAR_VENDA", "Trocar Cliente da Venda"),
    ),
    481: lambda _m: _diag(
        "CONFIGURACAO", "cStat 481 · Regime tributário",
        "Regime Tributário da Sua Empresa Diverge da SEFAZ",
        'O Regime Tributário em Dados da Empresa é diferente do que a SEFAZ tem para o seu CNPJ. O caso mais comum: a empresa é MEI e está cadastrada como "1 - Simples Nacional".',
        'Confira na Consulta Optantes do Simples Nacional se o CNPJ é optante pelo SIMEI. Se for, troque o Regime Tributário para "4 - MEI" em Dados da Empresa e emita de novo.',
        ("CONFIG_FISCAL", "Abrir Dados da Empresa"),
    ),
    539: _duplicidade_539,
}


def diagnosticar(
    cstat: Optional[int], mensagem: Optional[str], motivo: Optional[str] = None
) -> dict:
    """Diagnóstico de uma rejeição. Sempre devolve algo: no pior caso, o genérico com a mensagem da SEFAZ."""
    if cstat and cstat in TABELA:
        return {**TABELA[cstat](mensagem), "cstat": cstat}

    texto = f"{(mensagem or '').lower()} {(motivo or '').lower()}"
    tem = lambda *termos: any(t in texto for t in termos)  # noqa: E731

    # Configuração/certificado só SEM cStat: com código, a nota chegou à SEFAZ
    # — certificado e configuração funcionaram, e "emitente" é só a SEFAZ
    # descrevendo a regra.
    if not cstat and tem("configuração fiscal", "certificado", "emitente", "empresa não possui"):
        return {**_diag(
            "CONFIGURACAO", "Configuração Pendente",
            "Configuração Fiscal da Empresa Incompleta",
            mensagem or "A empresa não possui parâmetros fiscais ativos ou certificado digital configurado para este ambiente.",
            "Acesse as Configurações Fiscais da empresa e cadastre o certificado e séries fiscais.",
            ("CONFIG_FISCAL", "Abrir Configuração Fiscal"),
        ), "cstat": cstat}

    if cstat in (696, 234, 232, 233) or tem("inscrição estadual", "destinatário não vinculada", "indicador de ie"):
        c = cstat or 696
        return {**_diag(
            "CLIENTE", f"cStat {c} · IE Destinatário",
            "Inscrição Estadual do Cliente Inconsistente",
            "A SEFAZ rejeitou porque o cliente está classificado com Inscrição Estadual não vinculada ao CNPJ ou não cadastrada na UF de destino.",
            'Abra a edição da venda, marque o cliente como "Consumidor Não Contribuinte / Isento" ou preencha a IE correta e reemita a nota.',
            ("EDITAR_VENDA", "Editar Cliente da Venda"),
        ), "cstat": c}

    if cstat in (207, 208, 209) or tem("cpf do destinatário", "cnpj do destinatário", "dígito verificador"):
        c = cstat or 208
        return {**_diag(
            "CLIENTE", f"cStat {c} · CPF/CNPJ",
            "Documento (CPF/CNPJ) do Cliente Inválido",
            "O número do CPF ou CNPJ informado para o destinatário é inválido perante a Receita Federal.",
            "Edite os dados da venda vinculando o cliente com CPF ou CNPJ válido.",
            ("EDITAR_VENDA", "Corrigir Cliente da Venda"),
        ), "cstat": c}

    if cstat in (703, 777, 778) or tem("ncm", "nomenclatura comum"):
        c = cstat or 703
        return {**_diag(
            "PRODUTO", f"cStat {c} · NCM Inválido",
            "Código NCM do Produto Inexistente ou Incorreto",
            "Um ou mais produtos vinculados à nota possuem NCM fora da tabela vigente da Receita Federal ou em branco.",
            "Acesse o cadastro de produtos ou o painel de pendências fiscais para informar o NCM válido de 8 dígitos.",
            ("RESOLVER_PRODUTOS", "Resolver Pendências de Produtos"),
        ), "cstat": c}

    if cstat in (508, 528) or tem("csosn", "cfop", "alíquota"):
        c = cstat or 508
        return {**_diag(
            "TRIBUTACAO", f"cStat {c} · Regra Fiscal",
            "Incompatibilidade de Tributação (CSOSN / CFOP)",
            "A regra fiscal (CSOSN/CST) não é compatível com o CFOP de operação ou regime tributário da empresa.",
            "Verifique a configuração fiscal do produto e ajuste o CSOSN (ex: 102 para tributação integral ou 500 para ST).",
            ("RESOLVER_PRODUTOS", "Ajustar Dados do Produto"),
        ), "cstat": c}

    if cstat == 204 or tem("duplicidade"):
        return {**_diag(
            "DUPLICIDADE", "cStat 204 · Duplicidade",
            "Número de NF-e Já Utilizado",
            "Esta numeração e série de nota já foram autorizadas anteriormente na base de dados da SEFAZ.",
            "Consulte o status do documento ou faça a reemissão para gerar a próxima numeração sequencial.",
            ("RECONSULTAR", "Consultar Status na SEFAZ"),
        ), "cstat": 204}

    if cstat in (108, 109, 502) or tem("paralisado", "timeout", "comunicação", "bad gateway"):
        return {**_diag(
            "SEFAZ_INDISPONIVEL", "SEFAZ Temporariamente Instável",
            "Servidores da SEFAZ Temporariamente Indisponíveis",
            "Os servidores da Secretaria da Fazenda estão enfrentando oscilações ou lentidão no momento.",
            "Aguarde alguns minutos e tente reemitir ou consultar o status novamente.",
            ("RECONSULTAR", "Tentar Novamente"),
        ), "cstat": cstat or 108}

    return {**_diag(
        "GENERICO", f"cStat {cstat}" if cstat else "Rejeição SEFAZ",
        f"Rejeição SEFAZ (Código {cstat})" if cstat else "Rejeição na Emissão Fiscal",
        mensagem or motivo or "A SEFAZ rejeitou o lote de emissão deste documento.",
        "Revise os dados da venda, destinatário e tributação dos produtos antes de tentar uma nova emissão.",
        ("EDITAR_VENDA", "Editar Dados da Venda"),
    ), "cstat": cstat}
