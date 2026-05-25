/**
 * Barrel file - Composables do modulo Ordem de Servico
 */

// Listagem e filtros
export { useOrdensServico } from './useOrdensServico';
export { useServicos } from './useServicos';

// Formulario de OS (composables especializados)
export { useOSForm } from './useOSForm';
export { useOSFormState, type OSItemForm, type OSFormData } from './useOSFormState';
export { useOSFormQueries } from './useOSFormQueries';
export { useOSFinancials } from './useOSFinancials';
export { useOSFormMutations, type MutationCallbacks, type UseOSFormMutationsReturn } from './useOSFormMutations';
export {
  useOSFormContext,
  useOSFormContextOptional,
  provideOSFormContext,
  OS_FORM_CONTEXT_KEY,
  type OSFormContext,
} from './useOSFormContext';

// Acoes
export { useOSActions } from './useOSActions';
export { useServicoActions } from './useServicoActions';
export { useOSFinalization } from './useOSFinalization';

// Outros
export { useOSClientSearch } from './useOSClientSearch';
export { useOSItemForm } from './useOSItemForm';
export { useOSCancel } from './useOSCancel';
