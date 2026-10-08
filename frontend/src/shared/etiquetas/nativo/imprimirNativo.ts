/**
 * @fileoverview Impressão DIRETA na térmica, sem o diálogo do Windows
 * (plano, fase 4): pagina → agrupa as páginas iguais → desenha cada grupo
 * uma vez → gera a linguagem → manda para a impressora (Windows ou rede).
 *
 * Folha (A4/Carta) nunca vem por aqui: é papel de impressora comum, e segue
 * pelo driver mesmo com a térmica configurada.
 */

import { imprimirRaw, imprimirRede, impressaoDisponivel } from '@/shared/services/impressao.service';
import type { ConfigImpressao } from '@/shared/stores/impressao.store';
import { tamanhoDoPapel, type DefinicaoEtiqueta } from '../modelo';
import { paginar, type Posicionada } from '../paginacao';
import type { ValoresEtiqueta } from '../campos';
import { gerarNaLinguagem, type ConfigNativa, type PaginaRasterizada } from './linguagens';
import { rasterizarPagina } from './rasterizar';

export interface TrabalhoNativo {
  definicao: DefinicaoEtiqueta;
  etiquetas: ValoresEtiqueta[];
  pular: number;
  deslocamentoX: number;
  deslocamentoY: number;
}

/** Por que a etiqueta NÃO vai direto (nulo = vai direto). */
export function motivoParaDriver(config: ConfigImpressao, definicao: DefinicaoEtiqueta): string | null {
  if (config.etiqueta_saida === 'driver') return 'driver escolhido';
  if (!impressaoDisponivel()) return 'fora do aplicativo (navegador)';
  if (definicao.pagina.tipo === 'folha') return 'folha é papel de impressora comum';
  return null;
}

/** O que falta configurar para imprimir direto (nulo = pronto). */
export function faltaConfigurar(config: ConfigImpressao): string | null {
  if (config.etiqueta_conexao === 'rede') {
    return config.etiqueta_ip ? null : 'Informe o IP da impressora de etiquetas.';
  }
  return config.etiqueta_impressora ? null : 'Escolha a impressora de etiquetas.';
}

/**
 * Páginas iguais em sequência viram uma só com quantidade. Compara pelo
 * CONTEÚDO (valores + posições), não pela referência: 40 etiquetas do mesmo
 * produto são uma imagem só no cabo.
 */
export function agruparPaginas(paginas: Posicionada<ValoresEtiqueta>[][]): { pagina: Posicionada<ValoresEtiqueta>[]; quantidade: number }[] {
  const grupos: { pagina: Posicionada<ValoresEtiqueta>[]; quantidade: number; chave: string }[] = [];
  for (const pagina of paginas) {
    const chave = JSON.stringify(pagina);
    const ultimo = grupos[grupos.length - 1];
    if (ultimo && ultimo.chave === chave) ultimo.quantidade++;
    else grupos.push({ pagina, quantidade: 1, chave });
  }
  return grupos.map(({ pagina, quantidade }) => ({ pagina, quantidade }));
}

export function gerarBytes(trabalho: TrabalhoNativo, config: ConfigImpressao): Uint8Array {
  if (config.etiqueta_saida === 'driver') throw new Error('Saída "driver" não gera bytes.');
  const papel = tamanhoDoPapel(trabalho.definicao.pagina);
  const cfg: ConfigNativa = {
    dpi: config.etiqueta_dpi,
    larguraMm: papel.largura_mm,
    alturaMm: papel.altura_mm,
    gapMm: config.etiqueta_gap_mm,
    escuridao: config.etiqueta_escuridao,
    girar180: config.etiqueta_girar_180,
    inverter: config.etiqueta_inverter,
  };

  const grupos = agruparPaginas(paginar(trabalho.definicao.pagina, trabalho.etiquetas, trabalho.pular));
  const rasterizadas: PaginaRasterizada[] = grupos.map(({ pagina, quantidade }) => ({
    quantidade,
    bitmap: rasterizarPagina(trabalho.definicao, pagina, {
      dpi: cfg.dpi,
      larguraMm: cfg.larguraMm,
      alturaMm: cfg.alturaMm,
      deslocamentoX: trabalho.deslocamentoX,
      deslocamentoY: trabalho.deslocamentoY,
    }),
  }));
  return gerarNaLinguagem(config.etiqueta_saida, rasterizadas, cfg);
}

export async function imprimirNaTermica(trabalho: TrabalhoNativo, config: ConfigImpressao): Promise<void> {
  const falta = faltaConfigurar(config);
  if (falta) throw new Error(falta);
  const bytes = gerarBytes(trabalho, config);
  if (config.etiqueta_conexao === 'rede') {
    await imprimirRede(config.etiqueta_ip!, config.etiqueta_porta, bytes);
  } else {
    await imprimirRaw(config.etiqueta_impressora!, bytes);
  }
}
