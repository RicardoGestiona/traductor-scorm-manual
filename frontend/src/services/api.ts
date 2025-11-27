/**
 * API client service para conectar con el backend FastAPI.
 *
 * Filepath: frontend/src/services/api.ts
 * Feature alignment: STORY-003 - Setup Frontend React, STORY-017 - Autenticación
 */

import { supabase } from '../contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Get authorization headers with JWT token
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
      return {
        'Authorization': `Bearer ${session.access_token}`,
      };
    }

    return {};
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
   * @requires Authentication
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

    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/v1/upload`, {
      method: 'POST',
      headers: authHeaders,
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
   * @requires Authentication
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
    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/v1/jobs/${jobId}`, {
      headers: authHeaders,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al obtener status');
    }

    return response.json();
  }

  /**
   * Obtener detalles completos de un job
   * @requires Authentication
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
    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/v1/jobs/${jobId}/details`, {
      headers: authHeaders,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al obtener detalles');
    }

    return response.json();
  }

  /**
   * Descargar paquete traducido para un idioma específico
   * @requires Authentication
   * @returns URL de descarga firmada (redirect)
   */
  async downloadTranslatedPackage(jobId: string, language: string): Promise<void> {
    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/v1/download/${jobId}/${language}`, {
      headers: authHeaders,
      redirect: 'follow',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al descargar archivo');
    }

    // Trigger download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scorm_${language}.zip`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  /**
   * Descargar todos los paquetes traducidos (bundle)
   * @requires Authentication
   */
  async downloadAllPackages(jobId: string): Promise<void> {
    const authHeaders = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/v1/download/${jobId}/all`, {
      headers: authHeaders,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Error al descargar archivos');
    }

    // Trigger download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scorm_translations.zip`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}

export const api = new ApiClient(API_BASE_URL);
