/**
 * Formulário de Configurações › Marcenaria (Spec 04B §6.5), em funções puras.
 *
 * A tela mostra % e R$; a API guarda basis points e centavos (PR4). Converter
 * aqui, num lugar só e testado, evita perder centavo: 12,35% vira 1235 bp e
 * volta 12,35%. Arredonda com Math.round, nunca trunca (D10).
 *
 * As regras das listas e os limites são OS MESMOS do backend (Spec 04A §4.1 e
 * §6.4), com as mesmas mensagens: o erro aparece ao digitar, não ao salvar.
 */
import type {
  ConfiguracaoMarcenaria,
  ConfiguracaoMarcenariaUpdate,
  RtModo,
} from '../../../schemas/configuracaoMarcenaria.schema';

/** Valores como a TELA os mostra. Os de custo só existem com permissão (D8). */
export interface FormMarcenaria {
  validade_dias: number;
  prazo_entrega_dias: number;
  etapas_producao: string[];
  checklist_vistoria: string[];
  markup_percentual?: number;   // 90 = 90%
  perda_percentual?: number;    // 10 = 10%
  custo_hora_reais?: number;    // 45.5 = R$ 45,50
  rt_percentual?: number;       // 8 = 8%
  rt_modo?: RtModo;
}

/** Limites das listas (Spec 04A §4.1). */
export const LIMITES_LISTA = {
  etapas: { maxItens: 20, maxCaracteres: 60, nome: 'Etapas de produção' },
  checklist: { maxItens: 30, maxCaracteres: 120, nome: 'Checklist de vistoria' },
} as const;

/** API → tela: basis points viram %, centavos viram R$ (D10). */
export function paraTela(api: ConfiguracaoMarcenaria): FormMarcenaria {
  const form: FormMarcenaria = {
    validade_dias: api.validade_dias,
    prazo_entrega_dias: api.prazo_entrega_dias,
    etapas_producao: [...api.etapas_producao],        // cópia: editar não mexe no cache da query
    checklist_vistoria: [...api.checklist_vistoria],
  };
  if (api.inclui_custos) {                            // só quem vê custo recebe estes campos
    form.markup_percentual = api.markup_padrao_bp / 100;     // 9000 bp -> 90 %
    form.perda_percentual = api.perda_padrao_bp / 100;       // 1000 bp -> 10 %
    form.custo_hora_reais = api.custo_hora_centavos / 100;   // 4550 centavos -> R$ 45,50
    form.rt_percentual = api.rt_padrao_bp / 100;
    form.rt_modo = api.rt_modo;
  }
  return form;
}

/** Tela → corpo do PUT. Só manda custos se a tela os mostrou (D8). */
export function paraApi(form: FormMarcenaria): ConfiguracaoMarcenariaUpdate {
  const corpo: ConfiguracaoMarcenariaUpdate = {
    validade_dias: form.validade_dias,
    prazo_entrega_dias: form.prazo_entrega_dias,
    etapas_producao: form.etapas_producao.map((t) => t.trim()),     // espaços das pontas saem
    checklist_vistoria: form.checklist_vistoria.map((t) => t.trim()),
  };
  if (form.markup_percentual !== undefined) {         // a tela mostrou o bloco de custos
    corpo.markup_padrao_bp = Math.round(form.markup_percentual * 100);          // arredonda, nunca trunca
    corpo.perda_padrao_bp = Math.round((form.perda_percentual ?? 0) * 100);
    corpo.custo_hora_centavos = Math.round((form.custo_hora_reais ?? 0) * 100);
    corpo.rt_padrao_bp = Math.round((form.rt_percentual ?? 0) * 100);
    corpo.rt_modo = form.rt_modo ?? 'MARGEM';
  }
  return corpo;
}

/**
 * Erros de cada item de uma lista (mesma regra do backend): vazio, longo
 * demais ou repetido (sem diferenciar maiúsculas e sem os espaços das pontas).
 * Devolve um texto por item, vazio quando o item está certo.
 */
export function errosDosItens(itens: string[], maxCaracteres: number): string[] {
  const vistos = new Map<string, number>();            // texto normalizado -> primeira posição
  return itens.map((item, indice) => {
    const limpo = item.trim();
    if (!limpo) return 'Preencha ou remova este item.';
    if (limpo.length > maxCaracteres) return `Até ${maxCaracteres} caracteres.`;
    const chave = limpo.toLocaleLowerCase('pt-BR');
    const primeiro = vistos.get(chave);
    if (primeiro !== undefined && primeiro !== indice) return 'Item repetido.';
    vistos.set(chave, indice);
    return '';
  });
}

/** Mensagens dos limites numéricos, iguais às do backend (Spec 04A §4.1). */
export function errosDoFormulario(form: FormMarcenaria): Record<string, string> {
  const erros: Record<string, string> = {};
  const fora = (v: number | undefined, min: number, max?: number) =>
    v === undefined || Number.isNaN(v) || v < min || (max !== undefined && v > max);

  if (fora(form.validade_dias, 1, 365)) erros.validade_dias = 'A validade deve ficar entre 1 e 365 dias.';
  if (fora(form.prazo_entrega_dias, 1, 365)) erros.prazo_entrega_dias = 'O prazo de entrega deve ficar entre 1 e 365 dias.';
  if (form.markup_percentual !== undefined) {          // só quem vê custo edita estes
    if (fora(form.markup_percentual, 0, 1000)) erros.markup_percentual = 'O markup deve ficar entre 0% e 1000%.';
    if (fora(form.perda_percentual, 0, 50)) erros.perda_percentual = 'A perda deve ficar entre 0% e 50%.';
    if (fora(form.custo_hora_reais, 0)) erros.custo_hora_reais = 'O custo por hora não pode ser negativo.';
    if (fora(form.rt_percentual, 0, 30)) erros.rt_percentual = 'O RT deve ficar entre 0% e 30%.';
  }
  for (const [campo, limites] of [['etapas_producao', LIMITES_LISTA.etapas], ['checklist_vistoria', LIMITES_LISTA.checklist]] as const) {
    const itens = form[campo];
    if (itens.length < 1 || itens.length > limites.maxItens) {
      erros[campo] = `${limites.nome}: informe de 1 a ${limites.maxItens} itens.`;
    } else if (errosDosItens(itens, limites.maxCaracteres).some(Boolean)) {
      erros[campo] = `${limites.nome}: corrija os itens marcados.`;
    }
  }
  return erros;
}
