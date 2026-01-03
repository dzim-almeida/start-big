<template>
  <div class="w-32 h-32 mx-auto relative">
    <!-- Círculo de fundo animado -->
    <div
      class="absolute inset-0 bg-linear-to-br from-brand-primary/20 to-brand-secondary/20 rounded-full animate-pulse"
    ></div>

    <!-- Ícone de foguete -->
    <svg
      class="w-full h-full p-6 text-brand-primary relative"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Foguete -->
      <path
        d="M32 4C32 4 16 16 16 36C16 44 20 52 32 56C44 52 48 44 48 36C48 16 32 4 32 4Z"
        fill="currentColor"
        opacity="0.2"
      />
      <path
        d="M32 8C32 8 20 18 20 34C20 40 23 46 32 50C41 46 44 40 44 34C44 18 32 8 32 8Z"
        fill="currentColor"
      />
      <!-- Janela -->
      <circle cx="32" cy="26" r="6" fill="white" opacity="0.9" />
      <circle cx="32" cy="26" r="4" fill="#E3F2FD" />
      <!-- Chamas -->
      <path d="M28 52L32 60L36 52" fill="#FF9800" />
      <path d="M30 52L32 58L34 52" fill="#FFCA28" />
      <!-- Asas -->
      <path d="M16 40L20 36V44L16 40Z" fill="currentColor" opacity="0.7" />
      <path d="M48 40L44 36V44L48 40Z" fill="currentColor" opacity="0.7" />
    </svg>

    <!-- Partículas decorativas -->
    <div
      class="absolute -top-2 -right-2 w-3 h-3 bg-brand-secondary rounded-full animate-bounce"
      style="animation-delay: 0.1s"
    ></div>
    <div
      class="absolute top-4 -left-4 w-2 h-2 bg-brand-primary rounded-full animate-bounce"
      style="animation-delay: 0.3s"
    ></div>
    <div
      class="absolute -bottom-1 right-4 w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce"
      style="animation-delay: 0.5s"
    ></div>
  </div>
</template>
