import type { AddressFormData } from '@/modules/customers/schemas/customer.schema';
import type {
  EnderecoCreateDataType,
  EnderecoUpdateDataType,
} from '@/modules/customers/schemas/customerMutate.schema';
import { unmaskCep } from '@/shared/utils/unmask.utils';

export function prepareAddresses(addresses: Partial<AddressFormData>[], isUpdate: true): EnderecoUpdateDataType[] | undefined;
export function prepareAddresses(addresses: Partial<AddressFormData>[], isUpdate: false): EnderecoCreateDataType[] | undefined;
export function prepareAddresses(
  addresses: Partial<AddressFormData>[],
  isUpdate: boolean,
): EnderecoCreateDataType[] | EnderecoUpdateDataType[] | undefined {
  if (addresses.length === 0) return undefined;

  if (isUpdate) {
    return addresses.map((addr): EnderecoUpdateDataType => ({
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

  return addresses.map((addr): EnderecoCreateDataType => ({
    cep: unmaskCep(addr.cep || ''),
    logradouro: addr.logradouro || '',
    numero: addr.numero || '',
    complemento: addr.complemento || undefined,
    bairro: addr.bairro || '',
    cidade: addr.cidade || '',
    estado: (addr.estado || 'SP') as EnderecoCreateDataType['estado'],
  }));
}
