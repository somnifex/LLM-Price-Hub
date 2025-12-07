import CryptoJS from 'crypto-js';

/**
 * Generate encryption key from password and salt using PBKDF2
 */
export function generateKey(password: string, salt: string): string {
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 10000
    });
    return key.toString();
}

/**
 * Encrypt text using AES
 */
export function encrypt(text: string, password: string, salt: string): string {
    const key = generateKey(password, salt);
    const encrypted = CryptoJS.AES.encrypt(text, key);
    return encrypted.toString();
}

/**
 * Decrypt ciphertext using AES
 */
export function decrypt(ciphertext: string, password: string, salt: string): string {
    const key = generateKey(password, salt);
    const decrypted = CryptoJS.AES.decrypt(ciphertext, key);
    return decrypted.toString(CryptoJS.enc.Utf8);
}

/**
 * Generate a random salt
 */
export function generateSalt(): string {
    return CryptoJS.lib.WordArray.random(128 / 8).toString();
}

/**
 * Verify password by attempting to decrypt the verification string
 */
export function verifyPassword(password: string, salt: string, verification: string): boolean {
    try {
        const decrypted = decrypt(verification, password, salt);
        return decrypted === 'VERIFIED';
    } catch {
        return false;
    }
}
