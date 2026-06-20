<script setup lang="ts">
import { Headphones, Globe, Youtube, ExternalLink } from 'lucide-vue-next'
import BaseButton from '@/shared/components/ui/BaseButton/BaseButton.vue'
import { openUrl } from '@tauri-apps/plugin-opener'

const LINKS = {
  whatsapp: 'https://wa.me/5588996971128?text=Ol%C3%A1!%20Obrigado%20por%20entrar%20em%20contato%20com%20o%20suporte%20do%20StartBig.%20%F0%9F%91%8B%0A%0APara%20que%20eu%20possa%20direcionar%20sua%20solicita%C3%A7%C3%A3o%20o%20mais%20r%C3%A1pido%20poss%C3%ADvel%2C%20por%20favor%2C%20digite%20o%20n%C3%BAmero%20da%20op%C3%A7%C3%A3o%20que%20melhor%20descreve%20o%20que%20voc%C3%AA%20precisa%3A%0A%0A1%EF%B8%8F%E2%83%A3%20-%20D%C3%BAvidas%20sobre%20o%20sistema%20(Como%20usar)%0A2%EF%B8%8F%E2%83%A3%20-%20Relatar%20um%20erro%20ou%20instabilidade%0A3%EF%B8%8F%E2%83%A3%20-%20Sugest%C3%A3o%20de%20nova%20funcionalidade%0A4%EF%B8%8F%E2%83%A3%20-%20Assuntos%20financeiros%20%2F%20Mensalidade%0A%0APor%20favor%2C%20digite%20tamb%C3%A9m%20o%20seu%20nome%20e%20empresa.%20J%C3%A1%20volto%20para%20te%20atender',
  site: 'https://startbig.com.br',
  youtube: 'https://www.youtube.com/@StartBigOficial',
}

function abrirLink(url: string) {
  openUrl(url)
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h3 class="text-base font-bold text-zinc-900">Suporte e Ajuda</h3>
      <p class="text-sm text-zinc-500 mt-0.5">Encontre ajuda, entre em contato com o suporte e acesse recursos</p>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Contato</p>

      <div class="flex flex-col gap-2">
        <BaseButton variant="primary" size="sm" @click="abrirLink(LINKS.whatsapp)">
          <Headphones :size="14" class="mr-2" />
          Falar com Suporte
          <ExternalLink :size="12" class="ml-auto opacity-60" />
        </BaseButton>

        <BaseButton variant="ghost" size="sm" @click="abrirLink(LINKS.site)">
          <Globe :size="14" class="mr-2" />
          Site Oficial — startbig.com.br
          <ExternalLink :size="12" class="ml-auto opacity-60" />
        </BaseButton>

        <BaseButton variant="ghost" size="sm" @click="abrirLink(LINKS.youtube)">
          <Youtube :size="14" class="mr-2" />
          Tutoriais em Vídeo
          <ExternalLink :size="12" class="ml-auto opacity-60" />
        </BaseButton>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <p class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Informações do Sistema</p>

      <div class="bg-zinc-50 rounded-xl p-4 flex flex-col gap-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Versão do sistema</span>
          <span class="text-xs font-semibold text-zinc-700">1.0.0</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Última atualização</span>
          <span class="text-xs font-semibold text-zinc-700">01/06/2026</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-zinc-500">Ambiente</span>
          <span class="text-xs font-semibold text-emerald-600">Produção</span>
        </div>
      </div>
    </div>
  </div>
</template>
