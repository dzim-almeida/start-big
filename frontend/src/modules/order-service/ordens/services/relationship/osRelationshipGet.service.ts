import api from '@/api/axios';

import {
  EmployeeReadSchema,
  EmployeeReadSchemaDataType,
} from '../../schemas/relationship/employee/employee.schema';

import {
  CustomerUnionReadSchema,
  CustomerUnionReadSchemaDataType,
} from '../../schemas/relationship/customer/customer.schema';

import { BASE_EMPLOYEE_OS_URL, BASE_CUSTOMER_OS_URL } from '../../constants/core.constant';

export async function getEmployeesAll(): Promise<EmployeeReadSchemaDataType> {
  const { data } = await api.get<EmployeeReadSchemaDataType>(`${BASE_EMPLOYEE_OS_URL}/`);
  return data;
  // const validatedData = EmployeeReadSchema.parse(data);
  // return validatedData;
}

export async function getCustomersAll(): Promise<CustomerUnionReadSchemaDataType> {
  const { data } = await api.get<CustomerUnionReadSchemaDataType>(`${BASE_CUSTOMER_OS_URL}/`);
  return data;
  // const validatedData = CustomerUnionReadSchema.parse(data);
  // return validatedData;
}
