import { describe, expect, it, vi } from 'vitest';

import { criarGuardaNumeracao, MENSAGEM_NUMERACAO_NAO_CONFIRMADA } from '../useNumeracaoConfirmada';
import type { FiscalConfiguracao } from '../../types/fiscal.types';

function configuracao(sobrescrita: Partial<FiscalConfiguracao> = {}): FiscalConfiguracao {
  return {
    ambiente: 2,
    ambiente_label: 'Homologação',
    mock_ativo: true,
    certificado_configurado: true,
    certificado_valido: true,
    numeracao_confirmada: true,
    ...sobrescrita,
  };
}

function montar(config: FiscalConfiguracao | undefined) {
  const avisar = vi.fn();
  const irParaConfiguracoes = vi.fn();
  const garantir = criarGuardaNumeracao({
    obterConfiguracao: () => config,
    avisar,
    irParaConfiguracoes,
  });
  return { garantir, avisar, irParaConfiguracoes };
}

describe('criarGuardaNumeracao', () => {
  it('bloqueia e avisa quando a configuração em cache diz não confirmada', () => {
    const { garantir, avisar } = montar(configuracao({ numeracao_confirmada: false }));

    expect(garantir()).toBe(false);
    expect(avisar).toHaveBeenCalledTimes(1);
    expect(avisar).toHaveBeenCalledWith(
      MENSAGEM_NUMERACAO_NAO_CONFIRMADA.titulo,
      MENSAGEM_NUMERACAO_NAO_CONFIRMADA.descricao,
      expect.objectContaining({ label: MENSAGEM_NUMERACAO_NAO_CONFIRMADA.acao }),
    );
  });

  it('o botão do aviso leva para a tela de configurações', () => {
    const { garantir, avisar, irParaConfiguracoes } = montar(
      configuracao({ numeracao_confirmada: false }),
    );
    garantir();

    const [, , acao] = avisar.mock.calls[0];
    acao.onClick();
    expect(irParaConfiguracoes).toHaveBeenCalledTimes(1);
  });

  it('libera quando confirmada, sem aviso', () => {
    const { garantir, avisar } = montar(configuracao({ numeracao_confirmada: true }));

    expect(garantir()).toBe(true);
    expect(avisar).not.toHaveBeenCalled();
  });

  it('sem configuração em cache não adivinha: libera e deixa o backend decidir', () => {
    const { garantir, avisar } = montar(undefined);

    expect(garantir()).toBe(true);
    expect(avisar).not.toHaveBeenCalled();
  });
});
