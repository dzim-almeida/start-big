import type { PermissionKey } from '@/shared/constants/permissions.constants';
import { EnderecoFormData } from './address.types';

export type Permissions = PermissionKey;

export interface Company {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  documento: string;
  telefone: string;
  celular: string;
  email: string; 
  enderecos: EnderecoFormData[];
  url_logo: string;
  ativo: boolean;
}

export interface Position {
  nome: string;
  permissoes: Record<string, boolean>;
}

export interface User {
  id: number;
  nome: string;
  email: string;
  url_perfil?: string;
  ativo: boolean;
  empresa?: Company;
  cargo?: Position;
}

export interface UserResponse extends User {}
