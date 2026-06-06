import { watch } from 'vue';
import { useForm } from 'vee-validate';
import { useSignIn } from './useSignIn';
import { lojaValidationSchema, type LojaFormData } from '../schemas/sign-in.schema';
import { useCepQuery } from './useCepLookup';

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

  watch(cepData, (data) => {
    if (data) {
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
