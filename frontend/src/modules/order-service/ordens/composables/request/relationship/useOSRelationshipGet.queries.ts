import { useQuery } from '@tanstack/vue-query';

import {
  getEmployeesAll,
  getCustomersAll,
} from '../../../services/relationship/osRelationshipGet.service';

import {
  OS_CUSTOMER_QUERY_KEY,
  OS_CUSTOMER_QUERY_STALE_TIME,
  OS_EMPLOYEE_QUERY_KEY,
  OS_EMPLOYEE_QUERY_STALE_TIME,
} from '../../../constants/core.constant';
import { computed, ref } from 'vue';
import { refDebounced } from '@vueuse/core';

export function useOsCustomersGet() {
  const searchCustomer = ref<string>('');
  const deboucedSearchCustomer = refDebounced(searchCustomer, 300);

  const query = useQuery({
    queryKey: [OS_CUSTOMER_QUERY_KEY, deboucedSearchCustomer],
    queryFn: () => getCustomersAll(deboucedSearchCustomer.value),
    staleTime: OS_CUSTOMER_QUERY_STALE_TIME,
  });

  const customers = computed(() => {
    return query.data.value?.items ?? [];
  });

  return {
    searchCustomer,
    customers,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error
  }
}

export function useOsEmployeesGet() {
  return useQuery({
    queryKey: [OS_EMPLOYEE_QUERY_KEY],
    queryFn: getEmployeesAll,
    staleTime: OS_EMPLOYEE_QUERY_STALE_TIME,
  });
}
