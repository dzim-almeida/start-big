import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type {
  EnderecoCreateDataType,
  EnderecoUpdateDataType,
} from '@/modules/customers/schemas/customerMutate.schema';
import { unmaskCep } from '@/shared/utils/unmask.utils';

const ADDRESS_FIELDS = ['cep', 'logradouro', 'numero', 'bairro', 'cidade', 'estado'] as const;

function isAddressEmpty(addr: Partial<AddressFormData>): boolean {
  return ADDRESS_FIELDS.every((field) => !addr[field]?.trim());
}

export function prepareAddresses(addresses: Partial<AddressFormData>[], isUpdate: true): EnderecoUpdateDataType[] | undefined;
export function prepareAddresses(addresses: Partial<AddressFormData>[], isUpdate: false): EnderecoCreateDataType[] | undefined;
export function prepareAddresses(
  addresses: Partial<AddressFormData>[],
  isUpdate: boolean,
): EnderecoCreateDataType[] | EnderecoUpdateDataType[] | undefined {
  const filledAddresses = addresses.filter((addr) => !isAddressEmpty(addr));
  if (filledAddresses.length === 0) return undefined;

  if (isUpdate) {
    return filledAddresses.map((addr): EnderecoUpdateDataType => ({
      id: addr.id,
      cep: unmaskCep(addr.cep || ''),
      logradouro: addr.logradouro || '',
      numero: addr.numero || '',
      complemento: addr.complemento || undefined,
      bairro: addr.bairro || '',
      cidade: addr.cidade || '',
      estado: (addr.estado || undefined) as EnderecoUpdateDataType['estado'],
    }));
  }

  return filledAddresses.map((addr): EnderecoCreateDataType => ({
    cep: unmaskCep(addr.cep || ''),
    logradouro: addr.logradouro || '',
    numero: addr.numero || '',
    complemento: addr.complemento || undefined,
    bairro: addr.bairro || '',
    cidade: addr.cidade || '',
    estado: (addr.estado || undefined) as EnderecoCreateDataType['estado'],
  }));
}
