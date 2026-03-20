import { useCreateCustomerPFMutation, useCreateCustomerPJMutation } from '@/modules/customers/composables/request/useCustomerCreate.mutate';
import { useUpdateCustomerMutation, useToggleCustomerAtivoMutation } from '@/modules/customers/composables/request/useCustomerUpdate.mutate';

export function useClienteActions() {
  const createPFMutation = useCreateCustomerPFMutation();
  const createPJMutation = useCreateCustomerPJMutation();
  const updateMutation = useUpdateCustomerMutation();
  const toggleAtivoMutation = useToggleCustomerAtivoMutation();

  return {
    createPFMutation,
    createPJMutation,
    updateMutation,
    toggleAtivoMutation,
  };
}
