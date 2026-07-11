// ---------------------------------------------------------------------------
// Contrato de definição de campos por segmento (metadados vindos do backend).
// Fonte: GET /ordens-servico/definicao-campos (app/core/segmentos.py).
//
// O frontend renderiza os campos/vistoria a partir deste contrato, permitindo
// que novos segmentos (ex: oficina_moto) funcionem sem alterar o frontend.
// ---------------------------------------------------------------------------

/** Tipo de widget de um campo dinâmico. */
export type SegmentFieldType = 'texto' | 'numero' | 'inteiro' | 'opcao' | 'booleano';

/** Onde o campo é persistido: no objeto (veículo) ou na OS (check-in). */
export type SegmentFieldScope = 'objeto' | 'os';

/** Descrição de um campo dinâmico do segmento. */
export interface SegmentField {
  nome: string;
  label: string;
  tipo: SegmentFieldType;
  obrigatorio: boolean;
  escopo: SegmentFieldScope;
  /** Presente quando `tipo === 'opcao'`. */
  opcoes?: string[];
}

/** Campo identificador principal do objeto (ex: placa mapeada em numero_serie). */
export interface SegmentIdentifier {
  nome: string;
  label: string;
  /** Regex de validação (ex: placa). `null` quando não há. */
  regex: string | null;
}

/** Grupo da vistoria de inspeção; cada item é avaliado por um dos `estados`. */
export interface SegmentInspectionGroup {
  titulo: string;
  estados: string[];
  itens: string[];
}

/** Definição completa dos campos de um segmento com regras dedicadas. */
export interface SegmentDefinition {
  segmento: string;
  rotulo_objeto_singular: string;
  rotulo_objeto_plural: string;
  identificador: SegmentIdentifier;
  veiculo: SegmentField[];
  checkin: SegmentField[];
  acessorios: string[];
  vistoria: SegmentInspectionGroup[];
}

/** Resposta do endpoint de definição de campos. */
export interface SegmentDefinitionResponse {
  segmento: string | null;
  tem_definicao: boolean;
  /** `null` para segmentos sem definição dedicada (ex: mercado, informática). */
  definicao: SegmentDefinition | null;
}
