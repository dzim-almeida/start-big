/**
 * @fileoverview Serviço de verificação de licença.
 * Usa axios puro (sem interceptor 401) pois executa antes da autenticação.
 */

import axios from 'axios';
import { getApiBaseUrl } from '@/api/backendUrl';
import { obterHwid } from '@/shared/services/system/hwid.service';

export interface LicencaStatusResponse {
  status: 'online_valid' | 'offline_valid';
  dias_restantes?: number;
  /** Só presente quando a licença é um trial. Ausente = licença paga. */
  trial?: boolean;
  /**
   * O plano venceu, mas o gateway ainda está re-tentando o cartão.
   *
   * NÃO confundir com "vencida": aqui o sistema continua liberado, e o aviso
   * é para o dono saber que a cobrança falhou — cartão trocado, limite, banco
   * recusando. Só acontece em assinatura no cartão; no PIX, não pagar foi uma
   * escolha e a licença trava na hora.
   */
  em_carencia?: boolean;
  /** Dias que ainda faltam da carência. */
  dias_restantes_carencia?: number | null;
  /**
   * Módulos contratados, lidos do JWT assinado da licença.
   *
   * AUSENTE (`undefined`/`null`) = o token não carrega a claim, ou o backend é
   * anterior a ela. Lista VAZIA = a plataforma ainda não cadastrou módulo
   * nenhum. Os dois significam "não sei" e liberam; só uma lista PREENCHIDA
   * sem o identificador é que bloqueia.
   *
   * Não interprete nada disto aqui — quem cuida da regra é a `modulos.store`.
   */
  modulos?: string[] | null;
  /**
   * Aviso para o dono (LIC-02/LIC-08). Hoje só "relogio_recuou": o relógio do
   * computador voltou no tempo. Não bloqueia nada (D-05); a tela mostra uma faixa.
   */
  aviso?: 'relogio_recuou' | null;
  /**
   * true = os dias restantes foram calculados neste computador (sem internet),
   * e não informados pela API. A tela mostra "(estimado, sem internet)".
   */
  estimativa?: boolean;
}

export interface LicencaErroResponse {
  codigo: string;
  mensagem: string;
}

/**
 * Lê o código e a mensagem de um erro da licença, num lugar só (LIC-03 §6.4, D-29).
 *
 * O backend manda `{ error, detail: { codigo, mensagem } }`. Também aceitamos o
 * código no topo do corpo, porque um caixa atualizado pode falar com um
 * servidor ainda na versão antiga. Erro sem resposta (rede) volta sem código.
 */
export function lerErroDaLicenca(erro: unknown): { codigo?: string; mensagem?: string } {
  // `?.` (encadeamento opcional) devolve undefined em vez de quebrar quando
  // algum pedaço não existe (ex.: erro de rede não tem `response`).
  const dados = (erro as { response?: { data?: Record<string, unknown> } })?.response?.data ?? {};
  // Se `detail` é um objeto, o código está dentro dele; senão, no próprio corpo.
  const detalhe = (typeof dados.detail === 'object' && dados.detail !== null ? dados.detail : dados) as {
    codigo?: string;
    mensagem?: string;
  };
  return { codigo: detalhe.codigo, mensagem: detalhe.mensagem };
}

/**
 * Texto fixo, em português, para cada código de erro da licença (D-16).
 *
 * A tela NUNCA mostra o texto da exceção do servidor: ela olha o código e
 * mostra a frase daqui. Todo código das specs LIC-01 a LIC-09 que pode chegar
 * a uma tela tem uma linha aqui (o teste CT-17 confere).
 */
export const MENSAGENS_DE_CODIGO: Record<string, string> = {
  CREDENCIAIS_INVALIDAS: 'E-mail ou senha da conta StartBig incorretos.',
  SENHA_NAO_CONFIGURADA: 'Sua conta ainda não tem senha. Use "Reenviar link" para criar uma.',
  MUITAS_TENTATIVAS: 'Muitas tentativas. Aguarde alguns minutos e tente de novo.',
  AGUARDANDO_CONFIRMACAO_EMAIL: 'Confirme o link enviado ao seu e-mail antes de entrar.',
  CONFIRMACAO_NECESSARIA:
    'Enviamos as instruções para o seu e-mail. Depois de confirmar, entre com o seu e-mail e senha.',
  CONTA_RECUSADA: 'A StartBig recusou o acesso desta conta. Fale com o suporte.',
  SEM_LICENCA_ATIVA: 'Nenhuma licença ativa foi encontrada para este e-mail.',
  LICENCA_VENCIDA: 'Sua licença está vencida. Renove a assinatura para continuar.',
  LICENCA_TRANSFERIDA: 'Esta licença foi transferida para outro computador.',
  LICENCA_HWID_REVOGADO: 'Este computador não é mais o servidor desta licença.',
  LICENCA_DE_OUTRA_CONTA: 'Esta conta não é dona da licença deste computador.',
  // A chave que não abre aqui responde LICENCA_DE_OUTRA_MAQUINA (LIC-01, Revisão 3);
  // CHAVE_ATIVACAO_ILEGIVEL não é emitido, mas a linha fica por segurança.
  LICENCA_DE_OUTRA_MAQUINA:
    'A licença deste banco foi ativada em outro computador. Entre de novo com a conta StartBig.',
  CHAVE_ATIVACAO_ILEGIVEL:
    'A licença deste banco foi ativada em outro computador. Entre de novo com a conta StartBig.',
  TOKEN_DE_OUTRA_LICENCA:
    'A licença guardada não confere com este computador. Entre de novo com a conta StartBig.',
  TOKEN_ILEGIVEL:
    'Não foi possível ler a licença guardada. Conecte-se à internet ou entre de novo com a conta StartBig.',
  CHAVE_CORROMPIDA: 'A chave de segurança da licença está danificada. Conecte-se à internet para recuperá-la.',
  COFRE_INDISPONIVEL: 'O Windows não permitiu acessar o cofre da licença. Reinicie o computador e tente de novo.',
  BACKUP_INEXISTENTE: 'Não há backup na nuvem para esta licença.',
  BACKUP_CHAVE_INVALIDA: 'O backup da nuvem não abre com a chave desta licença.',
  BACKUP_MAQUINA_REVOGADA:
    'Este computador não é mais o servidor desta licença. O backup na nuvem só funciona no servidor atual.',
  BACKUP_HWID_AUSENTE: 'A licença guardada é antiga. Conecte-se à internet para renová-la e tente de novo.',
  BACKUP_TRIAL_LIMITE: 'O período de teste dá direito a um backup na nuvem, e ele já foi feito.',
  TRIAL_BACKUP_USADO: 'O backup na nuvem do período de teste já foi usado. Assine para ter backups contínuos.',
  RESTAURACAO_JA_PENDENTE: 'Uma restauração já está pendente. Reinicie o sistema para aplicá-la.',
  DOCUMENTO_TRAVADO: 'O CPF ou CNPJ do titular não pode ser alterado pelo sistema. Fale com o suporte.',
  FORA_DA_REDE_DA_LOJA: 'Este computador não está na rede da loja. Conecte-o à mesma rede do servidor.',
  RESPOSTA_INVALIDA: 'A StartBig respondeu de um jeito inesperado. Tente de novo em instantes.',
  SEM_CONEXAO: 'Sem conexão com a StartBig. Verifique a internet.',
  NUVEM_INDISPONIVEL: 'O servidor da StartBig não respondeu. Tente de novo em alguns minutos.',
};

/** Mensagem do código, ou a genérica se o código não estiver na tabela. */
export function mensagemDoCodigo(codigo: string | undefined): string {
  // `??` usa o valor da direita quando o da esquerda é null/undefined
  return MENSAGENS_DE_CODIGO[codigo ?? ''] ?? 'Não foi possível concluir agora. Tente de novo em instantes.';
}

/**
 * Códigos de "a licença deste banco foi ativada em outro computador".
 *
 * Na prática é troca de servidor (o banco foi copiado), e a saída é uma só:
 * a tela de transferência. `CLONAGEM_DETECTADA` é o nome antigo — continua
 * aqui porque um caixa atualizado pode falar com um servidor ainda na versão
 * anterior.
 */
const CODIGOS_LICENCA_DE_OUTRA_MAQUINA = ['LICENCA_DE_OUTRA_MAQUINA', 'CLONAGEM_DETECTADA'];

export function ehLicencaDeOutraMaquina(codigo: string | undefined | null): boolean {
  return !!codigo && CODIGOS_LICENCA_DE_OUTRA_MAQUINA.includes(codigo);
}

/**
 * Verifica o status da licença via GET /licenca/status.
 * Endpoint público (sem autenticação).
 */
export async function verificarLicenca(): Promise<LicencaStatusResponse> {
  const { data } = await axios.get<LicencaStatusResponse>(
    `${getApiBaseUrl()}/licenca/status`,
  );
  return data;
}

/**
 * Desconecta a sessão da licença na API StartBig.
 * Chamado no logout e no encerramento da aplicação.
 * Nunca propaga erro — falhas são silenciosas.
 */
export async function desconectarLicenca(): Promise<void> {
  try {
    const hwid = await obterHwid();
    await axios.post(
      `${getApiBaseUrl()}/licenca/desconectar?hwid=${encodeURIComponent(hwid)}`,
      null,
      { signal: AbortSignal.timeout(2000) },
    );
  } catch {
    // Silencioso — não bloqueia o fluxo de encerramento
  }
}

/**
 * Retorna a URL completa do endpoint de desconexão com HWID.
 * Usada pelo sendBeacon no beforeunload (fecho de janela).
 *
 * @param hwid - Hardware ID do terminal (deve ser pré-cacheado, pois
 *               beforeunload é síncrono e não pode aguardar async).
 */
export function getDesconectarUrl(hwid: string): string {
  return `${getApiBaseUrl()}/licenca/desconectar?hwid=${encodeURIComponent(hwid)}`;
}
