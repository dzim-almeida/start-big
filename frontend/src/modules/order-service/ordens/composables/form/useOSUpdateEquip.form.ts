import { computed } from 'vue';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import type { Ref } from 'vue';

import { OsEquipUpdateSchema } from '../../schemas/relationship/osEquip.schema';
import type { OsEquipUpdateSchemaDataType } from '../../schemas/relationship/osEquip.schema';

import type { OSUpdateEquipFormContext } from '../../types/context.type';

import { useUpdateEquipOSMutation } from '../request/useOrderServiceUpdate.mutate';


export function useOSUpdateEquipForm(opts: {
  osNumber: Ref<string | null>;
  onSuccess?: () => void;
}): OSUpdateEquipFormContext {
  const equipMutation = useUpdateEquipOSMutation();

  const { handleSubmit, errors, defineField, setValues, resetForm: veeReset } = useForm({
    validationSchema: toTypedSchema(OsEquipUpdateSchema),
  });

  const [tipo_equipamento] = defineField('tipo_equipamento');
  const [marca] = defineField('marca');
  const [modelo] = defineField('modelo');
  const [numero_serie] = defineField('numero_serie');
  const [imei] = defineField('imei');
  const [cor] = defineField('cor');
  const [cliente_id] = defineField('cliente_id');

  const populateForm = (equip: OsEquipUpdateSchemaDataType) => {
    setValues({
      tipo_equipamento: equip.tipo_equipamento,
      marca: equip.marca,
      modelo: equip.modelo,
      numero_serie: equip.numero_serie,
      imei: equip.imei,
      cor: equip.cor,
      cliente_id: equip.cliente_id,
    });
  };

  const onSubmit = handleSubmit((formData) => {
    if (!opts.osNumber.value) return;
    equipMutation.mutate(
      { osNumber: opts.osNumber.value, updatedEquip: formData },
      { onSuccess: () => opts.onSuccess?.() },
    );
  });

  const resetForm = () => {
    veeReset();
  };

  const isPending = computed(() => equipMutation.isPending.value);

  return {
    tipo_equipamento,
    marca,
    modelo,
    numero_serie,
    imei,
    cor,
    cliente_id,
    errors,
    isPending,
    onSubmit,
    resetForm,
    populateForm,
  };
}
