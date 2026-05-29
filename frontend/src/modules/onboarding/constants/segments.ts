/**
 * @fileoverview Constantes dos segmentos de negócio
 * @description Define os segmentos disponíveis com seus ícones e descrições
 */

import type { SegmentOption } from '../types/onboarding.types';

/**
 * Lista de segmentos de negócio disponíveis
 * Cada segmento possui um ícone SVG inline para garantir consistência visual
 */
export const BUSINESS_SEGMENTS: SegmentOption[] = [
  {
    id: 'assistencia_tecnica',
    label: 'Assistência Técnica',
    icon: 'computer',
    description: 'Reparo de computadores, celulares e eletrônicos',
  },
  {
    id: 'oficina_mecanica',
    label: 'Oficina Mecânica',
    icon: 'wrench',
    description: 'Manutenção e reparo de veículos',
  },
  {
    id: 'mercado',
    label: 'Mercado',
    icon: 'store',
    description: 'Supermercados, mercearias e vendas no varejo',
  },
  {
    id: 'marcenaria',
    label: 'Marcenaria',
    icon: 'hammer',
    description: 'Fabricação e reparo de móveis',
  },
  {
    id: 'eletricista',
    label: 'Eletricista',
    icon: 'bolt',
    description: 'Serviços de instalação e manutenção elétrica',
  },
  {
    id: 'outros',
    label: 'Outros',
    icon: 'grid',
    description: 'Outros tipos de negócio',
  },
];

/**
 * Mapeia o ID do segmento para suas informações
 */
export function getSegmentById(id: string): SegmentOption | undefined {
  return BUSINESS_SEGMENTS.find((segment) => segment.id === id);
}
