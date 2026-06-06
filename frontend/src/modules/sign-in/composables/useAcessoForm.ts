import { useForm } from 'vee-validate';
import { useSignIn } from './useSignIn';
import { acessoValidationSchema, type AcessoFormData } from '../schemas/sign-in.schema';

/**
 * Composable para o formulário de dados de acesso (Passo 3)
 */
export function useAcessoForm() {
  const { signInData, nextStep, updateAcessoData } = useSignIn();

  const { handleSubmit, errors, defineField, submitCount } =
    useForm<AcessoFormData>({
      validationSchema: acessoValidationSchema,
      initialValues: {
        nomeUsuario: signInData.acesso.nomeUsuario,
        email: signInData.acesso.email,
        senha: signInData.acesso.senha,
        confirmarSenha: signInData.acesso.confirmarSenha,
      },
    });

  const [nomeUsuario] = defineField('nomeUsuario');
  const [email] = defineField('email');
  const [senha] = defineField('senha');
  const [confirmarSenha] = defineField('confirmarSenha');

  const onSubmit = handleSubmit((formData) => {
    updateAcessoData({
      nomeUsuario: formData.nomeUsuario,
      email: formData.email,
      senha: formData.senha,
      confirmarSenha: formData.confirmarSenha,
    });
    nextStep();
  });

  return {
    nomeUsuario,
    email,
    senha,
    confirmarSenha,

    errors,

    onSubmit,
    submitCount,
  };
}
