/**
 * Re-export dos composables globais de formulário de clientes.
 * Mantido para compatibilidade com imports existentes.
 */
export {
  useCustomerFormProvider,
  useCustomerForm,
  CUSTOMER_FORM_KEY,
} from '@/shared/composables/modals/customers/context/useCustomerForm.context';

export {
  CUSTOMER_TYPE_TABS,
  GENDER_OPTIONS,
  DEFAULT_ADDRESS,
  DEFAULT_PF_VALUES,
  DEFAULT_PJ_VALUES,
} from '@/shared/composables/modals/customers/constants/customer.constant';

export type { CustomerFormContext } from '@/shared/composables/modals/customers/types/context.type';
