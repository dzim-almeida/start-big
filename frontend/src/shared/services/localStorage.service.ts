export function saveItem(key: string, value: string) {
  localStorage.setItem(key, value);
}

export function getItem(key: string) {
  try {
    const token = localStorage.getItem(key);
    return token;
  } catch {
    return null;
  }
}

export function removeItem(key: string) {
  localStorage.removeItem(key);
}
