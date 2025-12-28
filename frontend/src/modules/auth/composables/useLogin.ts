/**
 * @fileoverview Composable para lógica de login
 * @description Encapsula toda a lógica de estado, validação e submissão
 * do formulário de login utilizando Vee-Validate e Vue Query.
 */

import { ref, reactive, onMounted } from 'vue';
import { useForm } from 'vee-validate';
import { useMutation } from '@tanstack/vue-query';
import { useRouter } from 'vue-router';
import { loginValidationSchema, type LoginFormData } from '../schemas/login.schema';
import {
  login,
  saveToken,
  saveRememberMe,
  clearRememberMe,
  getRememberedEmail,
} from '../services/auth.service';
import type { LoginResponse } from '../types/auth.types';
import type { ApiError } from '@/shared/types/axios.types';
import type { AxiosError } from 'axios';

/**
 * Composable que gerencia o formulário de login
 * @returns Objeto com estados e métodos para o formulário
 */
export function useLogin() {
  const router = useRouter();
  const rememberMe = ref(false);
  const apiError = ref<string | null>(null);

  /**
   * Configuração do formulário com Vee-Validate
   */
  const { handleSubmit, errors, defineField, resetForm, submitCount } = useForm<LoginFormData>({
    validationSchema: loginValidationSchema,
    initialValues: {
      email: '',
      senha: '',
    },
  });

  /**
   * Definição dos campos do formulário
   */
  const loginData: LoginFormData = reactive({
    email: defineField('email')[0],
    senha: defineField('senha')[0]
  })

  /**
   * Mutation do Vue Query para login
   */
  const loginMutation = useMutation<LoginResponse, AxiosError<ApiError>, LoginFormData>({
    mutationFn: (data) => login({ email: data.email, senha: data.senha }),
    onSuccess: (data) => {
      saveToken(data.access_token, data.token_type);

      if (rememberMe.value && loginData.email) {
        saveRememberMe(loginData.email);
      } else {
        clearRememberMe();
      }

      apiError.value = null;
      router.push('/dashboard');
    },
    onError: (error) => {
      const errorData = error.response?.data;
      apiError.value = errorData?.detail || errorData?.message || 'Erro ao realizar login';
    },
  });

  /**
   * Handler de submissão do formulário
   */
  const loginSubmit = handleSubmit((values) => {
    apiError.value = null;
    loginMutation.mutate(values);
  });

  /**
   * Carrega email salvo se "lembrar-me" estava ativo
   */
  onMounted(() => {
    const savedEmail = getRememberedEmail();
    if (savedEmail) {
      loginData.email = savedEmail;
      rememberMe.value = true;
    }
  });

  return {
    // Campos do formulário
    loginData,
    rememberMe,

    // Estado de erros
    errors,
    apiError,

    // Estado de loading
    isLoading: loginMutation.isPending,

    // Métodos
    loginSubmit,
    resetForm,
    submitCount,
  };
}
