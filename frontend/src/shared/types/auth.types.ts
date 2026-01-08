export interface TokenUser {
    sub: string;
    nome: string;
    empresa_id?: number;
    ativo: boolean;
    is_master: boolean;
    cargo?: string;
    permissoes?: Record<string, boolean>;
}