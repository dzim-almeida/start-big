/**
 * @fileoverview Conversão do logo da empresa em bitmap monocromático (1-bit)
 * para o comando raster do ESC/POS. Roda no browser (fetch + canvas).
 *
 * Impressora térmica só imprime preto e branco: a imagem é reduzida à largura
 * da bobina, achatada para tons de cinza e passada por um limiar (threshold).
 */

import type { RasterImage } from './escpos'

// Cache por (url + largura): decodificar e binarizar a cada impressão é caro.
// Só sucessos são cacheados — falha de rede não deve virar "sem logo" permanente.
const cache = new Map<string, RasterImage>()

interface Opcoes {
  /** Luminância (0–255) abaixo da qual o pixel vira preto. Padrão 160. */
  limiar?: number
  /** Teto de altura em pontos, evita logo gigante consumir bobina. Padrão 240. */
  alturaMaxDots?: number
}

/**
 * Carrega o logo e devolve o bitmap pronto para `EscPosBuilder.raster()`.
 * Retorna `null` se não houver URL ou se algo falhar (rede, imagem inválida,
 * canvas indisponível) — a impressão segue sem logo, nunca quebra.
 */
export async function carregarLogoRaster(
  url: string | null | undefined,
  larguraMaxDots: number,
  opts: Opcoes = {},
): Promise<RasterImage | null> {
  if (!url) return null

  const chave = `${url}@${larguraMaxDots}`
  const emCache = cache.get(chave)
  if (emCache) return emCache

  const limiar = opts.limiar ?? 160
  const alturaMax = opts.alturaMaxDots ?? 240

  try {
    const resp = await fetch(url)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const bitmap = await createImageBitmap(await resp.blob())

    // Escala mantendo proporção: cabe na largura da bobina e num teto de altura.
    let escala = Math.min(1, larguraMaxDots / bitmap.width)
    if (bitmap.height * escala > alturaMax) escala = alturaMax / bitmap.height
    const w = Math.max(1, Math.round(bitmap.width * escala))
    const h = Math.max(1, Math.round(bitmap.height * escala))

    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('canvas 2d indisponível')

    // Fundo branco: transparência (PNG/webp) deve virar papel (branco), não preto.
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, w, h)
    ctx.drawImage(bitmap, 0, 0, w, h)
    bitmap.close?.()

    const px = ctx.getImageData(0, 0, w, h).data
    const larguraBytes = Math.ceil(w / 8)
    const data = new Uint8Array(larguraBytes * h)

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4
        const a = px[i + 3]
        // Alfa 0 = transparente = branco. Senão, luminância perceptual.
        const lum = a === 0 ? 255 : 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
        if (lum < limiar) data[y * larguraBytes + (x >> 3)] |= 0x80 >> (x & 7)
      }
    }

    const raster: RasterImage = { width: w, height: h, data }
    cache.set(chave, raster)
    return raster
  } catch {
    return null
  }
}
