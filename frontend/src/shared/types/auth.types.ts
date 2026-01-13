export type Permissions =
  | 'all'
  | 'view_dashboard'
  | 'view_sales'
  | 'view_storage'
  | 'view_services'
  | 'view_customers'
  | 'view_products'
  | 'view_catalog'
  | 'view_enterprise'
  | 'view_employees';

export interface Company {
  id: number;
  razao_social: string;
  nome_fantasia: string;
  url_logo: string;
  ativo: boolean;
}

export interface Position {
  nome: string;
  permissoes: Record<Permissions, boolean>;
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
