export interface CompanyData {
    razao_social: string;
    nome_fantasia: string;
    url_logo: string;
    ativo: boolean;
}

export interface UserDataResponse {
    nome: string;
    email: string;
    url_perfil: string;
    empresa: CompanyData;
}