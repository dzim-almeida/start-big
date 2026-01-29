/**
 * @fileoverview Constants for customers module
 * @description Stats card configuration matching employees pattern
 */

import { Building2, Users, UserCheck, UserCircle } from 'lucide-vue-next';

import type { Component } from 'vue';

interface CardInfo {
  key: 'total' | 'ativos' | 'pf' | 'pj';
  icon: Component;
  label: string;
}

export const CARDS_INFO: CardInfo[] = [
  { key: 'total', icon: Users, label: 'Total de Clientes' },
  { key: 'ativos', icon: UserCheck, label: 'Clientes Ativos' },
  { key: 'pf', icon: UserCircle, label: 'Pessoa Fisica' },
  { key: 'pj', icon: Building2, label: 'Pessoa Juridica' },
];
