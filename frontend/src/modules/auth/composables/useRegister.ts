/**
 * @fileoverview Composable para lógica de cadastro de usuario
 * @description Encapsula toda a lógica de estado, validação e submissão
 * do formulário de cadastro utilizando Vee-Validate e Vue Query.
 */

import { ref, reactive, Ref} from 'vue';
import { useForm } from 'vee-validate';
import { useMutation } from '@tanstack/vue-query';
import { registerValidationSchema, type RegisterFormData } from '../schemas/register.schema';
import { register } from '../services/login.service';
import type { AuthTab, RegisterResponse } from '../types/auth.types';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage, isConflictError } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';
import type { AxiosError } from 'axios';

/**
 * Composable que gerencia o formulário de cadastro
 * @returns Objeto com estados e métodos para o formulário
 */
export function useRegister(activeTab?: Ref<AuthTab>) {
  const toast = useToast();
  const apiError = ref<string | null>(null);

  /**
   * Configuração do formulário com Vee-Validate
   */
  const { handleSubmit, errors, defineField, submitCount, resetForm } = useForm<RegisterFormData>({
    validationSchema: registerValidationSchema,
  });

  /**
   * Definição dos campos do formulário
   */
  const registerData: RegisterFormData = reactive({
    nome: defineField('nome')[0],
    email: defineField('email')[0],
    senha: defineField('senha')[0],
    confirmarSenha: defineField('confirmarSenha')[0],
  });

  /**
   * Mutation do Vue Query para cadastro
   */
  const registerMutation = useMutation<RegisterResponse, AxiosError<ApiError>, RegisterFormData>({
    mutationFn: (data) =>
      register({
        nome: data.nome,
        email: data.email,
        senha: data.senha,
      }),
    onSuccess: () => {
      toast.success('Cadastro realizado com sucesso!', 'Você já pode fazer login.');
      resetForm();
      if (activeTab?.value) {
        activeTab.value = 'entrar';
      }
    },
    onError: (error) => {
      if (isConflictError(error)) {
        apiError.value = 'Usuário master da empresa já cadastrado.';
        return;
      }
      apiError.value = getErrorMessage(error, 'Erro ao realizar o cadastro');
    },
  });

  const registerSubmit = handleSubmit((values) => {
    apiError.value = null;
    registerMutation.mutate(values)
  });

  return {
    // Campos do formulário
    registerData,

    // Estado de erros
    errors,
    apiError,

    // Estado de loading
    isLoading: registerMutation.isPending,

    // Métodos
    registerSubmit,
    submitCount,
  };
}
