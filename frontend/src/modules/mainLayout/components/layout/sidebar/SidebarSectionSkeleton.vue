<template>
  <div class="animate-pulse space-y-6">
    <div class="space-y-1">
      <div class="h-2.5 w-24 bg-zinc-800 rounded mx-4 mb-3 mt-1"></div>

      <div
        v-for="i in 5"
        :key="i"
        class="flex items-center space-x-3 px-4 py-3 rounded-xl border border-transparent"
      >
        <div class="w-5 h-5 bg-zinc-800 rounded shrink-0"></div>
        <div class="h-3.5 bg-zinc-800 rounded" :class="i % 2 === 0 ? 'w-24' : 'w-32'"></div>
      </div>
    </div>

    <div class="space-y-1">
      <div class="h-2.5 w-16 bg-zinc-800 rounded mx-4 mb-3"></div>

      <div
        v-for="j in 2"
        :key="`sec2-${j}`"
        class="flex items-center space-x-3 px-4 py-3 rounded-xl border border-transparent"
      >
        <div class="w-5 h-5 bg-zinc-800 rounded shrink-0"></div>
        <div class="h-3.5 bg-zinc-800 rounded w-28"></div>
      </div>
    </div>
  </div>
</template>
