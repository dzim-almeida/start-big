<script setup lang="ts">
/**
 * @component AvisosBackupLista
 * @description Quadros de aviso da tela de backup (LIC-08 §6.3, quadro 5).
 *
 * Recebe os avisos já buscados (`GET /backup/avisos`) e escolhe o texto de cada
 * código. O texto fica só aqui: o backend manda apenas o código.
 */

import { useRouter } from 'vue-router'
import { Cloud, Lock } from 'lucide-vue-next'
import type { AvisoBackupType } from '@/modules/configuracoes/types/backup.types'

defineProps<{ avisos: AvisoBackupType[] }>()

const router = useRouter()

/** "18/11/2026" a partir de uma data ISO. */
function formatarDia(iso: string): string {
  const data = new Date(iso)
  return Number.isNaN(data.getTime()) ? '' : data.toLocaleDateString('pt-BR')
}

/** Título e texto de cada código (tabela da §6.3). */
function textoDoAviso(aviso: AvisoBackupType): { titulo: string; texto: string } {
  switch (aviso.codigo) {
    case 'TRIAL_BACKUP_USADO': {
      const dia = aviso.feito_em ? formatarDia(aviso.feito_em) : ''
      return {
        titulo: 'Backup na nuvem do período de teste já usado',
        texto: dia
          ? `Período de teste: 1 backup na nuvem, feito em ${dia}. Assine para ter backups contínuos.`
          : 'Período de teste: o backup na nuvem já foi feito. Assine para ter backups contínuos.',
      }
    }
    case 'TRIAL':
      return { titulo: 'Backup na nuvem indisponível', texto: 'O backup na nuvem não está disponível no período de teste.' }
    case 'LICENCA_VENCIDA':
      return {
        titulo: 'Backup na nuvem parado',
        texto: 'Licença vencida: o backup na nuvem volta quando a assinatura for renovada.',
      }
    case 'LICENCA_SUSPENSA':
    case 'LICENCA_BLOQUEADA':
    case 'LICENCA_REVOGADA':
      return {
        titulo: 'Backup na nuvem parado',
        texto: 'A licença não está ativa: o backup na nuvem está parado. Fale com o suporte.',
      }
    case 'BACKUP_MAQUINA_REVOGADA':
    case 'LICENCA_HWID_REVOGADO':
      return {
        titulo: 'Backup na nuvem parado',
        texto: 'Este computador não é mais o servidor da licença. O backup na nuvem está parado.',
      }
    case 'BACKUP_HWID_AUSENTE':
      return {
        titulo: 'Backup na nuvem parado',
        texto: 'O backup na nuvem está parado por um problema na licença. Entre de novo com a conta StartBig.',
      }
    case 'PASTA_DADOS_ABERTA':
      return {
        titulo: 'Pasta de dados aberta',
        texto:
          'A pasta de dados do sistema está aberta para outros usuários deste computador. Peça ao técnico para restringir o acesso.',
      }
    default:
      return { titulo: 'Backup na nuvem não concluído', texto: 'O backup na nuvem não foi concluído. Tente de novo mais tarde.' }
  }
}

/** A pasta aberta é um risco de segurança (vermelho); os outros são atenção (âmbar). */
function ehGrave(codigo: string): boolean {
  return codigo === 'PASTA_DADOS_ABERTA'
}
</script>

<template>
  <!-- Nada a avisar: não desenha nada -->
  <div v-if="avisos.length" class="flex flex-col gap-2.5">
    <div
      v-for="aviso in avisos"
      :key="aviso.codigo"
      data-testid="aviso-backup"
      role="status"
      class="rounded-xl border px-4 py-3.5 flex items-start gap-3"
      :class="ehGrave(aviso.codigo) ? 'bg-red-50 border-red-100' : 'bg-amber-50 border-amber-200'"
    >
      <div
        class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
        :class="ehGrave(aviso.codigo) ? 'bg-red-100' : 'bg-amber-100'"
      >
        <Lock v-if="ehGrave(aviso.codigo)" :size="16" class="text-red-600" aria-hidden="true" />
        <Cloud v-else :size="16" class="text-amber-700" aria-hidden="true" />
      </div>
      <div class="flex-1 flex flex-col gap-0.5">
        <p class="text-sm font-semibold" :class="ehGrave(aviso.codigo) ? 'text-red-700' : 'text-amber-800'">
          {{ textoDoAviso(aviso).titulo }}
        </p>
        <p class="text-[13px] leading-relaxed" :class="ehGrave(aviso.codigo) ? 'text-red-700' : 'text-amber-800'">
          {{ textoDoAviso(aviso).texto }}
        </p>
      </div>
      <!-- Trial: "Assinar" leva à tela de renovação que já existe -->
      <button
        v-if="aviso.codigo === 'TRIAL_BACKUP_USADO'"
        type="button"
        class="self-center min-h-9 px-3.5 border border-brand-primary rounded-md text-brand-primary text-xs font-semibold cursor-pointer hover:bg-white"
        @click="router.push({ name: 'licenca.renovar' })"
      >Assinar</button>
    </div>
  </div>
</template>
