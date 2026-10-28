import api from '@/api/axios';
import type { ResultadoVerificacaoFiscal } from '@/shared/types/fiscal.types';
import type { EmissaoResponse, NfseDocumento, NfsePreview } from '../types/fiscal.types';
import { TIMEOUT_CONSULTA, TIMEOUT_EMISSAO } from '../constants/fiscal.constants';

const NFSE_ENDPOINT = '/fiscal/nfse';

/**
 * NFS-e da OS (backend-fastapi/docs/nfse-plano.md, F3). Tudo atrás do módulo
 * NFSE — quem chama já conferiu `recursoDisponivel('nfse')`.
 *
 * Rotas próprias, e não as do Centro Fiscal da NF-e: aquelas exigem o módulo
 * NFE, e o prestador MEI contrata só a NFS-e.
 */
export const nfseService = {
  async listarDocumentos(): Promise<NfseDocumento[]> {
    const { data } = await api.get<NfseDocumento[]>(`${NFSE_ENDPOINT}/documentos`, {
      timeout: TIMEOUT_CONSULTA,
    });
    return data;
  },

  async verificarOs(numeroOs: string): Promise<ResultadoVerificacaoFiscal> {
    const { data } = await api.get<ResultadoVerificacaoFiscal>(
      `${NFSE_ENDPOINT}/os/${encodeURIComponent(numeroOs)}/verificar`,
      { timeout: TIMEOUT_CONSULTA },
    );
    return data;
  },

  async previewOs(numeroOs: string): Promise<NfsePreview> {
    const { data } = await api.post<NfsePreview>(
      `${NFSE_ENDPOINT}/os/${encodeURIComponent(numeroOs)}/preview`,
      null,
      { timeout: TIMEOUT_CONSULTA },
    );
    return data;
  },

  async emitirOs(numeroOs: string): Promise<EmissaoResponse> {
    const { data } = await api.post<EmissaoResponse>(
      `${NFSE_ENDPOINT}/os/${encodeURIComponent(numeroOs)}/emitir`,
      null,
      { timeout: TIMEOUT_EMISSAO },
    );
    return data;
  },

  async consultar(documentoId: number): Promise<EmissaoResponse> {
    const { data } = await api.post<EmissaoResponse>(
      `${NFSE_ENDPOINT}/documentos/${documentoId}/consultar`,
      null,
      { timeout: TIMEOUT_CONSULTA },
    );
    return data;
  },

  async cancelar(documentoId: number, justificativa: string): Promise<EmissaoResponse> {
    const { data } = await api.post<EmissaoResponse>(
      `${NFSE_ENDPOINT}/documentos/${documentoId}/cancelar`,
      { justificativa },
      { timeout: TIMEOUT_EMISSAO },
    );
    return data;
  },
};
