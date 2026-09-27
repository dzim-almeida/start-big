/**
 * @fileoverview Layouts de fábrica do envio (plano, fase 5): etiqueta de
 * volume e DANFE Simplificado – Etiqueta.
 *
 * Os dois são uma PILHA de linhas com pesos, escalada para a altura da
 * etiqueta — o mesmo desenho serve um rolo 100 × 150 e uma folha A4 em 4.
 *
 * DANFE Simplificado (NT 2020.004): largura mínima de 55 mm (leitura do
 * código de barras da chave), letra de pelo menos 6 pt, e o conteúdo que a
 * nota exige — chave com código de barras, protocolo, emitente (nome,
 * CNPJ, IE, UF), tipo de operação, número e série, data de emissão,
 * destinatário (nome, CPF/CNPJ, IE, UF) e valor total. O layout do DANFE NÃO
 * é editável: é documento fiscal, não etiqueta de loja.
 */

import type { CampoEtiqueta } from './campos';
import { fontePara } from './layoutAuto';
import { arredondar, type Alinhamento, type ElementoEtiqueta, type PaginaEtiqueta } from './modelo';

type Linha =
  | { texto?: string; campo?: CampoEtiqueta; peso: number; negrito?: boolean; linhas?: number; alinhamento?: Alinhamento; minimoPt?: number }
  | { separador: true }
  | { barras: CampoEtiqueta; peso: number };

const PESO_SEPARADOR = 0.35;

function empilhar(pagina: PaginaEtiqueta, linhas: Linha[]): ElementoEtiqueta[] {
  const margem = Math.max(1.5, Math.min(3, Math.min(pagina.largura_mm, pagina.altura_mm) * 0.03));
  const x = margem;
  const w = arredondar(pagina.largura_mm - 2 * margem, 1);
  const altura = pagina.altura_mm - 2 * margem;
  const pesoTotal = linhas.reduce((soma, l) => soma + ('separador' in l ? PESO_SEPARADOR : l.peso), 0);

  let y = margem;
  const elementos: ElementoEtiqueta[] = [];
  for (const linha of linhas) {
    const h = (altura * ('separador' in linha ? PESO_SEPARADOR : linha.peso)) / pesoTotal;
    if ('separador' in linha) {
      elementos.push({ tipo: 'linha', x, y: arredondar(y + h / 2, 1), w, h: 0, espessura_mm: 0.3 });
    } else if ('barras' in linha) {
      elementos.push({
        tipo: 'barras', x, y: arredondar(y, 1), w, h: arredondar(h * 0.92, 1),
        campo: linha.barras, simbologia: 'CODE128', legenda: false,
      });
    } else {
      const n = linha.linhas ?? 1;
      elementos.push({
        tipo: 'texto', x, y: arredondar(y, 1), w, h: arredondar(h, 1),
        campo: linha.campo, texto: linha.texto,
        fonte_pt: Math.max(linha.minimoPt ?? 4, fontePara(h, n)),
        negrito: linha.negrito ?? false, alinhamento: linha.alinhamento ?? 'esquerda', linhas_max: n,
      });
    }
    y += h;
  }
  return elementos;
}

const rotulo = (texto: string): Linha => ({ texto, peso: 0.55, negrito: true });

/** Etiqueta de volume: destinatário em destaque, remetente discreto, contador grande. */
export function gerarVolume(pagina: PaginaEtiqueta): ElementoEtiqueta[] {
  // Abaixo de ~90 mm de altura a versão completa vira letra miúda: sai a compacta.
  if (pagina.altura_mm < 90) {
    return empilhar(pagina, [
      rotulo('DESTINATÁRIO'),
      { campo: 'destinatario.nome', peso: 1.6, negrito: true },
      { campo: 'destinatario.endereco', peso: 1 },
      { campo: 'destinatario.bairro', peso: 0.9 },
      { campo: 'destinatario.cidade_uf', texto: '', peso: 1.1, negrito: true },
      { campo: 'destinatario.cep', texto: 'CEP ', peso: 0.9 },
      { separador: true },
      { campo: 'remetente.nome', texto: 'Rem.: ', peso: 0.8 },
      { campo: 'volume.rotulo', peso: 1.4, negrito: true, alinhamento: 'centro' },
      { campo: 'envio.origem', peso: 0.8, alinhamento: 'centro' },
    ]);
  }
  return empilhar(pagina, [
    rotulo('REMETENTE'),
    { campo: 'remetente.nome', peso: 0.9, negrito: true },
    { campo: 'remetente.endereco', peso: 0.8 },
    { campo: 'remetente.cidade_uf', peso: 0.8 },
    { campo: 'remetente.telefone', texto: 'Tel. ', peso: 0.8 },
    { separador: true },
    rotulo('DESTINATÁRIO'),
    { campo: 'destinatario.nome', peso: 2.4, negrito: true, linhas: 2 },
    { campo: 'destinatario.endereco', peso: 1.1 },
    { campo: 'destinatario.bairro', peso: 1 },
    { campo: 'destinatario.cidade_uf', peso: 1.4, negrito: true },
    { campo: 'destinatario.cep', texto: 'CEP ', peso: 1.2, negrito: true },
    { campo: 'destinatario.telefone', texto: 'Tel. ', peso: 0.9 },
    { separador: true },
    { campo: 'volume.rotulo', peso: 2, negrito: true, alinhamento: 'centro' },
    { campo: 'envio.peso', texto: 'Peso: ', peso: 0.9, alinhamento: 'centro' },
    { campo: 'envio.observacao', peso: 0.8, alinhamento: 'centro' },
    { separador: true },
    { campo: 'envio.origem', peso: 0.9, negrito: true, alinhamento: 'centro' },
    { campo: 'envio.identificador', texto: 'Ref.: ', peso: 0.8, alinhamento: 'centro' },
    { barras: 'envio.codigo', peso: 2.2 },
    { campo: 'nfe.numero', peso: 0.8, alinhamento: 'centro' },
  ]);
}

/** DANFE Simplificado – Etiqueta: todas as linhas com pelo menos 6 pt (NT 2020.004). */
export function gerarDanfe(pagina: PaginaEtiqueta): ElementoEtiqueta[] {
  const seis = { minimoPt: 6 };
  return empilhar(pagina, [
    { texto: 'DANFE SIMPLIFICADO - ETIQUETA', peso: 1.1, negrito: true, alinhamento: 'centro', ...seis },
    { campo: 'nfe.homologacao', peso: 0.7, negrito: true, alinhamento: 'centro', ...seis },
    { separador: true },
    { texto: 'CHAVE DE ACESSO', peso: 0.6, negrito: true, ...seis },
    { barras: 'nfe.chave', peso: 3 },
    { campo: 'nfe.chave_formatada', peso: 1.3, linhas: 2, alinhamento: 'centro', ...seis },
    { campo: 'nfe.protocolo', texto: 'PROTOCOLO DE AUTORIZAÇÃO: ', peso: 0.8, linhas: 2, ...seis },
    { separador: true },
    { texto: 'EMITENTE', peso: 0.6, negrito: true, ...seis },
    { campo: 'remetente.nome', peso: 0.9, negrito: true, ...seis },
    { campo: 'remetente.documento', peso: 0.75, ...seis },
    { campo: 'remetente.ie', peso: 0.75, ...seis },
    { campo: 'remetente.uf', texto: 'UF: ', peso: 0.75, ...seis },
    { separador: true },
    { texto: 'TIPO DE OPERAÇÃO: 1 - SAÍDA', peso: 0.75, ...seis },
    { campo: 'nfe.numero', peso: 0.9, negrito: true, ...seis },
    { campo: 'nfe.data_emissao', texto: 'DATA DE EMISSÃO: ', peso: 0.75, ...seis },
    { separador: true },
    { texto: 'DESTINATÁRIO', peso: 0.6, negrito: true, ...seis },
    { campo: 'destinatario.nome', peso: 0.9, negrito: true, ...seis },
    { campo: 'destinatario.documento', peso: 0.75, ...seis },
    { campo: 'destinatario.ie', peso: 0.75, ...seis },
    { campo: 'destinatario.uf', texto: 'UF: ', peso: 0.75, ...seis },
    { separador: true },
    { campo: 'nfe.valor_total', texto: 'VALOR TOTAL: ', peso: 1.1, negrito: true, ...seis },
  ]);
}

/** Largura mínima do DANFE Simplificado (NT 2020.004): abaixo disso a chave não é lida. */
export const LARGURA_MINIMA_DANFE_MM = 55;
