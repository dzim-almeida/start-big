import { useForm, useFieldArray } from 'vee-validate';
import { customerPJValidationSchema, type AddressFormData } from '@/modules/customers/schemas/customer.schema';
import { DEFAULT_PJ_VALUES, DEFAULT_ADDRESS } from '../constants/modal.constant';

export function useCustomerPJForm() {
  const form = useForm({
    validationSchema: customerPJValidationSchema,
    initialValues: { ...DEFAULT_PJ_VALUES },
  });

  // Campo useFieldArray DEVE ser chamado imediatamente após useForm
  const addresses = useFieldArray<AddressFormData>('enderecos');

  // Definir campos PJ
  const [razao_social] = form.defineField('razao_social');
  const [nome_fantasia] = form.defineField('nome_fantasia');
  const [cnpj] = form.defineField('cnpj');
  const [ie] = form.defineField('ie');
  const [im] = form.defineField('im');
  const [regime_tributario] = form.defineField('regime_tributario');
  const [responsavel] = form.defineField('responsavel');
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
    // Campos específicos PJ
    razao_social,
    nome_fantasia,
    cnpj,
    ie,
    im,
    regime_tributario,
    responsavel,

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

export type CustomerPJFormReturn = ReturnType<typeof useCustomerPJForm>;
