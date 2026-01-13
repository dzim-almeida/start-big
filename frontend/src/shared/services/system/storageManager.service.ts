import { getPassword, setPassword } from 'tauri-plugin-keyring-api';

const SERVICE_NAME = 'StartBig_ERP';
const USER_ACCOUNT = 'db_encryption_key';

export async function getOrGenerateVaultPass(): Promise<string> {
    console.time('[StorageManager] getOrGenerateVaultPass-total');

    //Busca uma chave existente
    try {
        console.time('[StorageManager] getPassword');
        const password = await getPassword(SERVICE_NAME, USER_ACCOUNT);
        console.timeEnd('[StorageManager] getPassword');

        if (password) {
            console.log('Chave de criptografia recuperada do sistema.');
            console.timeEnd('[StorageManager] getOrGenerateVaultPass-total');
            return password;
        }
    } catch (error) {
        console.timeEnd('[StorageManager] getPassword');
        console.log("Nenhuma chave encontrada (ou erro). Criando nova...");
    }

    //Caso nao exista, cria uma nova
    const newPassword = crypto.randomUUID();

    console.time('[StorageManager] setPassword');
    await setPassword(SERVICE_NAME, USER_ACCOUNT, newPassword);
    console.timeEnd('[StorageManager] setPassword');

    console.log('Chave de criptografia gerada e salva no sistema.');
    console.timeEnd('[StorageManager] getOrGenerateVaultPass-total');
    return newPassword;
}