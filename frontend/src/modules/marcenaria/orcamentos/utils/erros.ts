/**
 * @fileoverview Leitura dos erros da API do orçamento (Spec 06A §6.9, Revisão 1).
 *
 * Os 409 e o 422 do motor chegam com `detail = { codigo, mensagem, campo? }`;
 * a tela decide pelo CÓDIGO (dois 409 pedem reações diferentes) e mostra o erro
 * do motor embaixo do CAMPO certo. O texto do 409 nunca é comparado.
 */
import axios from 'axios';

import { getErrorMessage } from '@/shared/utils/error.utils';

/** O `detail` da resposta, se for o objeto estruturado. */
function detalheEstruturado(erro: unknown): Record<string, unknown> | null {
  if (!axios.isAxiosError(erro)) return null;
  const detail = (erro.response?.data as { detail?: unknown } | undefined)?.detail;
  return detail && typeof detail === 'object' && !Array.isArray(detail) ? (detail as Record<string, unknown>) : null;
}

/** 'REVISAO_DESATUALIZADA', 'STATUS_NAO_EDITAVEL', 'CALCULO_INVALIDO'... ou null. */
export function codigoDoErro(erro: unknown): string | null {
  const detalhe = detalheEstruturado(erro);
  if (detalhe && typeof detalhe.codigo === 'string') return detalhe.codigo;
  // Alguns erros vêm só com o texto (ex.: o PIN do cancelamento de OS).
  if (axios.isAxiosError(erro)) {
    const texto = (erro.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof texto === 'string' && /^[A-Z_]+$/.test(texto)) return texto;
  }
  return null;
}

/** O campo do 422 do motor ('desconto', 'sinal', 'markup', 'perda', 'custo_hora') ou null. */
export function campoDoErro(erro: unknown): string | null {
  const detalhe = detalheEstruturado(erro);
  return detalhe && typeof detalhe.campo === 'string' ? detalhe.campo : null;
}

/** A frase para o usuário (qualquer formato de erro). */
export function mensagemDoErro(erro: unknown, padrao = 'Não foi possível concluir. Tente novamente.'): string {
  if (axios.isAxiosError(erro)) return getErrorMessage(erro, padrao);
  return padrao;
}

/** Erro de rede (sem resposta do servidor): vale tentar de novo (06B D9). */
export function ehErroDeRede(erro: unknown): boolean {
  return axios.isAxiosError(erro) && !erro.response;
}

/** Status HTTP da resposta, se houver. */
export function statusDoErro(erro: unknown): number | null {
  return axios.isAxiosError(erro) ? erro.response?.status ?? null : null;
}
