/**
 * Avisos da tela de backup (LIC-08 §6.3, CT-06 a CT-09).
 *
 * Testamos o componente que desenha a lista (`AvisosBackupLista`): ele recebe
 * os avisos já buscados e só decide o texto de cada código.
 */
import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

// O botão "Assinar" navega pelo router; nos testes ele é simulado.
const push = vi.fn();
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));

import AvisosBackupLista from '../components/sections/backup-dados/components/AvisosBackupLista.vue';

describe('AvisosBackupLista', () => {
  it('CT-06: TRIAL_BACKUP_USADO mostra o texto do trial com a data e o botão Assinar', async () => {
    const tela = mount(AvisosBackupLista, {
      props: { avisos: [{ codigo: 'TRIAL_BACKUP_USADO', desde: '2026-11-19T08:00:00', feito_em: '2026-11-18T10:00:00' }] },
    });
    expect(tela.text()).toContain('Período de teste: 1 backup na nuvem, feito em 18/11/2026.');
    expect(tela.text()).toContain('Assine para ter backups contínuos.');
    const assinar = tela.findAll('button').find((b) => b.text() === 'Assinar');
    await assinar!.trigger('click');
    expect(push).toHaveBeenCalledWith({ name: 'licenca.renovar' });
  });

  it('CT-06b: sem a data, o texto do trial não fica pela metade', () => {
    const tela = mount(AvisosBackupLista, { props: { avisos: [{ codigo: 'TRIAL_BACKUP_USADO', desde: '2026-11-19T08:00:00' }] } });
    expect(tela.text()).toContain('Período de teste: o backup na nuvem já foi feito.');
    expect(tela.text()).not.toContain('feito em');
  });

  it('CT-07: PASTA_DADOS_ABERTA mostra o texto da pasta aberta', () => {
    const tela = mount(AvisosBackupLista, { props: { avisos: [{ codigo: 'PASTA_DADOS_ABERTA', desde: '2026-11-19T08:00:00' }] } });
    expect(tela.text()).toContain(
      'A pasta de dados do sistema está aberta para outros usuários deste computador. Peça ao técnico para restringir o acesso.',
    );
  });

  it('CT-08: código desconhecido mostra o texto genérico', () => {
    const tela = mount(AvisosBackupLista, { props: { avisos: [{ codigo: 'QUALQUER_COISA', desde: '2026-11-19T08:00:00' }] } });
    expect(tela.text()).toContain('O backup na nuvem não foi concluído. Tente de novo mais tarde.');
  });

  it('CT-09: lista vazia não mostra nenhum quadro', () => {
    const tela = mount(AvisosBackupLista, { props: { avisos: [] } });
    expect(tela.find('[data-testid="aviso-backup"]').exists()).toBe(false);
  });

  it('CA-07: os códigos da API antiga (TRIAL, LICENCA_*) também têm texto', () => {
    const tela = mount(AvisosBackupLista, {
      props: {
        avisos: [
          { codigo: 'TRIAL', desde: '2026-11-19T08:00:00' },
          { codigo: 'LICENCA_SUSPENSA', desde: '2026-11-19T08:00:00' },
          { codigo: 'BACKUP_MAQUINA_REVOGADA', desde: '2026-11-19T08:00:00' },
        ],
      },
    });
    expect(tela.text()).toContain('O backup na nuvem não está disponível no período de teste.');
    expect(tela.text()).toContain('A licença não está ativa: o backup na nuvem está parado. Fale com o suporte.');
    expect(tela.text()).toContain('Este computador não é mais o servidor da licença. O backup na nuvem está parado.');
    expect(tela.findAll('[data-testid="aviso-backup"]')).toHaveLength(3);
  });
});
