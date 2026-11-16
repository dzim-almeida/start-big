/**
 * @fileoverview Móveis × volumes → os valores de cada etiqueta (Spec 14 §5).
 *
 * Uma etiqueta por VOLUME (D1): 3 aéreos = 3 volumes, um guarda-roupa que sai
 * em 5 caixas = 5. Só transforma dados: quem desenha é o motor
 * (`shared/etiquetas`). Nenhum preço entra aqui (D10).
 */
import type { ValoresEtiqueta } from '@/shared/etiquetas/campos';
import { etiquetasPorPagina, type PaginaEtiqueta } from '@/shared/etiquetas/modelo';
import { formatarMedidasProposta } from '@/modules/marcenaria/orcamentos/utils/dadosProposta';

/** O que a etiqueta precisa do móvel (a `MovelProducao` da 12A satisfaz). */
export interface MovelParaEtiqueta {
  nome: string;
  ambiente: string;
  medidas: { largura_mm: number | null; altura_mm: number | null; profundidade_mm: number | null };
}

/** O que é igual em todas as etiquetas da OS. */
export interface DadosComunsEtiqueta {
  os: string;               // "OS-2026-000512"
  projeto: string;          // "PRJ-000031"
  enderecoObra: string;
  cliente: string;
  empresa: string;
}

/** Os valores de UMA etiqueta = um volume de um móvel (D1). */
export function valoresDoVolumeDoMovel(
  movel: MovelParaEtiqueta, volume: number, totalVolumes: number, comum: DadosComunsEtiqueta,
): ValoresEtiqueta {
  return {
    'os.numero': comum.os,
    'projeto.codigo': comum.projeto,
    'projeto.endereco_obra': comum.enderecoObra,
    'cliente.nome': comum.cliente,
    'movel.nome': movel.nome,
    'movel.ambiente': movel.ambiente,
    // "L 700 × A 2200 × P 600 mm": o mesmo formato da proposta (07).
    'movel.medidas': formatarMedidasProposta(movel.medidas.largura_mm, movel.medidas.altura_mm, movel.medidas.profundidade_mm),
    'volume.contador': `${volume}/${totalVolumes}`,                  // o mesmo formato do envio
    'volume.rotulo': `VOLUME ${volume} DE ${totalVolumes}`,
    'empresa.nome': comum.empresa,
  };
}

/** Móveis escolhidos × volumes → etiquetas, na ordem: ambiente, móvel, volume. */
export function montarEtiquetas(
  moveis: Array<{ movel: MovelParaEtiqueta; volumes: number }>, comum: DadosComunsEtiqueta,
): ValoresEtiqueta[] {
  return moveis.flatMap(({ movel, volumes }) =>
    Array.from({ length: volumes }, (_, i) => valoresDoVolumeDoMovel(movel, i + 1, volumes, comum)));
}

/** Volumes de 1 a 50 por móvel (§6): fora disso, o mais perto que vale. */
export function volumesValidos(valor: number): number {
  if (!Number.isFinite(valor)) return 1;
  return Math.min(50, Math.max(1, Math.round(valor)));
}

/**
 * "8 etiquetas · 2 folhas" (§6): quantas folhas, contando as posições já
 * usadas da primeira (D5). No rolo não há folha: só a contagem.
 */
export function resumoDaImpressao(pagina: PaginaEtiqueta, etiquetas: number, pular: number): string {
  const texto = `${etiquetas} ${etiquetas === 1 ? 'etiqueta' : 'etiquetas'}`;
  if (pagina.tipo !== 'folha' || !etiquetas) return texto;
  const porFolha = etiquetasPorPagina(pagina);
  const folhas = Math.ceil((etiquetas + Math.min(pular, porFolha - 1)) / porFolha);
  return `${texto} · ${folhas} ${folhas === 1 ? 'folha' : 'folhas'}`;
}

// --- O modelo escolhido fica lembrado neste computador (D11) ------------------------------
const CHAVE_MODELO = 'startbig.marcenaria.etiqueta_modelo';

/** A chave do último modelo usado (`preset:movel-...`), ou null. Sem armazenamento: null. */
export function modeloLembrado(): string | null {
  try {
    return window.localStorage.getItem(CHAVE_MODELO);
  } catch {
    return null;                                     // modo privado / armazenamento bloqueado
  }
}

export function lembrarModelo(chave: string): void {
  try {
    window.localStorage.setItem(CHAVE_MODELO, chave);
  } catch {
    // Sem armazenamento: na próxima vez volta ao padrão (A4 em 4). Nada quebra.
  }
}
