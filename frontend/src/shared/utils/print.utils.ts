import { computed } from 'vue';
import { useAuthStore } from '@/shared/stores/auth.store';
import { formatCNPJ } from '@/shared/utils/document.utils';
import type { CompanyPrintInfo } from '@/shared/components/print/print.types';

// --- Cliente helpers (union type PF/PJ) ---

export function getClienteNome(cliente?: { tipo: string; nome?: string; nome_fantasia?: string; razao_social?: string } | null): string {
  if (!cliente) return '-';
  if (cliente.tipo === 'PF') return cliente.nome || '-';
  return cliente.nome_fantasia || cliente.razao_social || '-';
}

export function getClienteDoc(cliente?: { cpf?: string; cnpj?: string } | null): string {
  if (!cliente) return '';
  return (cliente as { cpf?: string }).cpf || (cliente as { cnpj?: string }).cnpj || '';
}

export function getClientePhone(cliente?: { celular?: string; telefone?: string } | null): string {
  if (!cliente) return '';
  return (cliente as { celular?: string }).celular || (cliente as { telefone?: string }).telefone || '';
}

// --- Payment helpers ---

export function getPaymentDisplayName(nome: string): string {
  const map: Record<string, string> = {
    'PIX': 'Pix',
    'DINHEIRO': 'Dinheiro',
    'CARTAO_CREDITO': 'Cartão de Crédito',
    'CARTAO_DEBITO': 'Cartão de Débito',
    'BOLETO': 'Boleto',
    'TRANSFERENCIA': 'Transferência',
  };

  const mapped = map[nome.toUpperCase()];
  if (mapped) return mapped;

  return nome
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function inferPaymentType(nome: string): string {
  const lower = nome.toLowerCase();
  if (lower.includes('pix')) return 'PIX';
  if (lower.includes('crédito') || lower.includes('credito')) return 'CARTAO_CREDITO';
  if (lower.includes('débito') || lower.includes('debito')) return 'CARTAO_DEBITO';
  if (lower.includes('boleto')) return 'BOLETO';
  if (lower.includes('transferência') || lower.includes('transferencia')) return 'TRANSFERENCIA';
  if (lower.includes('dinheiro')) return 'DINHEIRO';
  return 'OUTROS';
}

export function inferPermiteParcelamento(tipo: string): boolean {
  return tipo === 'CARTAO_CREDITO';
}

// --- Formatters ---

export function formatPrintDate(dateStr?: string | Date | null): string {
  if (!dateStr) return '__/__/____';
  return new Date(dateStr).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatPrintPhone(phone?: string): string {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 11) {
    return digits.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  if (digits.length === 10) {
    return digits.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return phone;
}

export function formatPrintDoc(doc?: string): string {
  if (!doc) return '';
  const digits = doc.replace(/\D/g, '');
  if (digits.length > 11) {
    return digits.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  }
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

// --- Image URL ---

export function getImageUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  const cleanPath = path.replace(/^static\//, '');
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  return `${base}/static/${cleanPath}`;
}

// --- Company info composable ---

export function useCompanyPrintInfo() {
  const authStore = useAuthStore();

  const companyInfo = computed<CompanyPrintInfo>(() => {
    const empresa = authStore.userData?.empresa;
    const endereco = authStore.enderecoData;

    const enderecoParts: string[] = [];
    if (endereco?.logradouro) {
      enderecoParts.push(endereco.logradouro);
      if (endereco.numero) enderecoParts.push(endereco.numero);
    }
    if (endereco?.bairro) enderecoParts.push(endereco.bairro);
    if (endereco?.cidade && endereco?.estado) {
      enderecoParts.push(`${endereco.cidade} - ${endereco.estado}`);
    }

    const shortParts: string[] = [];
    if (endereco?.logradouro) shortParts.push(endereco.logradouro);
    if (endereco?.numero) shortParts.push(endereco.numero);
    if (endereco?.bairro) shortParts.push(endereco.bairro);

    const cityState = endereco?.cidade && endereco?.estado
      ? `${endereco.cidade} - ${endereco.estado}`
      : '';

    return {
      nome: empresa?.nome_fantasia || empresa?.razao_social || 'Empresa',
      razaoSocial: empresa?.razao_social || '',
      cnpj: formatCNPJ(empresa?.documento || ''),
      endereco: enderecoParts.join(', ') || 'Endereço não cadastrado',
      enderecoLinha1: shortParts.join(', ') || 'Endereço não informado',
      enderecoLinha2: cityState,
      contato: empresa?.telefone || empresa?.celular || '',
      email: empresa?.email || '',
      logo: getImageUrl(empresa?.url_logo),
    };
  });

  return { companyInfo };
}
