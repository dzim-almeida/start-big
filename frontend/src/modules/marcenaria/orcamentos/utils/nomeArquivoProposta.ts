/**
 * @fileoverview Nome sugerido do PDF da proposta (Spec 07 D5).
 *
 * O diálogo de impressão usa o TÍTULO da página como nome do arquivo no
 * "Salvar como PDF". Sem isto, todo PDF se chamaria "StartBig.pdf" e o
 * vendedor renomearia um por um.
 */
import type { DadosProposta } from './dadosProposta';

/** Caracteres proibidos em nome de arquivo no Windows. */
const PROIBIDOS = /[\\/:*?"<>|]/g;

/** "Proposta ORC-2026-000084 v2 - Studio Arquitetura". */
export function nomeArquivoProposta(dados: Pick<DadosProposta, 'codigo' | 'versao' | 'cliente'>): string {
  const cliente = dados.cliente.nome
    .replace(PROIBIDOS, ' ')   // proibido no Windows vira espaço
    .replace(/\s+/g, ' ')      // espaços repetidos viram um só
    .trim()
    .slice(0, 40)              // nome de empresa longo não estoura o caminho
    .trim();                   // o corte pode deixar um espaço no fim
  const base = `Proposta ${dados.codigo} v${dados.versao}`;
  return cliente ? `${base} - ${cliente}` : base;   // prévia sem cliente: só o código
}
