import { watch } from 'vue';
import { useForm } from 'vee-validate';
import { useSignIn } from './useSignIn';
import { lojaValidationSchema, type LojaFormData } from '../schemas/sign-in.schema';
import { useCepQuery } from './useCepLookup';
import { unmaskCep } from '@/shared/utils/unmask.utils';

/**
 * Composable para o formulário da loja + endereço (Passo 1)
 */
export function useLojaForm() {
  const { signInData, nextStep, updateLojaData } = useSignIn();

  const { handleSubmit, errors, defineField, submitCount, setValues } =
    useForm<LojaFormData>({
      validationSchema: lojaValidationSchema,
      initialValues: {
        nomeLoja: signInData.loja.nomeLoja,
        segmento: signInData.loja.segmento as LojaFormData['segmento'] || undefined,
        celular: signInData.loja.celular,
        emailLoja: signInData.loja.emailLoja,
        telefone: signInData.loja.telefone,
        cep: signInData.loja.cep,
        logradouro: signInData.loja.logradouro,
        numero: signInData.loja.numero,
        complemento: signInData.loja.complemento,
        bairro: signInData.loja.bairro,
        cidade: signInData.loja.cidade,
        estado: signInData.loja.estado,
      },
    });

  // Campos loja
  const [nomeLoja] = defineField('nomeLoja');
  const [segmento] = defineField('segmento');
  const [celular] = defineField('celular');
  const [emailLoja] = defineField('emailLoja');
  const [telefone] = defineField('telefone');

  // Campos endereço
  const [cep] = defineField('cep');
  const [logradouro] = defineField('logradouro');
  const [numero] = defineField('numero');
  const [complemento] = defineField('complemento');
  const [bairro] = defineField('bairro');
  const [cidade] = defineField('cidade');
  const [estado] = defineField('estado');

  // CEP auto-fill
  const { data: cepData, isLoading: cepIsLoading, isError: cepIsError } = useCepQuery(cep);

  // CEP que o formulário já abriu preenchido (veio da conta na nuvem, ou a
  // pessoa voltou de uma etapa). A busca do CEP roda sozinha ao abrir a tela,
  // e sem esta trava ela apagava o número e o complemento já preenchidos.
  const cepCarregado = unmaskCep(signInData.loja.cep || '');

  watch(cepData, (data) => {
    // Mesmo CEP do que já estava preenchido, com endereço: o endereço salvo
    // vale mais que o da consulta. Só um CEP NOVO preenche os campos.
    const mesmoCepJaPreenchido =
      cepCarregado !== '' && unmaskCep(cep.value || '') === cepCarregado && !!logradouro.value;
    if (data && !mesmoCepJaPreenchido) {
      setValues({
        cep: cep.value,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
        numero: '',
        complemento: data.complemento || '',
      }, false);
    }
  });

  const onSubmit = handleSubmit((formData) => {
    updateLojaData({
      nomeLoja: formData.nomeLoja,
      segmento: formData.segmento,
      celular: formData.celular,
      emailLoja: formData.emailLoja,
      telefone: formData.telefone || '',
      cep: formData.cep,
      logradouro: formData.logradouro,
      numero: formData.numero || '',
      complemento: formData.complemento || '',
      bairro: formData.bairro,
      cidade: formData.cidade,
      estado: formData.estado,
    });
    nextStep();
  });

  return {
    // Campos loja
    nomeLoja,
    segmento,
    celular,
    emailLoja,
    telefone,

    // Campos endereço
    cep,
    logradouro,
    numero,
    complemento,
    bairro,
    cidade,
    estado,

    // Estados
    errors,
    cepIsLoading,
    cepIsError,

    // Métodos
    onSubmit,
    submitCount,
  };
}
