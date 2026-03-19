export type { OrderServiceReadDataType as OrdemServicoRead } from '../schemas/orderServiceQuery.schema';
export type { OrderServiceReadDataType as OrdemServicoListRead } from '../schemas/orderServiceQuery.schema';
export type { OsStatusEnumDataType as OrdemServicoStatus } from '../schemas/enums/osEnums.schema';

export interface OrdemServicoItemCreate {
  tipo?: string;
  nome?: string;
  descricao?: string;
  servico_id?: number | string;
  produto_id?: number | string;
  item_id?: number;
  quantidade: number;
  valor_unitario: number;
  unidade_medida?: string;
}
