/**
 * ===========================================================================
 * ARQUIVO: clientes.types.ts
 * MODULO: Clientes
 * DESCRICAO: Define todas as interfaces e tipos TypeScript para o modulo
 *            de clientes. Segue o padrao polimorfico onde Cliente pode ser
 *            Pessoa Fisica (PF) ou Pessoa Juridica (PJ).
 * ===========================================================================
 *
 * ESTRUTURA DO ARQUIVO:
 * 1. Enums - Tipos simples (TipoCliente, Gender, State)
 * 2. Endereco - Interfaces para criar, ler e atualizar enderecos
 * 3. Cliente Base - Campos comuns entre PF e PJ
 * 4. Cliente PF - Interfaces especificas para Pessoa Fisica
 * 5. Cliente PJ - Interfaces especificas para Pessoa Juridica
 * 6. Union Types - Tipos que unem PF e PJ (polimorfismo)
 * 7. UI/Visual - Tipos para componentes visuais
 * 8. Constantes - Listas fixas (estados, generos)
 *
 * COMO USAR:
 * - Para criar cliente PF: use ClientePFCreate
 * - Para criar cliente PJ: use ClientePJCreate
 * - Para receber dados da API: use ClienteRead (ou Cliente)
 * - Para atualizar: use ClientePFUpdate ou ClientePJUpdate
 * ===========================================================================
 */

import type { Component } from 'vue';

// ===========================================================================
// ENUMS - Tipos simples que correspondem ao backend
// ===========================================================================

/**
 * Tipo do cliente - Pessoa Fisica ou Pessoa Juridica
 * Usado para discriminar qual interface usar
 */
export type TipoCliente = 'PF' | 'PJ';

/**
 * Genero do cliente (apenas para PF)
 */
export type Gender = 'MASCULINO' | 'FEMININO' | 'OUTRO';

/**
 * Filtro de status do cliente (ativo/inativo)
 * Atualmente nao implementado na UI, mas disponivel para uso futuro
 */
export type FilterStatus = 'todos' | 'ativos' | 'inativos';

/**
 * Filtro por tipo de cliente
 * - 'todos': Mostra PF e PJ
 * - 'PF': Apenas Pessoa Fisica
 * - 'PJ': Apenas Pessoa Juridica
 */
export type FilterTipo = 'todos' | TipoCliente;

// ===========================================================================
// STATS - Tipos para estatisticas do modulo
// ===========================================================================
export interface ClienteStatCard {
  id: string;
  icon: Component;
  label: string;
  value: number;
  colorClass: string;
}

// Interface que define o formato das estatísticas recebidas
export interface Stats {
  total: number;  // Total de clientes
  ativos: number; // Clientes ativos
  pf: number;     // Pessoas físicas
  pj: number;     // Pessoas jurídicas
}

export interface ClienteStatsData {
  total: number;
  ativos: number;
  pf: number;
  pj: number;
}

/**
 * Siglas dos estados brasileiros
 * Usado nos campos de endereco
 */
export type State =
  | 'AC' | 'AL' | 'AP' | 'AM' | 'BA' | 'CE' | 'DF' | 'ES'
  | 'GO' | 'MA' | 'MT' | 'MS' | 'MG' | 'PA' | 'PB' | 'PR'
  | 'PE' | 'PI' | 'RJ' | 'RN' | 'RS' | 'RO' | 'RR' | 'SC'
  | 'SP' | 'SE' | 'TO';

// ===========================================================================
// ENDERECO - Entidade generica (polimórfica)
// Pode ser vinculada a qualquer entidade (Cliente, Empresa, etc)
// ===========================================================================

/**
 * Interface para CRIAR um novo endereco
 * Campos obrigatorios: logradouro, numero, bairro, cidade, estado, cep
 */
export interface EnderecoCreate {
  logradouro: string;   // Nome da rua/avenida
  numero: string;       // Numero do imovel
  bairro: string;       // Bairro
  cidade: string;       // Cidade
  estado: State;        // Sigla do estado (ex: SP, RJ)
  cep: string;          // CEP sem formatacao (apenas numeros)
  complemento?: string; // Apartamento, bloco, etc (opcional)
}

/**
 * Interface de LEITURA de endereco (retorno da API)
 * Inclui campos adicionais como ID e vinculo com entidade
 */
export interface EnderecoRead extends EnderecoCreate {
  id: number;           // ID unico do endereco
  id_entidade: number;  // ID da entidade vinculada (cliente, empresa)
  tipo_entidade: string; // Tipo da entidade (CLIENTE, EMPRESA, etc)
}

/**
 * Interface para ATUALIZAR endereco
 * Todos os campos sao opcionais. O ID identifica qual endereco atualizar
 */
export interface EnderecoUpdate {
  id?: number;          // ID do endereco (se for atualizar existente)
  logradouro?: string;
  numero?: string;
  bairro?: string;
  cidade?: string;
  estado?: State;
  cep?: string;
  complemento?: string;
}

// ===========================================================================
// CLIENTE BASE - Campos comuns entre PF e PJ
// ===========================================================================

/**
 * Campos compartilhados por todos os tipos de cliente
 */
export interface ClienteBase {
  id: number;
  tipo: TipoCliente;
  email?: string;
  celular?: string;
  telefone?: string;
  ativo: boolean;
  criado_em: string;
  observacoes?: string; // Notas internas sobre o cliente
}
// Configuração de colunas da Tabela
export interface ClienteTableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
}
// ===========================================================================
// CLIENTE PF (Pessoa Fisica)
// Representa um cliente individual, identificado por CPF
// ===========================================================================

/**
 * Interface para CRIAR um cliente Pessoa Fisica
 * Campos obrigatorios: nome, cpf
 */
export interface ClientePFCreate {
  tipo: 'PF';
  nome: string;           // Nome completo
  cpf?: string;            // CPF sem formatacao (apenas numeros)
  rg?: string;            // RG (opcional)
  genero?: Gender;        // Genero (opcional)
  data_nascimento?: string; // Data no formato ISO: YYYY-MM-DD (opcional)
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  endereco?: EnderecoCreate[]; // Lista de enderecos (opcional)
}

/**
 * Interface de LEITURA de cliente PF (retorno da API)
 * Inclui campos de controle como ID e status ativo
 */
export interface ClientePFRead extends ClienteBase {
  id: number;             // ID unico do cliente
  tipo: 'PF';             // Discriminador - sempre 'PF' para pessoa fisica
  ativo: boolean;         // Se o cliente esta ativo no sistema
  nome: string;
  cpf: string;
  rg?: string;
  genero?: Gender;
  data_nascimento?: string;
  endereco?: EnderecoRead[];
}

/**
 * Interface para ATUALIZAR cliente PF
 * Todos os campos sao opcionais exceto 'tipo' que identifica como PF
 */
export interface ClientePFUpdate {
  tipo: 'PF';             // Obrigatorio para identificar o tipo
  nome?: string;
  cpf?: string;
  rg?: string;
  genero?: Gender;
  data_nascimento?: string;
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  endereco?: EnderecoUpdate[];
}

// ===========================================================================
// CLIENTE PJ (Pessoa Juridica)
// Representa uma empresa, identificada por CNPJ
// ===========================================================================

/**
 * Interface para CRIAR um cliente Pessoa Juridica
 * Campos obrigatorios: razao_social, cnpj, nome_fantasia
 */
export interface ClientePJCreate {
  razao_social: string;   // Nome legal da empresa
  cnpj?: string;           // CNPJ sem formatacao (apenas numeros)
  nome_fantasia?: string;  // Nome comercial/fantasia
  ie?: string;            // Inscricao Estadual (opcional)
  im?: string;            // Inscricao Municipal (opcional)
  regime_tributario?: string; // Ex: Simples Nacional, Lucro Presumido
  responsavel?: string;   // Nome da pessoa de contato
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  endereco?: EnderecoCreate[];
}

/**
 * Interface de LEITURA de cliente PJ (retorno da API)
 */
export interface ClientePJRead extends ClienteBase {
  id: number;
  tipo: 'PJ';             // Discriminador - sempre 'PJ' para pessoa juridica
  ativo: boolean;
  razao_social: string;
  cnpj: string;
  nome_fantasia: string;
  ie?: string;
  im?: string;
  regime_tributario?: string;
  responsavel?: string;
  endereco?: EnderecoRead[];
}

/**
 * Interface para ATUALIZAR endereco
 * Todos os campos sao opcionais. O ID identifica qual endereco atualizar
 */
export interface EnderecoUpdate {
  id?: number;          // ID do endereco (se for atualizar existente)
  logradouro?: string;
  numero?: string;
  bairro?: string;
  cidade?: string;
  estado?: State;
  cep?: string;
  complemento?: string;
}

export type Endereco = EnderecoRead;


/**
 * Interface para ATUALIZAR cliente PJ
 */
export interface ClientePJUpdate {
  tipo: 'PJ';
  razao_social?: string;
  cnpj?: string;
  nome_fantasia?: string;
  ie?: string;
  im?: string;
  regime_tributario?: string;
  responsavel?: string;
  email?: string;
  celular?: string;
  telefone?: string;
  observacoes?: string;
  endereco?: EnderecoUpdate[];
}

// ===========================================================================
// UNION TYPES (Discriminated Union)
// Permitem tratar PF e PJ de forma polimórfica
// ===========================================================================

/**
 * Cliente pode ser PF ou PJ
 * Use 'tipo' para discriminar: cliente.tipo === 'PF' ou 'PJ'
 */
export type Cliente = ClientePFRead | ClientePJRead;

/**
 * Alias para Cliente (mesmo significado)
 */
export type ClienteRead = ClientePFRead | ClientePJRead;

/**
 * Update pode ser para PF ou PJ
 */
export type ClienteUpdate = ClientePFUpdate | ClientePJUpdate;

/**
 * Cliente com campos de exibicao formatados
 * Usado na listagem e selects
 */
export type ClienteFormatted = Cliente & {
  displayName: string;
  displayDoc: string;
  displayPhone: string;
  initial: string;
  sortName: string;
};

export interface EquipamentoHistorico {
  equipamento: string;
  marca: string | null;
  modelo: string | null;
  numero_serie: string | null;
}

// ===========================================================================
// UI / VISUAL - Tipos para componentes da interface
// ===========================================================================


/**
 * Filtro por tipo de cliente na listagem
 */
export type ClienteFilterTipo = 'todos' | TipoCliente;

/**
 * Filtro por status (ativo/inativo) na listagem
 */
export type ClienteFilterStatus = 'todos' | 'ativos' | 'inativos';

/**
 * Configuracao de uma acao rapida
 * Usado em menus de contexto ou botoes de acao
 */
export interface ClienteAction {
  id: string;
  icon: Component;
  label: string;
  action: () => void;
  variant: 'primary' | 'secondary' | 'outline';
}

// ===========================================================================
// CONSTANTES - Listas fixas para selects e validacoes
// ===========================================================================

/**
 * Lista de estados brasileiros para selects
 * Ordenados alfabeticamente pela sigla
 */
export const ESTADOS_BRASIL: { value: State; label: string }[] = [
  { value: 'AC', label: 'Acre' },
  { value: 'AL', label: 'Alagoas' },
  { value: 'AP', label: 'Amapá' },
  { value: 'AM', label: 'Amazonas' },
  { value: 'BA', label: 'Bahia' },
  { value: 'CE', label: 'Ceará' },
  { value: 'DF', label: 'Distrito Federal' },
  { value: 'ES', label: 'Espírito Santo' },
  { value: 'GO', label: 'Goiás' },
  { value: 'MA', label: 'Maranhão' },
  { value: 'MT', label: 'Mato Grosso' },
  { value: 'MS', label: 'Mato Grosso do Sul' },
  { value: 'MG', label: 'Minas Gerais' },
  { value: 'PA', label: 'Pará' },
  { value: 'PB', label: 'Paraíba' },
  { value: 'PR', label: 'Paraná' },
  { value: 'PE', label: 'Pernambuco' },
  { value: 'PI', label: 'Piauí' },
  { value: 'RJ', label: 'Rio de Janeiro' },
  { value: 'RN', label: 'Rio Grande do Norte' },
  { value: 'RS', label: 'Rio Grande do Sul' },
  { value: 'RO', label: 'Rondônia' },
  { value: 'RR', label: 'Roraima' },
  { value: 'SC', label: 'Santa Catarina' },
  { value: 'SP', label: 'São Paulo' },
  { value: 'SE', label: 'Sergipe' },
  { value: 'TO', label: 'Tocantins' },
];

/**
 * Opcoes de genero para clientes PF
 */
export const GENEROS: { value: Gender; label: string }[] = [
  { value: 'MASCULINO', label: 'Masculino' },
  { value: 'FEMININO', label: 'Feminino' },
  { value: 'OUTRO', label: 'Outro' },
];
