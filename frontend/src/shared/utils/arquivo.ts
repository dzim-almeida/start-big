import { isTauri } from '@tauri-apps/api/core';

/** `cancelado`: o usuário fechou a janela "Salvar como" sem escolher local. */
export type ResultadoSalvarArquivo =
  | { cancelado: true }
  | { cancelado: false; caminho: string | null };

const FILTROS: Record<string, string> = {
  pdf: 'PDF',
  xml: 'XML',
  zip: 'Arquivo ZIP',
};

/**
 * Pergunta ao usuário onde salvar (janela "Salvar como" do Windows). Devolve
 * o caminho escolhido, null se cancelou, ou undefined se a janela não pôde
 * ser aberta (sem o plugin/permissão) — aí cai no comportamento antigo.
 */
async function perguntarOndeSalvar(nome: string): Promise<string | null | undefined> {
  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { downloadDir, join } = await import('@tauri-apps/api/path');
    const extensao = nome.split('.').pop()?.toLowerCase() ?? '';
    let sugestao = nome;
    try {
      sugestao = await join(await downloadDir(), nome);
    } catch {
      /* sem pasta Downloads — o Windows sugere a última usada */
    }
    return await save({
      defaultPath: sugestao,
      filters: FILTROS[extensao] ? [{ name: FILTROS[extensao], extensions: [extensao] }] : undefined,
    });
  } catch {
    return undefined;
  }
}

/**
 * Entrega um arquivo binário ao usuário:
 * - No app (Tauri/WebView bloqueia download por blob): abre o "Salvar como"
 *   do Windows, grava onde o usuário escolher e tenta abrir no programa
 *   padrão. Se a janela não abrir, grava na pasta de dados do app (como antes).
 * - No navegador (dev): download por blob; caminho null.
 */
export async function salvarArquivo(nome: string, conteudo: Blob): Promise<ResultadoSalvarArquivo> {
  if (isTauri()) {
    const { writeFile, BaseDirectory } = await import('@tauri-apps/plugin-fs');
    const bytes = new Uint8Array(await conteudo.arrayBuffer());

    let caminho = await perguntarOndeSalvar(nome);
    if (caminho === null) return { cancelado: true };
    if (caminho) {
      await writeFile(caminho, bytes);
    } else {
      const { appLocalDataDir, join } = await import('@tauri-apps/api/path');
      await writeFile(nome, bytes, { baseDir: BaseDirectory.AppLocalData });
      caminho = await join(await appLocalDataDir(), nome);
    }

    try {
      const { openPath } = await import('@tauri-apps/plugin-opener');
      await openPath(caminho);
    } catch {
      /* sem permissão de abrir — o arquivo já está salvo no caminho devolvido */
    }
    return { cancelado: false, caminho };
  }

  const url = URL.createObjectURL(conteudo);
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
  return { cancelado: false, caminho: null };
}
