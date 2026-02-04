/**
 * @fileoverview Serviço de API para o módulo Enterprise
 * @description Funções assíncronas puras para operações CRUD de empresa
 */

import api from '@/api/axios';
import type {
  EmpresaRead,
  EmpresaUpdate,
  WindowsCertificate,
  ConnectionTestResponse,
} from '../types/empresa.types';

const BASE_URL = '/empresas';

// =============================================
// Operações de leitura
// =============================================

/**
 * Busca empresa por ID
 * @param id - ID da empresa
 * @returns Dados completos da empresa
 * @example
 * const empresa = await getEmpresa(1);
 * console.log(empresa.razao_social);
 */
export async function getEmpresa(): Promise<EmpresaRead> {
  const { data } = await api.get<EmpresaRead>(`${BASE_URL}/`);
  return data;
}

/**
 * Lista certificados instalados no Windows
 * @returns Lista de certificados disponíveis
 * @example
 * const certs = await getWindowsCertificates();
 * console.log(certs[0].friendly_name);
 */
export async function getWindowsCertificates(): Promise<WindowsCertificate[]> {
  const { data } = await api.get<WindowsCertificate[]>(`${BASE_URL}/certificados-windows`);
  return data;
}

// =============================================
// Operações de escrita
// =============================================

/**
 * Atualiza dados da empresa
 * @param id - ID da empresa
 * @param payload - Dados a serem atualizados
 * @returns Empresa atualizada
 * @example
 * const updated = await updateEmpresa(1, {
 *   razao_social: 'Nova Razão Social',
 *   nome_fantasia: 'Novo Nome'
 * });
 */
export async function updateEmpresa(payload: EmpresaUpdate): Promise<EmpresaRead> {
  const { data } = await api.put<EmpresaRead>(`${BASE_URL}/`, payload);
  return data;
}

// =============================================
// Operações de upload
// =============================================

/**
 * Faz upload do certificado digital A1 (PKCS#12)
 *
 * IMPORTANTE: A senha é enviada apenas nesta requisição para validação.
 * Ela NÃO é persistida no banco de dados.
 *
 * @param file - Arquivo .pfx ou .p12
 * @param senha - Senha do certificado (usada apenas para validação)
 * @returns Empresa com certificado atualizado
 * @example
 * const file = event.target.files[0];
 * const empresa = await uploadCertificado(file, 'minhaSenha123');
 * console.log(empresa.fiscal_settings?.certificado_validade);
 */
export async function uploadCertificado(file: File, senha: string): Promise<EmpresaRead> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('senha', senha);

  const { data } = await api.post<EmpresaRead>(`${BASE_URL}/certificado-a1`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return data;
}

/**
 * Vincula um certificado do Windows Certificate Store à empresa
 *
 * O certificado é identificado pelo thumbprint (hash único).
 * Não há upload de arquivo - o certificado deve estar instalado no Windows.
 *
 * @param thumbprint - Identificador único do certificado no Windows
 * @returns Empresa atualizada com o certificado vinculado
 * @example
 * const empresa = await vincularCertificadoWindows('ABC123...');
 * console.log(empresa.fiscal_settings?.certificado_thumbprint);
 */
export async function vincularCertificadoWindows(thumbprint: string): Promise<EmpresaRead> {
  const { data } = await api.post<EmpresaRead>(`${BASE_URL}/certificado-windows`, {
    thumbprint,
  });

  return data;
}

/**
 * Faz upload da logo da empresa
 * @param file - Arquivo de imagem (PNG, JPG)
 * @returns Empresa com logo atualizada
 * @example
 * const file = event.target.files[0];
 * const empresa = await uploadLogo(file);
 * console.log(empresa.url_logo);
 */
export async function uploadLogo(file: File): Promise<EmpresaRead> {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post<EmpresaRead>(`${BASE_URL}/imagem/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return data;
}

// =============================================
// Operações de teste de conexão
// =============================================

/**
 * Testa conexão com o SEFAZ (emissão estadual)
 * @param id - ID da empresa
 * @returns Resultado do teste de conexão
 * @example
 * const result = await testSefazConnection(1);
 * if (result.success) {
 *   console.log('Conexão OK:', result.message);
 * }
 */
export async function testSefazConnection(id: number): Promise<ConnectionTestResponse> {
  const { data } = await api.post<ConnectionTestResponse>(`${BASE_URL}/${id}/testar-sefaz`);
  return data;
}

/**
 * Testa conexão com a Prefeitura (emissão municipal)
 * @param id - ID da empresa
 * @returns Resultado do teste de conexão
 * @example
 * const result = await testPrefeituraConnection(1);
 * if (result.success) {
 *   console.log('Conexão OK:', result.message);
 * }
 */
export async function testPrefeituraConnection(id: number): Promise<ConnectionTestResponse> {
  const { data } = await api.post<ConnectionTestResponse>(`${BASE_URL}/${id}/testar-prefeitura`);
  return data;
}
