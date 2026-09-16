import type { SegmentWorkType } from './segmentDefinition.type';

/**
 * O texto miúdo embaixo do nome do cliente na lista de OS — a coluna
 * "Cliente / Objeto" diz que TIPO de coisa entrou na loja.
 *
 * Até aqui a lista imprimia `objeto.tipo_equipamento` cru. Isso serve a quem
 * preenche esse campo: informática (o atendente digita "Notebook") e oficina
 * (o backend deduz "Veículo" pela placa). Segmento que declara TIPOS DE
 * TRABALHO (serigrafia, marcenaria) grava o tipo em `os.dados_adicionais.
 * tipo_trabalho` e nunca preenche `tipo_equipamento` — então o backend caía no
 * fallback "Equipamento", e a lista da serigrafia dizia "Equipamento" numa
 * camisa. Ninguém reportou; a marcenaria fez aparecer.
 *
 * A regra: se a OS tem tipo de trabalho e o contrato conhece o id, o rótulo
 * do tipo ("Móveis planejados", "Camisa (pintura)"). Senão, EXATAMENTE o que
 * era antes — é o que mantém oficina e informática intocadas, e a função é
 * pura para isso poder ser provado sem montar tela.
 */
export function subtituloObjetoLista(
  os: {
    dados_adicionais?: Record<string, unknown> | null;
    objeto?: { tipo_equipamento?: string | null } | null;
  },
  tipos: readonly SegmentWorkType[],
): string {
  const id = os.dados_adicionais?.tipo_trabalho;
  if (typeof id === 'string' && id) {
    const tipo = tipos.find((t) => t.id === id);
    if (tipo?.label) return tipo.label;
  }
  return os.objeto?.tipo_equipamento ?? '';
}
