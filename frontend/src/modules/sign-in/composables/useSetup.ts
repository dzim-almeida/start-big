import { ref } from 'vue';
import { useMutation } from '@tanstack/vue-query';
import type { AxiosError } from 'axios';
import type { ApiError } from '@/shared/types/axios.types';
import { getErrorMessage } from '@/shared/utils/error.utils';
import { useToast } from '@/shared/composables/useToast';
import { useAppNavigation } from '@/shared/composables/useAppNavigation';
import { useAuthStore } from '@/shared/stores/auth.store';
import { unmaskCep, unmaskDocument, unmaskPhone } from '@/shared/utils/unmask.utils';
import { useSignIn } from './useSignIn';
import { setupSistema, uploadEmpresaLogo } from '../services/sign-in.service';
import type { SetupRequest } from '../types/sign-in.types';

/**
 * Composable para gerenciar a submissão do setup (Passo 4 - Resumo)
 */
export function useSetup() {
  const { goToHome } = useAppNavigation();
  const toast = useToast();
  const { signInData, logoFile, resetSignIn } = useSignIn();
  const authStore = useAuthStore();

  const apiError = ref<string | null>(null);

  const setupMutation = useMutation<
    { access_token: string; token_type: string },
    AxiosError<ApiError>,
    SetupRequest
  >({
    mutationFn: setupSistema,
    onSuccess: async () => {
      // Revalidar usuário (JWT já foi salvo no localStorage pelo service)
      await authStore.revalidateUser();

      // Upload da logo se houver
      if (logoFile.value) {
        try {
          await uploadEmpresaLogo(logoFile.value);
        } catch {
          // Logo falhou mas setup já foi feito — não bloqueia o fluxo
          console.warn('Falha no upload da logo, mas setup foi concluído.');
        }
      }

      toast.success(
        'Sua loja foi cadastrada. Bem-vindo ao Start Big!',
        'Um email com sua chave de acesso foi enviado para você. Verifique sua caixa de entrada e spam.',
      );

      resetSignIn();
      goToHome();
    },
    onError: (error) => {
      apiError.value = getErrorMessage(error, 'Erro ao configurar o sistema') as string;
    },
  });

  async function confirmSetup(): Promise<void> {
    apiError.value = null;

    const isPF = signInData.responsavel.tipoPessoa === 'PF';

    const request: SetupRequest = {
      // Loja
      nome_loja: signInData.loja.nomeLoja,
      segmento: signInData.loja.segmento || undefined,
      celular: signInData.loja.celular
        ? unmaskPhone(signInData.loja.celular)
        : undefined,
      email_loja: signInData.loja.emailLoja || undefined,
      telefone: signInData.loja.telefone
        ? unmaskPhone(signInData.loja.telefone)
        : undefined,
      endereco: [
        {
          cep: unmaskCep(signInData.loja.cep),
          logradouro: signInData.loja.logradouro,
          numero: signInData.loja.numero || 'S/N',
          complemento: signInData.loja.complemento || undefined,
          bairro: signInData.loja.bairro,
          cidade: signInData.loja.cidade,
          estado: signInData.loja.estado,
        },
      ],

      // Responsável
      tipo_pessoa: signInData.responsavel.tipoPessoa,
      nome_responsavel: signInData.responsavel.nomeResponsavel,

      // Campos PF
      ...(isPF && {
        cpf: signInData.responsavel.cpf
          ? unmaskDocument(signInData.responsavel.cpf)
          : undefined,
        rg: signInData.responsavel.rg || undefined,
        genero: signInData.responsavel.genero || undefined,
        data_nascimento: signInData.responsavel.dataNascimento || undefined,
      }),

      // Campos PJ
      ...(!isPF && {
        razao_social: signInData.responsavel.razaoSocial || undefined,
        cnpj: signInData.responsavel.cnpj
          ? unmaskDocument(signInData.responsavel.cnpj)
          : undefined,
        nome_fantasia_pj: signInData.responsavel.nomeFantasiaPJ || undefined,
        inscricao_estadual: signInData.responsavel.inscricaoEstadual || undefined,
        inscricao_municipal: signInData.responsavel.inscricaoMunicipal || undefined,
        regime_tributario: signInData.responsavel.regimeTributario || undefined,
      }),

      // Contato responsável
      celular_responsavel: signInData.responsavel.celularResponsavel
        ? unmaskPhone(signInData.responsavel.celularResponsavel)
        : undefined,
      email_responsavel: signInData.responsavel.emailResponsavel || undefined,

      // Acesso
      nome_usuario: signInData.acesso.nomeUsuario,
      email: signInData.acesso.email,
      senha: signInData.acesso.senha,
    };

    setupMutation.mutate(request);
  }

  return {
    isPending: setupMutation.isPending,
    apiError,
    confirmSetup,
  };
}
