import { Stronghold } from "@tauri-apps/plugin-stronghold";
import { appDataDir, join } from '@tauri-apps/api/path';

import { getOrGenerateVaultPass } from "./storageManager.service";

// Constantes para organizar
const STRONGHOLD_FILE = 'vault.hold';
const CLIENT_NAME = 'start-client';

// Cache do Stronghold e Client para evitar reinicializações
let stronghold: Stronghold | null = null;
let cachedClient: Awaited<ReturnType<Stronghold['loadClient']>> | null = null;
let initPromise: Promise<Stronghold> | null = null;

/**
 * Inicializa o Stronghold. Deve ser chamado antes de usar.
 * Usa singleton com promise para evitar inicializações paralelas.
 */
export async function initStronghold(): Promise<Stronghold> {
    if (stronghold) return stronghold;

    // Evita múltiplas inicializações paralelas
    if (initPromise) return initPromise;

    initPromise = (async () => {
        console.time('[SecureStorage] initStronghold-total');

        console.time('[SecureStorage] getOrGenerateVaultPass');
        const VAULT_PASS = await getOrGenerateVaultPass();
        console.timeEnd('[SecureStorage] getOrGenerateVaultPass');

        // Define onde o arquivo será salvo (AppData do usuário)
        console.time('[SecureStorage] appDataDir');
        const path = await appDataDir();
        console.timeEnd('[SecureStorage] appDataDir');

        console.time('[SecureStorage] join');
        const vaultPath = await join(path, STRONGHOLD_FILE);
        console.timeEnd('[SecureStorage] join');

        //Cria arquivo criptografado
        console.time('[SecureStorage] Stronghold.load');
        stronghold = await Stronghold.load(vaultPath, VAULT_PASS);
        console.timeEnd('[SecureStorage] Stronghold.load');

        console.timeEnd('[SecureStorage] initStronghold-total');
        return stronghold;
    })();

    return initPromise;
}

/**
 * Retorna o client cacheado ou carrega/cria um novo.
 */
async function getClient(sh: Stronghold) {
    if (cachedClient) return cachedClient;

    console.time('[SecureStorage] getClient');
    try {
        console.time('[SecureStorage] loadClient');
        cachedClient = await sh.loadClient(CLIENT_NAME);
        console.timeEnd('[SecureStorage] loadClient');
    } catch {
        console.timeEnd('[SecureStorage] loadClient');
        console.time('[SecureStorage] createClient');
        cachedClient = await sh.createClient(CLIENT_NAME);
        console.timeEnd('[SecureStorage] createClient');
    }
    console.timeEnd('[SecureStorage] getClient');

    return cachedClient;
}

/**
 * Salva um valor (string) de forma segura
 */
export async function saveSecret(key: string, value: string): Promise<void> {
    console.time(`[SecureStorage] saveSecret(${key})-total`);

    console.time(`[SecureStorage] saveSecret-initStronghold`);
    const sh = await initStronghold();
    console.timeEnd(`[SecureStorage] saveSecret-initStronghold`);

    console.time(`[SecureStorage] saveSecret-getClient`);
    const client = await getClient(sh);
    console.timeEnd(`[SecureStorage] saveSecret-getClient`);

    console.time(`[SecureStorage] saveSecret-getStore`);
    const store = client.getStore();
    console.timeEnd(`[SecureStorage] saveSecret-getStore`);

    const encodedValue = Array.from(new TextEncoder().encode(value));

    console.time(`[SecureStorage] saveSecret-insert`);
    await store.insert(key, encodedValue);
    console.timeEnd(`[SecureStorage] saveSecret-insert`);

    console.time(`[SecureStorage] saveSecret-sh.save`);
    await sh.save();
    console.timeEnd(`[SecureStorage] saveSecret-sh.save`);

    console.timeEnd(`[SecureStorage] saveSecret(${key})-total`);
    console.log(`[SecureStorage] ${key} salvo com sucesso.`);
}

/**
 * Recupera um valor seguro
 */
export async function getSecret(key: string): Promise<string | null> {
    console.time(`[SecureStorage] getSecret(${key})-total`);

    console.time(`[SecureStorage] getSecret-initStronghold`);
    const sh = await initStronghold();
    console.timeEnd(`[SecureStorage] getSecret-initStronghold`);

    let client;

    try {
        console.time(`[SecureStorage] getSecret-getClient`);
        client = await getClient(sh);
        console.timeEnd(`[SecureStorage] getSecret-getClient`);
    } catch {
        console.timeEnd(`[SecureStorage] getSecret-getClient`);
        console.timeEnd(`[SecureStorage] getSecret(${key})-total`);
        return null;
    }

    console.time(`[SecureStorage] getSecret-getStore`);
    const store = client.getStore();
    console.timeEnd(`[SecureStorage] getSecret-getStore`);

    console.time(`[SecureStorage] getSecret-store.get`);
    const data = await store.get(key);
    console.timeEnd(`[SecureStorage] getSecret-store.get`);

    console.timeEnd(`[SecureStorage] getSecret(${key})-total`);

    if (!data) return null;

    return new TextDecoder().decode(new Uint8Array(data));
}

/**
 * Remove um segredo (Usar no Logout)
 */
export async function removeSecret(key: string): Promise<void> {
    const sh = await initStronghold();
    let client;

    try {
        client = await getClient(sh);
    } catch {
        return;
    }

    const store = client.getStore();
    await store.remove(key);

    await sh.save();
    console.log(`[SecureStorage] ${key} removido com sucesso.`);
}