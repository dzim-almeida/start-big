import { useForm, useFieldArray } from 'vee-validate';
import { customerPFValidationSchema, type AddressFormData } from '@/modules/customers/schemas/customer.schema';
import { DEFAULT_PF_VALUES, DEFAULT_ADDRESS } from '../constants/modal.constant';

export function useCustomerPFForm() {
  const form = useForm({
    validationSchema: customerPFValidationSchema,
    initialValues: { ...DEFAULT_PF_VALUES },
  });

  // Campo useFieldArray DEVE ser chamado imediatamente após useForm
  // para garantir binding correto via injectWithSelf
  const addresses = useFieldArray<AddressFormData>('enderecos');

  // Definir campos PF
  const [nome] = form.defineField('nome');
  const [cpf] = form.defineField('cpf');
  const [rg] = form.defineField('rg');
  const [genero] = form.defineField('genero');
  const [data_nascimento] = form.defineField('data_nascimento');
  const [email] = form.defineField('email');
  const [celular] = form.defineField('celular');
  const [telefone] = form.defineField('telefone');
  const [observacoes] = form.defineField('observacoes');

  function handleAddAddress() {
    addresses.push({ ...DEFAULT_ADDRESS });
  }

  function handleRemoveAddress(index: number) {
    addresses.remove(index);
  }

  return {
    // Campos específicos PF
    nome,
    cpf,
    rg,
    genero,
    data_nascimento,

    // Campos comuns
    email,
    celular,
    telefone,
    observacoes,

    // Endereços
    enderecos: addresses.fields,
    handleAddAddress,
    handleRemoveAddress,

    // Utilitários do formulário
    errors: form.errors,
    submitCount: form.submitCount,
    values: form.values,
    handleSubmit: form.handleSubmit,
    setValues: form.setValues,
    resetForm: form.resetForm,
  };
}

export type CustomerPFFormReturn = ReturnType<typeof useCustomerPFForm>;
