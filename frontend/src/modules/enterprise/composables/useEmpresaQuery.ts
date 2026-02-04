/**
 * @fileoverview TanStack Query composable para o módulo Enterprise
 * @description Gerencia queries e mutations para dados da empresa
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { useToast } from '@/shared/composables/useToast';
import { useAuthStore } from '@/shared/stores/auth.store';
import {
  getEmpresa,
  updateEmpresa,
  uploadCertificado,
  uploadLogo,
  getWindowsCertificates,
  testSefazConnection,
  testPrefeituraConnection,
} from '../services/empresa.service';
import { QUERY_KEYS, STALE_TIME, MESSAGES } from '../constants/empresa.constants';
import type { EmpresaRead, EmpresaUpdate } from '../types/empresa.types';
import type { AxiosError } from 'axios';

// =============================================
// Query: Buscar dados da empresa
// =============================================

/**
 * Query para buscar dados da empresa do usuário autenticado
 * @returns Query com dados da empresa, loading state e error
 * @example
 * const { data: empresa, isLoading, error } = useEmpresaQuery();
 */
export function useEmpresaQuery() {
  const authStore = useAuthStore();
  const empresaId = authStore.userData?.empresa?.id;

  return useQuery({
    queryKey: [QUERY_KEYS.empresa, empresaId],
    queryFn: async () => {
      if (!empresaId) return null;
      return getEmpresa();
    },
    staleTime: STALE_TIME,
  });
}

/**
 * Query para listar certificados Windows
 * @returns Query com lista de certificados
 */
export function useWindowsCertificatesQuery() {
  return useQuery({
    queryKey: [QUERY_KEYS.windowsCertificates],
    queryFn: getWindowsCertificates,
    enabled: false, // Só executa manualmente via refetch
    staleTime: 0, // Sempre busca dados frescos
  });
}

// =============================================
// Mutation: Atualizar empresa
// =============================================

/**
 * Mutation para atualizar dados da empresa
 * @returns Mutation com função mutate e estados
 * @example
 * const { mutate, isPending } = useUpdateEmpresaMutation();
 * mutate({ id: 1, data: { razao_social: 'Nova Razão' } });
 */
export function useUpdateEmpresaMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const authStore = useAuthStore();

  return useMutation<EmpresaRead, AxiosError, { data: EmpresaUpdate }>({
    mutationFn: ({ data }) => updateEmpresa(data),
    onSuccess: async () => {
      toast.success(MESSAGES.success.save);
      await queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.empresa] });

      // Atualiza empresa no auth store
      authStore.revalidateUser()
    },
    onError: (error) => {
      const message = (error.response?.data as any)?.detail || MESSAGES.error.save;
      toast.error(message);
    },
  });
}

// =============================================
// Mutation: Upload de certificado
// =============================================

/**
 * Mutation para upload de certificado digital
 * @returns Mutation com função mutate e estados
 * @example
 * const { mutate, isPending } = useUploadCertificadoMutation();
 * mutate(file);
 */
export function useUploadCertificadoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<EmpresaRead, AxiosError, File>({
    mutationFn: uploadCertificado,
    onSuccess: () => {
      toast.success(MESSAGES.success.uploadCert);
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.empresa] });
    },
    onError: () => {
      toast.error(MESSAGES.error.uploadCert);
    },
  });
}

// =============================================
// Mutation: Upload de logo
// =============================================

/**
 * Mutation para upload de logo da empresa
 * @returns Mutation com função mutate e estados
 * @example
 * const { mutate, isPending } = useUploadLogoMutation();
 * mutate(file);
 */
export function useUploadLogoMutation() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const authStore = useAuthStore();

  return useMutation<EmpresaRead, AxiosError, File>({
    mutationFn: uploadLogo,
    onSuccess: () => {
      toast.success(MESSAGES.success.uploadLogo);
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.empresa] });

      // Atualiza empresa no auth store para refletir nova logo
      authStore.revalidateUser()
    },
    onError: () => {
      toast.error(MESSAGES.error.uploadLogo);
    },
  });
}

// =============================================
// Mutation: Teste de conexão SEFAZ
// =============================================

/**
 * Mutation para testar conexão com SEFAZ
 * @returns Mutation com função mutate e estados
 */
export function useTestSefazMutation() {
  const toast = useToast();

  return useMutation({
    mutationFn: testSefazConnection,
    onSuccess: (result) => {
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    },
    onError: (error: AxiosError) => {
      const message = (error.response?.data as any)?.detail || MESSAGES.error.connection;
      toast.error(message);
    },
  });
}

// =============================================
// Mutation: Teste de conexão Prefeitura
// =============================================

/**
 * Mutation para testar conexão com Prefeitura
 * @returns Mutation com função mutate e estados
 */
export function useTestPrefeituraMutation() {
  const toast = useToast();

  return useMutation({
    mutationFn: testPrefeituraConnection,
    onSuccess: (result) => {
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    },
    onError: (error: AxiosError) => {
      const message = (error.response?.data as any)?.detail || MESSAGES.error.connection;
      toast.error(message);
    },
  });
}

// =============================================
// Utilitários
// =============================================

/**
 * Hook para invalidar manualmente o cache da empresa
 * @returns Função para invalidar cache
 */
export function useInvalidateEmpresa() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.empresa] });
  };
}
