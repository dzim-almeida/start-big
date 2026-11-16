import { describe, expect, it } from 'vitest';

import { resolverDesfechoInutilizacao } from '../useFiscalInutilizarMutation';
import { avisoViradaDeAno } from '../../utils/numeracao.utils';
import type { InutilizacaoRead } from '../../types/fiscal.types';

function registro(status: string, extra: Partial<InutilizacaoRead> = {}): InutilizacaoRead {
  return {
    id: 1, serie: 1, ano: 2026, numero_inicial: 3, numero_final: 4,
    justificativa: 'Numeros queimados por falha de transmissao', status, ...extra,
  };
}

describe('resolverDesfechoInutilizacao', () => {
  it('homologada é sucesso, com o protocolo', () => {
    const d = resolverDesfechoInutilizacao(registro('HOMOLOGADA', { protocolo: '135260000000001' }));
    expect(d.tipo).toBe('sucesso');
    expect(d.titulo).toContain('nº 3 a 4');
    expect(d.descricao).toContain('135260000000001');
  });

  it('número único não diz "a"', () => {
    const d = resolverDesfechoInutilizacao(registro('HOMOLOGADA', { numero_final: 3 }));
    expect(d.titulo).toContain('nº 3 (série 1)');
    expect(d.titulo).not.toContain(' a ');
  });

  it('rejeitada pela SEFAZ manda olhar a mensagem dela', () => {
    const d = resolverDesfechoInutilizacao(registro('REJEITADA', { mensagem_sefaz: 'Rejeicao: faixa ja inutilizada' }));
    expect(d.tipo).toBe('rejeitada');
    expect(d.titulo).toContain('SEFAZ');
    expect(d.descricao).toBe('Rejeicao: faixa ja inutilizada');
  });

  it('não transmitida é diferente de rejeitada: a faixa continua aberta', () => {
    const d = resolverDesfechoInutilizacao(registro('NAO_TRANSMITIDA', {
      mensagem_sefaz: 'A plataforma recusou a inutilização (HTTP 404) antes de enviar a SEFAZ.',
    }));
    expect(d.tipo).toBe('nao_transmitida');
    expect(d.titulo).toContain('não chegou');
    expect(d.descricao).toContain('continua aberta');
    expect(d.descricao).toContain('configuração');
  });

  it('indeterminada manda NÃO pedir de novo', () => {
    const d = resolverDesfechoInutilizacao(registro('INDETERMINADA'));
    expect(d.tipo).toBe('incerta');
    expect(d.descricao).toContain('Não peça de novo');
  });

  it('processando é aguardar, não erro', () => {
    expect(resolverDesfechoInutilizacao(registro('PROCESSANDO')).tipo).toBe('aguardando');
    expect(resolverDesfechoInutilizacao(registro('PENDENTE')).tipo).toBe('aguardando');
  });
});

describe('avisoViradaDeAno', () => {
  it('em dezembro pede para resolver antes da virada', () => {
    const a = avisoViradaDeAno(new Date(2026, 11, 10));
    expect(a?.nivel).toBe('atencao');
    expect(a?.titulo).toContain('2026');
    expect(a?.detalhe).toContain('antes da virada');
  });

  it('em janeiro alerta sobre faixas do ano anterior', () => {
    const a = avisoViradaDeAno(new Date(2027, 0, 5));
    expect(a?.nivel).toBe('alerta');
    expect(a?.titulo).toContain('2026');
  });

  it('no resto do ano fica calado — aviso permanente vira ruído', () => {
    for (const mes of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) {
      expect(avisoViradaDeAno(new Date(2026, mes, 15))).toBeNull();
    }
  });
});
