import api from '@/api/axios';
import type { ResultadoVerificacaoFiscal } from '@/shared/types/fiscal.types';
import type {
  EmissaoResponse,
  NfseAvulsaRequest,
  NfseConfiguracao,
  NfseDocumento,
  NfsePreview,
  NfseSaude,
  NfseOsParaEmitir,
  NfseDetalhe,
  DocumentoFiscalResumo,
} from '../types/fiscal.types';
import { TIMEOUT_CONSULTA, TIMEOUT_EMISSAO, TIMEOUT_LOTE } from '../constants/fiscal.constants';

const NFSE_ENDPOINT = '/fiscal/nfse';

/**
 * NFS-e da OS (backend-fastapi/docs/nfse-plano.md, F3). Tudo atrás do módulo
 * NFSE — quem chama já conferiu `recursoDisponivel('nfse')`.
 *
 * Rotas próprias, e não as do Centro Fiscal da NF-e: aquelas exigem o módulo
 * NFE, e o prestador MEI contrata só a NFS-e.
 */
export const nfseService = {
  /** Contadores por status das NFS-e (os cards da aba). */
  async obterResumo(): Promise<DocumentoFiscalResumo> {
    const { data } = await api.get<DocumentoFiscalResumo>(`${NFSE_ENDPOINT}/resumo`, { timeout: TIMEOUT_CONSULTA });
    return data;
  },

  /** O que falta para a NFS-e sair (a barra "Saúde Fiscal" da aba). */
  async obterSaude(): Promise<NfseSaude> {
    const { data } = await api.get<NfseSaude>(`${NFSE_ENDPOINT}/saude`, { timeout: TIMEOUT_CONSULTA });
    return data;
  },

  async listarDocumentos(): Promise<NfseDocumento[]> {
    const { data } = await api.get<NfseDocumento[]>(`${NFSE_ENDPOINT}/documentos`, {
      timeout: TIMEOUT_CONSULTA,
    });
    return data;
  },

  /** OS finalizadas sem NFS-e; `buscar` aceita o número curto ("158") ou o cliente. */
  async osParaEmitir(buscar = ''): Promise<NfseOsParaEmitir[]> {
    const { data } = await api.get<NfseOsParaEmitir[]>(`${NFSE_ENDPOINT}/os-para-emitir`, {
      params: { buscar },
      timeout: TIMEOUT_CONSULTA,
    });
    return data;
  },

  /** Tudo de uma NFS-e: o motivo inteiro, o que fazer e as tentativas anteriores. */
  async obterDocumento(id: number): Promise<NfseDetalhe> {
    const { data } = await api.get<NfseDetalhe>(`${NFSE_ENDPOINT}/documentos/${id}`, { timeout: TIMEOUT_CONSULTA });
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

  /**
   * `confirmarDuplicidade`: o operador viu o aviso de nota repetida (409
   * NOTA_DUPLICADA_SUSPEITA da plataforma) e confirmou que é outro serviço.
   */
  async emitirOs(
    numeroOs: string,
    confirmarDuplicidade = false,
    /** Com uma nota por código (G3): qual código emitir. */
    codigoNacional?: string,
  ): Promise<EmissaoResponse> {
    const params: Record<string, unknown> = {};
    if (confirmarDuplicidade) params.confirmar_duplicidade = true;
    if (codigoNacional) params.codigo_nacional = codigoNacional;
    const { data } = await api.post<EmissaoResponse>(
      `${NFSE_ENDPOINT}/os/${encodeURIComponent(numeroOs)}/emitir`,
      null,
      { params, timeout: TIMEOUT_EMISSAO },
    );
    return data;
  },

  /** A DPS da NFS-e avulsa (G4), sem enviar nada. */
  async previewAvulsa(dados: NfseAvulsaRequest): Promise<{ dps: NfsePreview['dps'] }> {
    const { data } = await api.post<{ dps: NfsePreview['dps'] }>(`${NFSE_ENDPOINT}/avulsa/preview`, dados, {
      timeout: TIMEOUT_CONSULTA,
    });
    return data;
  },

  async emitirAvulsa(dados: NfseAvulsaRequest, confirmarDuplicidade = false): Promise<EmissaoResponse> {
    const { data } = await api.post<EmissaoResponse>(`${NFSE_ENDPOINT}/avulsa/emitir`, dados, {
      params: confirmarDuplicidade ? { confirmar_duplicidade: true } : undefined,
      timeout: TIMEOUT_EMISSAO,
    });
    return data;
  },

  /** A NFS-e da instalação dos móveis da marcenaria (G5): uma por OS. */
  async emitirInstalacao(numeroOs: string, confirmarDuplicidade = false): Promise<EmissaoResponse> {
    const { data } = await api.post<EmissaoResponse>(
      `${NFSE_ENDPOINT}/os/${encodeURIComponent(numeroOs)}/instalacao/emitir`,
      null,
      { params: confirmarDuplicidade ? { confirmar_duplicidade: true } : undefined, timeout: TIMEOUT_EMISSAO },
    );
    return data;
  },

  async obterConfiguracao(): Promise<NfseConfiguracao> {
    const { data } = await api.get<NfseConfiguracao>(`${NFSE_ENDPOINT}/configuracao`, { timeout: TIMEOUT_CONSULTA });
    return data;
  },

  async salvarConfiguracao(dados: NfseConfiguracao): Promise<NfseConfiguracao> {
    const { data } = await api.put<NfseConfiguracao>(`${NFSE_ENDPOINT}/configuracao`, dados, {
      timeout: TIMEOUT_CONSULTA,
    });
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

  /** O ZIP do contador só com NFS-e (mesmo formato do `fiscalService.exportarXmlPeriodo`). */
  async exportarXmlPeriodo(
    dataInicio: string,
    dataFim: string,
  ): Promise<{ arquivo: Blob; nome: string; documentos: number; baixados: number; naoBaixados: number }> {
    const resposta = await api.get<Blob>(`${NFSE_ENDPOINT}/exportar-xml`, {
      params: { data_inicio: dataInicio, data_fim: dataFim },
      responseType: 'blob',
      timeout: TIMEOUT_LOTE,
    });
    const h = resposta.headers as Record<string, string | undefined>;
    return {
      arquivo: resposta.data,
      nome: `xml-nfse-${dataInicio}_${dataFim}.zip`,
      documentos: Number(h['x-fiscal-documentos'] ?? 0),
      baixados: Number(h['x-fiscal-baixados'] ?? 0),
      naoBaixados: Number(h['x-fiscal-nao-baixados'] ?? 0),
    };
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
