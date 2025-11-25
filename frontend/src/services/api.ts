/**
 * API client service para conectar con el backend FastAPI.
 *
 * Filepath: frontend/src/services/api.ts
 * Feature alignment: STORY-003 - Setup Frontend React
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Health check del backend
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) {
      throw new Error('Backend no disponible');
    }
    return response.json();
  }

  /**
   * Obtener información de la API
   */
  async getApiInfo(): Promise<{
    name: string;
    version: string;
    status: string;
    docs: string;
  }> {
    const response = await fetch(`${this.baseURL}/`);
    if (!response.ok) {
      throw new Error('No se pudo obtener información de la API');
    }
    return response.json();
  }

  // TODO-FASE-1: Añadir métodos para endpoints de traducción
  // - uploadScorm(file: File, sourceLang: string, targetLangs: string[])
  // - getJobStatus(jobId: string)
  // - getLanguages()
}

export const api = new ApiClient(API_BASE_URL);
