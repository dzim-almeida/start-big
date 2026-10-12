/**
 * @fileoverview O que falta para enviar o orçamento (Spec 06B D36).
 *
 * Espelha a regra do backend (06A D13: cliente, nome do projeto e pelo menos
 * um móvel) só para EXPLICAR antes de tentar: botão desabilitado não diz por
 * quê. Quem decide continua sendo o backend (que responde 422 se faltar algo).
 */
import type { OrcamentoDetalhe } from '../schemas/orcamentoDetalhe.schema';

/** Uma pendência e o bloco da tela que a resolve (para o link "ir até lá"). */
export interface PendenciaEnvio {
  texto: string;
  /** id do bloco no editor (`document.getElementById`). */
  bloco: 'titulo-cliente' | 'titulo-ambientes';
}

/** Só o que falta, na ordem da tela. Lista vazia = pode enviar. */
export function pendenciasParaEnviar(detalhe: OrcamentoDetalhe): PendenciaEnvio[] {
  const pendencias: PendenciaEnvio[] = [];
  if (!detalhe.cliente) pendencias.push({ texto: 'Escolha o cliente', bloco: 'titulo-cliente' });
  if (!detalhe.projeto.nome?.trim()) pendencias.push({ texto: 'Dê um nome ao projeto', bloco: 'titulo-cliente' });
  if (!detalhe.ambientes.some((ambiente) => ambiente.moveis.length > 0)) {
    pendencias.push({ texto: 'Adicione pelo menos um móvel', bloco: 'titulo-ambientes' });
  }
  return pendencias;
}
