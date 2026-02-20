import { AuthResponse } from '../app.model';

export function persistAuthTokens(response: AuthResponse): void {
  try {
    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
    }
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token);
    }
  } catch (error) {
    console.warn('Could not persist auth tokens', error);
  }
}

export function clearAuthTokens(): void {
  try {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  } catch (error) {
    console.warn('Could not clear auth tokens', error);
  }
}
