/**
 * Testes do BaseConfirmModal sem `v-html` (LIC-04 §6.3, D-17).
 *
 * O modal usa <Teleport to="body">: o conteúdo vai para o fim do <body>, fora
 * do componente montado. Por isso os testes procuram em `document.body`.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import BaseConfirmModal from '../BaseConfirmModal.vue';

const ATAQUE = '<img src=x onerror="window.invadido=true">';
let montado: VueWrapper | null = null;

/** Monta o modal aberto, com as props e slots pedidos. */
function abrir(props: Record<string, unknown>, slots: Record<string, string> = {}) {
  montado = mount(BaseConfirmModal, {
    props: { isOpen: true, title: 'Confirmar', ...props },
    slots,
    attachTo: document.body, // o Teleport precisa de um body de verdade
  });
  return document.body;
}

afterEach(() => {
  montado?.unmount(); // tira o modal do body entre um teste e outro
  montado = null;
  document.body.innerHTML = '';
});

describe('BaseConfirmModal', () => {
  it('CT-09: texto com <img onerror> aparece como texto, sem virar elemento', () => {
    const body = abrir({ description: `Excluir ${ATAQUE}?` });
    expect(body.querySelector('img')).toBeNull();
    expect(body.textContent).toContain(ATAQUE); // aparece igual ao digitado
  });

  it('CT-09b: o nome em negrito (trecho) também é escapado', () => {
    const body = abrir({ description: ['Excluir o móvel ', { negrito: ATAQUE }, '?'] });
    expect(body.querySelector('img')).toBeNull();
    const negrito = body.querySelector('strong');
    expect(negrito?.textContent).toBe(ATAQUE);
    expect(body.textContent).toContain('Excluir o móvel ');
  });

  it('CT-10: slot com <b> e interpolação aplica o negrito ao valor escapado', () => {
    const body = abrir(
      {},
      // O slot é um template Vue: {{ }} escapa o valor, o <b> é do template.
      { description: `<template #description>Ativar o serviço <b>{{ '${ATAQUE.replace(/"/g, '&quot;')}' }}</b>?</template>` },
    );
    expect(body.querySelector('img')).toBeNull();
    expect(body.querySelector('b')?.textContent).toBe(ATAQUE);
  });

  it('CT-11: o modal não tem v-html no template', () => {
    // Lê o arquivo do componente e confere que a diretiva não existe mais
    const fonte = readFileSync(resolve(__dirname, '../BaseConfirmModal.vue'), 'utf-8');
    expect(fonte).not.toContain('v-html');
  });
});
