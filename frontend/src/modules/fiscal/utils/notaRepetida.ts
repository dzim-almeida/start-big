/**
 * @fileoverview A "nota repetida" da franquia fiscal (409 NOTA_DUPLICADA_SUSPEITA):
 * a plataforma não emitiu porque a mesma nota, com outra ref, foi autorizada há
 * menos de 1 hora. Nada saiu para a SEFAZ e nenhum número foi gasto; o operador
 * decide e, se for mesmo outra venda, reenvia com a confirmação.
 *
 * Um lugar só para reconhecer o caso — NF-e, NFC-e e NFS-e (docs/nfse-fase2-plano.md, G2).
 */
import type { AxiosError } from 'axios';

export const CODIGO_NOTA_REPETIDA = 'NOTA_DUPLICADA_SUSPEITA';

type Detalhe = { detail?: { codigo?: string; mensagem?: string } };

export function codigoDoErro(error: unknown): string | undefined {
  return (error as AxiosError<Detalhe>)?.response?.data?.detail?.codigo;
}

export function ehNotaRepetida(error: unknown): boolean {
  return codigoDoErro(error) === CODIGO_NOTA_REPETIDA;
}

export function mensagemNotaRepetida(error: unknown): string {
  return (
    (error as AxiosError<Detalhe>)?.response?.data?.detail?.mensagem ??
    'Esta nota é igual a outra emitida há pouco.'
  );
}
