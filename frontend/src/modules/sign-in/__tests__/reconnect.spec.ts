/**
 * Testes do re-login, das mensagens por código e dos avisos (LIC-03, CT-14 a CT-20).
 *
 * Os componentes são montados no jsdom (o "navegador de mentira" do Vitest).
 * Tudo que fala com o backend ou com o Tauri é simulado com `vi.mock`, então
 * os testes só olham o que a TELA faz.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';

// --- Simulações (vêm antes dos imports dos componentes) ---------------------

// O service do sign-in: nenhuma chamada de verdade ao backend.
const restaurarBackupDaNuvem = vi.fn();
const reenviarLink = vi.fn();
vi.mock('../services/sign-in.service', () => ({
  restaurarBackupDaNuvem: (...args: unknown[]) => restaurarBackupDaNuvem(...args),
  reenviarLink: (...args: unknown[]) => reenviarLink(...args),
  reconnectLicenca: vi.fn(),
  setupSistema: vi.fn(),
  uploadEmpresaLogo: vi.fn(),
}));

// A transferência de licença (tela de troca de servidor).
const transferirLicenca = vi.fn();
vi.mock('@/modules/license/services/transferencia.service', () => ({
  transferirLicenca: (...args: unknown[]) => transferirLicenca(...args),
}));

// Router, Tauri e a store da licença não existem nos testes.
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }) }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));
vi.mock('@/shared/stores/licenca.store', () => ({ useLicencaStore: () => ({ limpar: vi.fn() }) }));

import {
  MENSAGENS_DE_CODIGO,
  lerErroDaLicenca,
  mensagemDoCodigo,
} from '@/shared/services/licenca.service';
import { useSignIn } from '../composables/useSignIn';
import EscolhaRestauracaoStep from '../components/steps/EscolhaRestauracaoStep.vue';
import ConfirmarEmailStep from '../components/steps/ConfirmarEmailStep.vue';
import ResponsavelStep from '../components/steps/ResponsavelStep.vue';
import TransferirLicencaView from '@/modules/license/views/TransferirLicencaView.vue';

const TITULAR_PJ = {
  tipoPessoa: 'PJ',
  nomeOuRazao: 'Loja Exemplo Ltda',
  documento: '11.222.333/0001-81',
  nomeFantasia: 'Loja Exemplo',
  telefone: null,
  celular: '(85) 99999-0000',
  endereco: null,
};

beforeEach(() => {
  useSignIn().resetSignIn(); // o estado do sign-in é único (singleton): zera entre testes
  vi.clearAllMocks();
});

afterEach(() => {
  document.body.innerHTML = ''; // modais com Teleport vão para o body
});

// --- CT-15 a CT-18: mensagens por código -------------------------------------

describe('mensagens por código (§6.4)', () => {
  it('CT-15: código conhecido mostra o texto da tabela', () => {
    expect(mensagemDoCodigo('LICENCA_DE_OUTRA_CONTA')).toBe('Esta conta não é dona da licença deste computador.');
  });

  it('CT-16: código desconhecido mostra a mensagem genérica, nunca o texto técnico', () => {
    expect(mensagemDoCodigo('Expecting value: line 1 column 1')).toBe(
      'Não foi possível concluir agora. Tente de novo em instantes.',
    );
    expect(mensagemDoCodigo(undefined)).toBe('Não foi possível concluir agora. Tente de novo em instantes.');
  });

  it('CT-17: todo código das specs LIC-01 a LIC-09 que chega à tela tem mensagem', () => {
    // Códigos que o backend local ou a API devolvem a uma tela do app.
    // Ficam de fora os que nunca chegam à tela: TOKEN_CONFIRMACAO_* (página web),
    // SESSAO_INEXISTENTE e HEARTBEAT_LICENCA_DIVERGENTE (só o heartbeat os vê).
    const codigos = [
      // LIC-01
      'COFRE_INDISPONIVEL', 'TOKEN_ILEGIVEL', 'CHAVE_ATIVACAO_ILEGIVEL', 'BACKUP_CHAVE_INVALIDA',
      'LICENCA_DE_OUTRA_MAQUINA',
      // LIC-02
      'TOKEN_DE_OUTRA_LICENCA', 'CHAVE_CORROMPIDA', 'LICENCA_TRANSFERIDA',
      // LIC-03
      'LICENCA_DE_OUTRA_CONTA', 'BACKUP_INEXISTENTE', 'RESTAURACAO_JA_PENDENTE', 'CREDENCIAIS_INVALIDAS',
      'CONTA_RECUSADA', 'SEM_CONEXAO', 'NUVEM_INDISPONIVEL', 'RESPOSTA_INVALIDA',
      // LIC-04
      'FORA_DA_REDE_DA_LOJA',
      // LIC-05
      'LICENCA_HWID_REVOGADO', 'BACKUP_MAQUINA_REVOGADA', 'BACKUP_HWID_AUSENTE', 'BACKUP_TRIAL_LIMITE',
      'LICENCA_VENCIDA', 'TRIAL_BACKUP_USADO',
      // LIC-06
      'MUITAS_TENTATIVAS', 'AGUARDANDO_CONFIRMACAO_EMAIL', 'DOCUMENTO_TRAVADO', 'CONFIRMACAO_NECESSARIA',
      'SEM_LICENCA_ATIVA', 'SENHA_NAO_CONFIGURADA',
    ];
    const semMensagem = codigos.filter((codigo) => !MENSAGENS_DE_CODIGO[codigo]);
    expect(semMensagem).toEqual([]);
  });

  it('CT-18: lê o código em detail e no topo do corpo', () => {
    const emDetail = { response: { data: { error: 'x', detail: { codigo: 'SEM_CONEXAO', mensagem: 'm' } } } };
    const noTopo = { response: { data: { codigo: 'SEM_CONEXAO', mensagem: 'm' } } };
    expect(lerErroDaLicenca(emDetail)).toEqual({ codigo: 'SEM_CONEXAO', mensagem: 'm' });
    expect(lerErroDaLicenca(noTopo)).toEqual({ codigo: 'SEM_CONEXAO', mensagem: 'm' });
    expect(lerErroDaLicenca(new Error('rede'))).toEqual({ codigo: undefined, mensagem: undefined });
  });
});

// --- CT-19: escolha depois do re-login ------------------------------------------

describe('escolha depois do re-login (§6.2)', () => {
  it('CT-19: com backup, só oferece restaurar', () => {
    const { dadosRelogin, signInData } = useSignIn();
    dadosRelogin.backup = { ciclo: '2026-11-17', ultimo_envio: '2026-11-18T22:40:00Z' };
    signInData.acesso.email = 'dono@exemplo.com.br';
    const tela = mount(EscolhaRestauracaoStep);
    expect(tela.text()).toContain('Restaurar backup da nuvem');
    expect(tela.text()).toContain('Semana de 17/11/2026');
    expect(tela.text()).not.toContain('Preencher os dados da empresa');
    // E-mail preenchido e travado (D-07)
    const email = tela.find('input[type="email"]');
    expect((email.element as HTMLInputElement).value).toBe('dono@exemplo.com.br');
    expect(email.attributes('disabled')).toBeDefined();
  });

  it('CT-19b: sem backup, só oferece preencher', () => {
    useSignIn().dadosRelogin.backup = null;
    const tela = mount(EscolhaRestauracaoStep);
    expect(tela.text()).toContain('Preencher os dados da empresa');
    expect(tela.text()).toContain('Não há backup na nuvem para esta licença.');
    expect(tela.text()).not.toContain('Restaurar backup da nuvem');
  });

  it('restaurar manda a senha confirmada e vai para a tela de restauração preparada', async () => {
    const signIn = useSignIn();
    signIn.dadosRelogin.backup = { ciclo: '2026-11-17', ultimo_envio: null };
    signIn.signInData.acesso.email = 'dono@exemplo.com.br';
    restaurarBackupDaNuvem.mockResolvedValue({ status: 'pendente_reinicio', ciclo: '2026-11-17', mensagem: 'ok' });
    const tela = mount(EscolhaRestauracaoStep);
    await tela.find('input[type="password"]').setValue('senha-da-conta');
    await tela.find('form').trigger('submit');
    await flushPromises();
    expect(restaurarBackupDaNuvem).toHaveBeenCalledWith('dono@exemplo.com.br', 'senha-da-conta', '2026-11-17');
    expect(signIn.signInMode.value).toBe('restauracao-preparada');
  });

  it('erro da restauração mostra o texto do código', async () => {
    useSignIn().dadosRelogin.backup = { ciclo: '2026-11-17', ultimo_envio: null };
    restaurarBackupDaNuvem.mockRejectedValue({
      response: { data: { detail: { codigo: 'LICENCA_DE_OUTRA_CONTA', mensagem: 'x' } } },
    });
    const tela = mount(EscolhaRestauracaoStep);
    await tela.find('input[type="password"]').setValue('senha');
    await tela.find('form').trigger('submit');
    await flushPromises();
    expect(tela.text()).toContain('Esta conta não é dona da licença deste computador.');
  });
});

// --- CT-14: documento travado no setup ------------------------------------------

describe('setup com os dados da nuvem (§6.6)', () => {
  it('CT-14: o documento vindo da nuvem fica travado, sem edição', () => {
    const signIn = useSignIn();
    signIn.aplicarTitular(TITULAR_PJ);
    const tela = mount(ResponsavelStep);
    const cnpj = tela.findAll('input').find((campo) => (campo.element as HTMLInputElement).value === '11.222.333/0001-81');
    expect(cnpj).toBeDefined();
    expect(cnpj!.attributes('disabled')).toBeDefined();
    expect(tela.text()).toContain('Para alterar, fale com o suporte.');
  });

  it('sem dados da nuvem, o documento continua editável', () => {
    const tela = mount(ResponsavelStep);
    const travados = tela.findAll('input').filter((campo) => campo.attributes('disabled') !== undefined);
    expect(travados).toHaveLength(0);
  });
});

// --- CT-20: aviso de troca e cadastro 202 ----------------------------------------

describe('aviso de troca e confirmação de e-mail', () => {
  it('CT-20: o aviso de troca aparece antes de qualquer chamada à API', async () => {
    const tela = mount(TransferirLicencaView, { attachTo: document.body });
    await tela.find('input[type="email"]').setValue('dono@exemplo.com.br');
    await tela.find('input[type="password"]').setValue('senha');
    await tela.find('form').trigger('submit');
    await flushPromises();
    // A validação do formulário (vee-validate + zod) termina num tique depois:
    // `vi.waitFor` repete a conferência até ela passar (ou estourar o tempo).
    await vi.waitFor(() => expect(document.body.textContent).toContain('Trocar o servidor de computador'));
    expect(document.body.textContent).toContain('3 trocas em 30 dias');
    expect(transferirLicenca).not.toHaveBeenCalled(); // ainda não confirmou
    tela.unmount();
  });

  it('CT-20b: o cadastro com confirmação mostra a mensagem e leva ao re-login', async () => {
    const signIn = useSignIn();
    signIn.emailConfirmacao.value = 'dono@exemplo.com.br';
    signIn.signInMode.value = 'confirmar-email';
    const tela = mount(ConfirmarEmailStep);
    expect(tela.text()).toContain('Confirme o seu e-mail');
    expect(tela.text()).toContain('dono@exemplo.com.br');
    const entrar = tela.findAll('button').find((b) => b.text() === 'Já confirmei, quero entrar');
    await entrar!.trigger('click');
    expect(signIn.signInMode.value).toBe('reconnect');
  });

  it('reenviar link chama a rota local com o e-mail', async () => {
    reenviarLink.mockResolvedValue(undefined);
    useSignIn().emailConfirmacao.value = 'dono@exemplo.com.br';
    const tela = mount(ConfirmarEmailStep);
    const botao = tela.findAll('button').find((b) => b.text() === 'Reenviar link');
    await botao!.trigger('click');
    await flushPromises();
    expect(reenviarLink).toHaveBeenCalledWith('dono@exemplo.com.br');
    expect(tela.text()).toContain('Se este e-mail tiver conta, enviamos um novo link.');
  });
});
