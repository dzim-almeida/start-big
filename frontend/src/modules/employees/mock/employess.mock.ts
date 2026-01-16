// mocks/employees.ts
import type { Employee } from "../types/employees.types";

export const mockEmployees: Employee[] = [
  { 
    id: 1, 
    name: 'Ana Silva', 
    email: 'ana.silva@empresa.com', 
    role: 'UX Designer', 
    status: 'active' 
  },
  { 
    id: 2, 
    name: 'Bruno Santos', 
    email: 'bruno.s@empresa.com', 
    role: 'Fullstack Developer', 
    status: 'active' 
  },
  { 
    id: 3, 
    name: 'Carla Oliveira', 
    email: 'carla.o@empresa.com', 
    role: 'Gerente de Projetos', 
    status: 'vacation' 
  },
  { 
    id: 4, 
    name: 'Diego Ferreira', 
    email: 'diego.f@empresa.com', 
    role: 'Analista de RH', 
    status: 'active' 
  },
  { 
    id: 5, 
    name: 'Elena Costa', 
    email: 'elena.c@empresa.com', 
    role: 'CFO', 
    status: 'inactive' 
  },
];