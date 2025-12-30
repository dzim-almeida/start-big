/**
 * @fileoverview Módulo de Onboarding
 * @description Exporta os componentes, composables e tipos do módulo de
 * configuração inicial da empresa.
 */

// Composables
export { useOnboarding } from './composables/useOnboarding';
export { useCepLookup } from './composables/useCepLookup';

// Types
export type {
  BusinessSegment,
  DocumentType,
  OnboardingData,
  OnboardingStep,
  CompanyData,
  ContactData,
  AddressData,
} from './types/onboarding.types';

// Constants
export { BUSINESS_SEGMENTS, getSegmentById } from './constants/segments';

// Routes
export { default as routes } from './routes';
