const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/iss/now';
export async function fetchIssNow() {
    const response = await fetch(API_URL, {
        cache: 'no-store',
    });
    if (!response.ok) {
        throw new Error(`Upstream error: ${response.status}`);
    }
    return response.json();
}
