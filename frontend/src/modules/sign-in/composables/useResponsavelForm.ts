import { useForm } from 'vee-validate';
import { useSignIn } from './useSignIn';
import { responsavelValidationSchema, type ResponsavelFormData } from '../schemas/sign-in.schema';
import type { TipoPessoa } from '../types/sign-in.types';

/**
 * Composable para o formulário do responsável (Passo 2)
 */
export function useResponsavelForm() {
  const { signInData, nextStep, updateResponsavelData } = useSignIn();

  const { handleSubmit, errors, defineField, submitCount, setFieldValue, resetField } =
    useForm<ResponsavelFormData>({
      validationSchema: responsavelValidationSchema,
      initialValues: {
        tipoPessoa: signInData.responsavel.tipoPessoa,
        nomeResponsavel: signInData.responsavel.nomeResponsavel,
        cpf: signInData.responsavel.cpf,
        rg: signInData.responsavel.rg,
        genero: signInData.responsavel.genero || undefined,
        dataNascimento: signInData.responsavel.dataNascimento,
        razaoSocial: signInData.responsavel.razaoSocial,
        cnpj: signInData.responsavel.cnpj,
        nomeFantasiaPJ: signInData.responsavel.nomeFantasiaPJ,
        inscricaoEstadual: signInData.responsavel.inscricaoEstadual,
        inscricaoMunicipal: signInData.responsavel.inscricaoMunicipal,
        regimeTributario: signInData.responsavel.regimeTributario || undefined,
        celularResponsavel: signInData.responsavel.celularResponsavel,
        emailResponsavel: signInData.responsavel.emailResponsavel,
      },
    });

  const [tipoPessoa] = defineField('tipoPessoa');
  const [nomeResponsavel] = defineField('nomeResponsavel');
  // PF
  const [cpfField] = defineField('cpf');
  const [rg] = defineField('rg');
  const [genero] = defineField('genero');
  const [dataNascimento] = defineField('dataNascimento');
  // PJ
  const [razaoSocial] = defineField('razaoSocial');
  const [cnpj] = defineField('cnpj');
  const [nomeFantasiaPJ] = defineField('nomeFantasiaPJ');
  const [inscricaoEstadual] = defineField('inscricaoEstadual');
  const [inscricaoMunicipal] = defineField('inscricaoMunicipal');
  const [regimeTributario] = defineField('regimeTributario');
  // Contato
  const [celularResponsavel] = defineField('celularResponsavel');
  const [emailResponsavel] = defineField('emailResponsavel');

  function handleTipoPessoaChange(tipo: TipoPessoa): void {
    setFieldValue('tipoPessoa', tipo);
    // Limpar campos do tipo anterior (nome é compartilhado, mantém)
    if (tipo === 'PF') {
      // Limpar campos PJ
      setFieldValue('razaoSocial', '');
      setFieldValue('cnpj', '');
      setFieldValue('nomeFantasiaPJ', '');
      setFieldValue('inscricaoEstadual', '');
      setFieldValue('inscricaoMunicipal', '');
      setFieldValue('regimeTributario', undefined);
    } else {
      // Limpar campos PF
      setFieldValue('cpf', '');
      setFieldValue('rg', '');
      setFieldValue('genero', undefined);
      setFieldValue('dataNascimento', '');
    }
  }

  const onSubmit = handleSubmit((formData) => {
    updateResponsavelData({
      tipoPessoa: formData.tipoPessoa,
      nomeResponsavel: formData.nomeResponsavel,
      cpf: formData.cpf || '',
      rg: formData.rg || '',
      genero: formData.genero || '',
      dataNascimento: formData.dataNascimento || '',
      razaoSocial: formData.razaoSocial || '',
      cnpj: formData.cnpj || '',
      nomeFantasiaPJ: formData.nomeFantasiaPJ || '',
      inscricaoEstadual: formData.inscricaoEstadual || '',
      inscricaoMunicipal: formData.inscricaoMunicipal || '',
      regimeTributario: formData.regimeTributario || '',
      celularResponsavel: formData.celularResponsavel || '',
      emailResponsavel: formData.emailResponsavel || '',
    });
    nextStep();
  });

  return {
    tipoPessoa,
    nomeResponsavel,
    cpfField,
    rg,
    genero,
    dataNascimento,
    razaoSocial,
    cnpj,
    nomeFantasiaPJ,
    inscricaoEstadual,
    inscricaoMunicipal,
    regimeTributario,
    celularResponsavel,
    emailResponsavel,

    errors,

    onSubmit,
    submitCount,
    handleTipoPessoaChange,
  };
}
