/**
 * @fileoverview Composable para lógica de login
 * @description Encapsula toda a lógica de estado, validação e submissão
 * do formulário de login utilizando Vee-Validate e Vue Query.
 */

import { ref, onMounted, reactive } from 'vue';
import { useForm } from 'vee-validate';
import { useMutation } from '@tanstack/vue-query';
import { useRouter } from 'vue-router';
import { loginValidationSchema, type LoginFormData } from '../schemas/login.schema';
import {
  login,
  saveRememberMe,
  clearRememberMe,
  getRememberedEmail,
} from '../services/login.service';
import type { LoginResponse } from '../types/auth.types';
import { useAuthStore } from '@/shared/store/auth.store';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';
import type { AxiosError } from 'axios';
import { saveItem } from '@/shared/services/localStorage.service';

/**
 * Composable que gerencia o formulário de login
 * @returns Objeto com estados e métodos para o formulário
 */
export function useLogin() {
  const authStore = useAuthStore();
  const router = useRouter();
  const toast = useToast();
  const rememberMe = ref(false);
  const savedEmail = ref<string | null>(null);
  const apiError = ref<string | null>(null);

  /**
   * Configuração do formulário com Vee-Validate
   */
  const { handleSubmit, errors, defineField, resetForm, submitCount } = useForm<LoginFormData>({
    validationSchema: loginValidationSchema,
  });

  /**
   * Definição dos campos do formulário
   */
  const loginData: LoginFormData = reactive({
    email: defineField('email')[0],
    senha: defineField('senha')[0],
  });

  /**
   * Mutation do Vue Query para login
   */
  const loginMutation = useMutation<LoginResponse, AxiosError<ApiError>, LoginFormData>({
    mutationFn: (data) => login({ email: data.email, senha: data.senha }),
    onSuccess: (response) => {
      authStore.setAuth(response);
      saveItem('token', response.access_token)

      if (rememberMe.value && loginData.email) {
        saveRememberMe(loginData.email);
      } else {
        clearRememberMe();
      }

      apiError.value = null;
      toast.success('Login realizado com sucesso!');
      if (authStore.user?.empresa_id) {
        router.push({ name: 'home' })
      } else {
        router.push({ name: 'onboarding' })
      }
    },
    onError: (error) => {
      apiError.value = getErrorMessage(error, 'Erro ao realizar login');
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
    savedEmail.value = getRememberedEmail();
    if (savedEmail.value) {
      rememberMe.value = true;
    }
  });

  return {
    // Campos do formulário
    loginData,
    savedEmail,
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
