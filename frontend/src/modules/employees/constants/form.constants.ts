/**
 * @fileoverview Form constants for employee forms
 * @description Select options for employee form fields
 */

interface SelectOption {
  value: string;
  label: string;
}

export const GENDER_OPTIONS: SelectOption[] = [
  { value: 'MASCULINO', label: 'Masculino' },
  { value: 'FEMININO', label: 'Feminino' },
  { value: 'OUTRO', label: 'Outro' },
];

export const BANK_ACCOUNT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CORRENTE', label: 'Conta Corrente' },
  { value: 'POUPANCA', label: 'Conta Poupanca' },
];

export const TIPO_CONTRATO_OPTIONS: SelectOption[] = [
  { value: 'CLT', label: 'CLT' },
  { value: 'PJ', label: 'Pessoa Juridica (PJ)' },
  { value: 'Estagio', label: 'Estagio' },
  { value: 'Temporario', label: 'Temporario' },
  { value: 'Freelancer', label: 'Freelancer' },
];

export const JORNADA_TRABALHO_OPTIONS: SelectOption[] = [
  { value: '44h semanais', label: '44 horas semanais' },
  { value: '40h semanais', label: '40 horas semanais' },
  { value: '36h semanais', label: '36 horas semanais' },
  { value: '30h semanais', label: '30 horas semanais' },
  { value: '20h semanais', label: '20 horas semanais' },
];
