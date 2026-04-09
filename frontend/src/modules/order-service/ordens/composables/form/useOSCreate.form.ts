import { computed } from 'vue';
import { useForm, useFieldArray } from 'vee-validate';

import { orderServiceCreateValidationSchema } from '../../schemas/orderServiceMutate.schema';
import type { OsItemCreateSchemaDataType } from '../../schemas/relationship/osItem.schema';
import type { OrderServiceReadDataType } from '../../schemas/orderServiceQuery.schema';

import type { OSCreateFormContext } from '../../types/context.type';

import { useCreateOrderServiceMutation } from '../request/useOrderServiceCreate.mutate';

import { DEFAULT_OS_CREATE_VALUES, DEFAULT_OS_ITEM_VALUES } from '../../constants/core.constant';


export function useOSCreateForm(opts?: { onSuccess?: (os: OrderServiceReadDataType) => void }): OSCreateFormContext {
  const createMutation = useCreateOrderServiceMutation();

  const { handleSubmit, errors, defineField, resetForm: veeReset } = useForm({
    validationSchema: orderServiceCreateValidationSchema,
    initialValues: { ...DEFAULT_OS_CREATE_VALUES },
  });

  // Campos gerais
  const [prioridade] = defineField('prioridade');
  const [defeito_relatado] = defineField('defeito_relatado');
  const [diagnostico] = defineField('diagnostico');
  const [observacoes] = defineField('observacoes');
  const [desconto] = defineField('desconto');
  const [valor_entrada] = defineField('valor_entrada');
  const [garantia] = defineField('garantia');
  const [data_previsao] = defineField('data_previsao');
  const [senha_aparelho] = defineField('senha_aparelho');
  const [acessorios] = defineField('acessorios');
  const [condicoes_aparelho] = defineField('condicoes_aparelho');

  // Vínculos
  const [cliente_id] = defineField('cliente_id');
  const [funcionario_id] = defineField('funcionario_id');

  // Equipamento (campos nested via dot-notation)
  const [equipamento_tipo_equipamento] = defineField('equipamento.tipo_equipamento');
  const [equipamento_marca] = defineField('equipamento.marca');
  const [equipamento_modelo] = defineField('equipamento.modelo');
  const [equipamento_numero_serie] = defineField('equipamento.numero_serie');
  const [equipamento_imei] = defineField('equipamento.imei');
  const [equipamento_cor] = defineField('equipamento.cor');

  // FieldArray de itens com generic explícito para inferência correta de tipos
  const { fields: itens, push: pushItem, remove: removeItem, update: updateItemField } =
    useFieldArray<OsItemCreateSchemaDataType>('itens');

  const handleAddItem = (item?: Partial<OsItemCreateSchemaDataType>) => {
    pushItem({ ...DEFAULT_OS_ITEM_VALUES, ...item });
  };

  const handleRemoveItem = (index: number) => {
    removeItem(index);
  };

  const handleUpdateItem = (index: number, item: OsItemCreateSchemaDataType) => {
    updateItemField(index, item);
  };

  const resetForm = () => {
    veeReset({ values: { ...DEFAULT_OS_CREATE_VALUES } });
  };

  const onSubmit = handleSubmit((formData) => {
    createMutation.mutate(formData, {
      onSuccess: (data) => {
        resetForm();
        opts?.onSuccess?.(data);
      },
    });
  });

  const isPending = computed(() => createMutation.isPending.value);

  return {
    prioridade,
    defeito_relatado,
    diagnostico,
    observacoes,
    desconto,
    valor_entrada,
    garantia,
    data_previsao,
    senha_aparelho,
    acessorios,
    condicoes_aparelho,
    cliente_id,
    funcionario_id,
    equipamento_tipo_equipamento,
    equipamento_marca,
    equipamento_modelo,
    equipamento_numero_serie,
    equipamento_imei,
    equipamento_cor,
    itens,
    handleAddItem,
    handleRemoveItem,
    handleUpdateItem,
    errors,
    isPending,
    onSubmit,
    resetForm,
  };
}
