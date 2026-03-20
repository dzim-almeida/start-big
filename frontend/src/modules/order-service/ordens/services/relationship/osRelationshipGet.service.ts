import api from '@/api/axios';

import {
  EmployeeReadSchema,
  EmployeeReadSchemaDataType,
} from '../../schemas/relationship/employee/employee.schema';

import {
  CustomerPaginationSchema,
  type CustomerPaginationDataType,
} from '@/modules/customers/schemas/customerQuery.schema';

import { CustomerUnionReadSchemaDataType } from '@/shared/schemas/customer/customer.schema';

import { BASE_EMPLOYEE_OS_URL, BASE_CUSTOMER_OS_URL } from '../../constants/core.constant';

export async function getEmployeesAll(): Promise<EmployeeReadSchemaDataType> {
  const { data } = await api.get<EmployeeReadSchemaDataType>(`${BASE_EMPLOYEE_OS_URL}/`);
  return data;
}

export async function getCustomersAll(search?: string): Promise<CustomerUnionReadSchemaDataType[]> {
  const params: Record<string, string | boolean> = {};
  if (search) params.search = search;
  params.only_active = true;
  const { data } = await api.get<CustomerUnionReadSchemaDataType>(`${BASE_CUSTOMER_OS_URL}/`, { params });
  const result = CustomerPaginationSchema.safeParse(data);
  if (!result.success) {
    console.warn('[getCustomersAll] Zod validation warning:', result.error.issues);
    return ((data as any).items ?? []) as CustomerUnionReadSchemaDataType[];
  }
  return result.data.items;
}
