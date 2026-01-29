export function maskCpfCnpj(document: string): string {
    if (!document) return '';
    if (document.length === 11) {
        return document.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    if (document.length === 14) {
        return document.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return document
}

export function maskPhoneNumber(number: string): string {
    if (!number) return '';
    if (number.length === 10) {
        return number.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
    }
    if (number.length === 11) {
        return number.replace(/(\d{2})(\d{1})(\d{4})(\d{4})/, '($1) $2.$3-$4')
    }
    return number;
}