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

  /**
   * Upload SCORM package para traducción
   */
  async uploadScorm(
    file: File,
    sourceLang: string,
    targetLangs: string[]
  ): Promise<{
    job_id: string;
    status: string;
    message: string;
    original_filename: string;
    created_at: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_language', sourceLang);
    formData.append('target_languages', targetLangs.join(','));

    const response = await fetch(`${this.baseURL}/api/v1/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al subir archivo');
    }

    return response.json();
  }

  /**
   * Obtener status de un job de traducción (para polling)
   */
  async getJobStatus(jobId: string): Promise<{
    job_id: string;
    status: string;
    progress_percentage: number;
    current_step: string;
    download_urls: Record<string, string>;
    error_message?: string;
    estimated_completion?: string;
  }> {
    const response = await fetch(`${this.baseURL}/api/v1/jobs/${jobId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al obtener status');
    }

    return response.json();
  }

  /**
   * Obtener detalles completos de un job
   */
  async getJobDetails(jobId: string): Promise<{
    id: string;
    original_filename: string;
    storage_path?: string;
    scorm_version?: string;
    source_language: string;
    target_languages: string[];
    status: string;
    progress_percentage: number;
    created_at: string;
    completed_at?: string;
    download_urls: Record<string, string>;
    error_message?: string;
  }> {
    const response = await fetch(`${this.baseURL}/api/v1/jobs/${jobId}/details`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al obtener detalles');
    }

    return response.json();
  }

  /**
   * Obtener URL de descarga para un idioma específico
   */
  getDownloadUrl(jobId: string, language: string): string {
    return `${this.baseURL}/api/v1/download/${jobId}/${language}`;
  }

  /**
   * Obtener URL de descarga de todos los idiomas (bundle)
   */
  getDownloadAllUrl(jobId: string): string {
    return `${this.baseURL}/api/v1/download/${jobId}/all`;
  }
}

export const api = new ApiClient(API_BASE_URL);
