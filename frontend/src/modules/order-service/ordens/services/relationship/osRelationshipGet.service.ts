import api from '@/api/axios';

import {
  type EmployeeReadSchemaDataType,
} from '../../schemas/relationship/employee/employee.schema';

import type { CustomerUnionReadSchemaDataType } from '../../schemas/relationship/customer/customer.schema';

import {
  CustomerPaginationSchema,
  type CustomerPaginationDataType,
} from '@/modules/customers/schemas/customerQuery.schema';

import { BASE_EMPLOYEE_OS_URL, BASE_CUSTOMER_OS_URL } from '../../constants/core.constant';

export async function getEmployeesAll(): Promise<EmployeeReadSchemaDataType> {
  const { data } = await api.get<EmployeeReadSchemaDataType>(`${BASE_EMPLOYEE_OS_URL}/`);
  return data;
}

export async function getCustomersAll(): Promise<CustomerUnionReadSchemaDataType[]> {
  const { data } = await api.get<CustomerPaginationDataType>(
    `${BASE_CUSTOMER_OS_URL}/`,
    { params: { only_true: true } },
  );

  const result = CustomerPaginationSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getCustomersAll] Zod validation warning:', result.error.issues);
    return ((data as any).items ?? []) as CustomerUnionReadSchemaDataType[];
  }
  return result.data.items;
}
