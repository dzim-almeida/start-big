import { defineStore } from 'pinia';
import { jwtDecode } from 'jwt-decode';
import { computed, ref } from 'vue';

import { saveSecret, getSecret, removeSecret } from '../services/secureStorage.service';
import { TokenUser } from '../types/auth.types';
import { LoginResponse } from '@/modules/auth/types/auth.types';
import { getItem } from '../services/localStorage.service';

const STORAGE_KEY = 'token';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getItem('token'));
  const user = ref<TokenUser | null>(jwtDecode((token.value) ?? ''));

  const isAuthenticated = computed(() => !!token.value);

  function setAuth(authData: LoginResponse): void {
    token.value = authData.access_token;

    try {
      user.value = jwtDecode(token.value);
    } catch {
      user.value = null;
      console.log('Erro ao decodificar o token JWT');
    }

    saveSecret(STORAGE_KEY, token.value);
  }

  async function tokenIsSaved(): Promise<boolean> {
    if (token.value !== null) return true;
    
    const checkToken = await getSecret(STORAGE_KEY);
    token.value = checkToken;
     
    if (checkToken) return true;
    
    return false;
  }

  async function logout(): Promise<void> {
    token.value = null;
    user.value = null;
    await removeSecret(STORAGE_KEY);
  }

  return {
    // refs
    token,
    user,

    // computed
    isAuthenticated,

    // metodos
    setAuth,
    tokenIsSaved,
    logout,
  }
});
