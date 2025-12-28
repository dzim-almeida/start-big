/**
 * @fileoverview Composable para lógica de cadastro de usuario
 * @description Encapsula toda a lógica de estado, validação e submissão
 * do formulário de cadastro utilizando Vee-Validate e Vue Query.
 */

import { ref, reactive } from 'vue';
import { useForm } from 'vee-validate';
import { useMutation } from '@tanstack/vue-query';
import { registerValidationSchema, type RegisterFormData } from '../schemas/register.schema';
import { register } from '../services/auth.service';
import type { RegisterResponse } from '../types/auth.types';
import type { ApiError } from '@/shared/types/axios.types';
import type { AxiosError } from 'axios';

/**
 * Composable que gerencia o formulário de cadastro
 * @returns Objeto com estados e métodos para o formulário
 */
export function useRegister() {
  const apiError = ref<string | null>(null);

  /**
   * Configuração do formulário com Vee-Validate
   */
  const { handleSubmit, errors, defineField, submitCount } = useForm<RegisterFormData>({
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
    onSuccess: (response) => {
      console.log(response);
    },
    onError: (error) => {
      const errorData = error.response?.data;
      apiError.value = errorData?.detail || errorData?.message || 'Erro ao realizar o cadastro';
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
