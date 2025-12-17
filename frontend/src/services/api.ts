/**
 * API client service para conectar con el backend FastAPI.
 *
 * Filepath: frontend/src/services/api.ts
 * Feature alignment: STORY-003 - Setup Frontend React, STORY-017 - Autenticacion
 *
 * SECURITY FIXES:
 * - HIGH-006: Sanitized error messages
 * - CRIT-002: CSRF token support (ready for backend implementation)
 */

import { supabase } from '../contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// SECURITY FIX: Environment-aware logging (MED-002)
const isDevelopment = import.meta.env.DEV;
const secureLog = {
  error: (...args: unknown[]) => {
    if (isDevelopment) {
      console.error(...args);
    }
  },
  warn: (...args: unknown[]) => {
    if (isDevelopment) {
      console.warn(...args);
    }
  },
};

// SECURITY FIX: Sanitized error messages (HIGH-006)
const ERROR_MESSAGES: Record<number, string> = {
  400: 'Solicitud invalida. Verifica los datos ingresados.',
  401: 'Sesion expirada. Por favor inicia sesion nuevamente.',
  403: 'No tienes permiso para esta accion.',
  404: 'Recurso no encontrado.',
  413: 'El archivo es demasiado grande.',
  422: 'Los datos proporcionados no son validos.',
  429: 'Demasiadas solicitudes. Intenta mas tarde.',
  500: 'Error del servidor. Intenta mas tarde.',
  502: 'Servicio temporalmente no disponible.',
  503: 'Servicio en mantenimiento. Intenta mas tarde.',
};

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Get authorization headers with JWT token and CSRF protection
   * SECURITY FIX: Added X-Requested-With header for CSRF protection (CRIT-002)
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();

    const headers: HeadersInit = {
      // SECURITY: CSRF protection - this header cannot be set by cross-origin requests
      'X-Requested-With': 'XMLHttpRequest',
    };

    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }

    return headers;
  }

  /**
   * SECURITY FIX: Handle API errors with sanitized messages (HIGH-006)
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.ok) {
      return response.json() as Promise<T>;
    }

    // Log detailed error only in development
    if (isDevelopment) {
      try {
        const errorBody = await response.clone().text();
        secureLog.error('API Error:', response.status, errorBody);
      } catch {
        // Ignore logging errors
      }
    }

    // Handle authentication errors
    if (response.status === 401) {
      // Clear session and redirect to login
      await supabase.auth.signOut();
      window.location.href = '/login';
      throw new Error(ERROR_MESSAGES[401]);
    }

    // Return sanitized error message
    const message = ERROR_MESSAGES[response.status] || 'Error inesperado. Intenta nuevamente.';
    throw new Error(message);
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

    return this.handleResponse(response);
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

    return this.handleResponse(response);
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

    return this.handleResponse(response);
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

    // Check for errors before processing blob
    if (!response.ok) {
      await this.handleResponse(response); // This will throw
      return;
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
   * Get download URL for a specific language package
   * @returns URL string for download
   */
  getDownloadUrl(jobId: string, language: string): string {
    return `${this.baseURL}/api/v1/download/${jobId}/${language}`;
  }

  /**
   * Get download URL for all packages (bundle)
   * @returns URL string for download
   */
  getDownloadAllUrl(jobId: string): string {
    return `${this.baseURL}/api/v1/download/${jobId}/all`;
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

    // Check for errors before processing blob
    if (!response.ok) {
      await this.handleResponse(response); // This will throw
      return;
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

  /**
   * Obtener historial de traducciones del usuario
   * @requires Authentication
   */
  async getHistory(
    limit: number = 20,
    offset: number = 0,
    statusFilter?: string
  ): Promise<{
    jobs: Array<{
      id: string;
      original_filename: string;
      source_language: string;
      target_languages: string[];
      status: string;
      progress_percentage: number;
      created_at: string;
      completed_at?: string;
      download_urls: Record<string, string>;
      error_message?: string;
    }>;
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }> {
    const authHeaders = await this.getAuthHeaders();

    let url = `${this.baseURL}/api/v1/jobs?limit=${limit}&offset=${offset}`;
    if (statusFilter) {
      url += `&status_filter=${statusFilter}`;
    }

    const response = await fetch(url, {
      headers: authHeaders,
    });

    return this.handleResponse(response);
  }
}

export const api = new ApiClient(API_BASE_URL);
