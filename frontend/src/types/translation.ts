/**
 * TypeScript types para el sistema de traducción SCORM.
 *
 * Filepath: frontend/src/types/translation.ts
 * Feature alignment: Sprint 3 - Frontend Types
 */

export type TranslationStatus =
  | 'uploaded'
  | 'validating'
  | 'parsing'
  | 'translating'
  | 'rebuilding'
  | 'completed'
  | 'failed';

export interface Language {
  code: string;
  name: string;
  flag: string; // emoji flag
}

export interface TranslationJob {
  job_id: string;
  original_filename: string;
  source_language: string;
  target_languages: string[];
  status: TranslationStatus;
  progress_percentage: number;
  current_step?: string;
  download_urls: Record<string, string>;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
  original_filename: string;
  created_at: string;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
];

export const STATUS_COLORS: Record<TranslationStatus, string> = {
  uploaded: 'bg-gray-500',
  validating: 'bg-blue-500',
  parsing: 'bg-indigo-500',
  translating: 'bg-purple-500',
  rebuilding: 'bg-pink-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};

export const STATUS_LABELS: Record<TranslationStatus, string> = {
  uploaded: 'Subido',
  validating: 'Validando',
  parsing: 'Analizando',
  translating: 'Traduciendo',
  rebuilding: 'Reconstruyendo',
  completed: 'Completado',
  failed: 'Error',
};
