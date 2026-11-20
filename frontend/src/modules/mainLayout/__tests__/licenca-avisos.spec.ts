/**
 * Avisos de licença no layout principal (LIC-08 §6.1, CT-10 e CT-11).
 *
 * A resposta de /licenca/status é simulada pelo composable de consulta.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import { mount } from '@vue/test-utils';

// Resposta de /licenca/status que cada teste escolhe
const status = ref<Record<string, unknown> | undefined>(undefined);
vi.mock('@/shared/composables/useLicencaStatusQuery', () => ({
  useLicencaStatusQuery: () => ({ data: status, isLoading: ref(false), isError: ref(false) }),
}));
// O badge usa a store de autenticação, o layout e o opener do Tauri
vi.mock('@/shared/stores/auth.store', () => ({ useAuthStore: () => ({ userData: ref({ is_master: true }) }) }));
vi.mock('pinia', async (original) => ({
  ...(await original<typeof import('pinia')>()),
  storeToRefs: (store: Record<string, unknown>) => store,
}));
vi.mock('../store/layout.store', () => ({ useLayoutStore: () => ({ abrirRenovacao: vi.fn() }) }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));

import FaixaAvisoRelogio from '../components/ui/FaixaAvisoRelogio.vue';
import LicencaStatusBadge from '../components/ui/LicencaStatusBadge.vue';

beforeEach(() => {
  status.value = undefined;
});

describe('avisos de licença', () => {
  it('CT-10: relógio recuado mostra a faixa, que não bloqueia nem tem botão de fechar', () => {
    status.value = { status: 'offline_valid', dias_restantes: 20, aviso: 'relogio_recuou' };
    const faixa = mount(FaixaAvisoRelogio);
    expect(faixa.text()).toContain('O relógio deste computador está atrasado.');
    expect(faixa.text()).toContain('Ajuste a data e a hora do Windows para a licença continuar funcionando sem internet.');
    expect(faixa.find('[role="status"]').exists()).toBe(true); // aviso, não diálogo que bloqueia
    expect(faixa.find('button').exists()).toBe(false);          // sem "fechar"
  });

  it('CT-10b: sem o aviso, a faixa some', () => {
    status.value = { status: 'online_valid', dias_restantes: 20 };
    const faixa = mount(FaixaAvisoRelogio);
    expect(faixa.text()).toBe('');
  });

  it('CT-11: estimativa mostra "(estimado, sem internet)" ao lado dos dias', () => {
    status.value = { status: 'offline_valid', dias_restantes: 9, trial: true, estimativa: true };
    const badge = mount(LicencaStatusBadge);
    expect(badge.text()).toContain('Trial • 9 dias');
    expect(badge.text()).toContain('(estimado, sem internet)');
  });

  it('com a API informando os dias, não mostra o rótulo', () => {
    status.value = { status: 'online_valid', dias_restantes: 9, trial: true, estimativa: false };
    const badge = mount(LicencaStatusBadge);
    expect(badge.text()).not.toContain('estimado');
  });
});
