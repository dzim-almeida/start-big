import { useToast } from '@/shared/composables/useToast';
import { ErroAoSalvar, salvarArquivo } from '@/shared/utils/arquivo';
import { fiscalService } from '../services/fiscal.service';

const ROTULO = { pdf: 'DANFE', xml: 'XML' } as const;

/**
 * Salva o DANFE (PDF) ou o XML de uma nota pelo "Salvar como" do Windows.
 *
 * O arquivo vem do BACKEND, que lê a cópia guardada na loja (funciona sem
 * internet) e só recorre à emissora quando não a tem — nunca pelo link da
 * emissora direto, que expira.
 */
export async function salvarDocumentoFiscal(
  doc: { id: number; chave_acesso: string | null },
  extensao: 'pdf' | 'xml',
): Promise<void> {
  const toast = useToast();
  const rotulo = ROTULO[extensao];
  let blob: Blob;
  try {
    blob = extensao === 'pdf'
      ? await fiscalService.baixarPdfDocumento(doc.id)
      : await fiscalService.baixarXmlDocumento(doc.id);
  } catch {
    toast.error(
      `Não foi possível obter o ${rotulo}`,
      'Ele não está guardado nesta máquina e a emissora não respondeu.',
    );
    return;
  }

  try {
    const r = await salvarArquivo(`${doc.chave_acesso || `documento-${doc.id}`}.${extensao}`, blob);
    if (r.cancelado) return;
    toast.success(`${rotulo} salvo`, r.caminho ? `Salvo em ${r.caminho}` : undefined);
  } catch (err) {
    toast.error(`Não foi possível salvar o ${rotulo}`, err instanceof ErroAoSalvar ? err.message : undefined);
  }
}
