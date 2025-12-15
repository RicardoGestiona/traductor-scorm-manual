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
  flag: string; // emoji flag o URL de imagen
  flagType: 'emoji' | 'image'; // tipo de bandera
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

// URLs de banderas regionales (Wikimedia Commons)
const FLAGS = {
  es: '🇪🇸',
  pt: '🇵🇹',
  it: '🇮🇹',
  ca: 'https://upload.wikimedia.org/wikipedia/commons/c/ce/Flag_of_Catalonia.svg',
  gl: 'https://upload.wikimedia.org/wikipedia/commons/6/64/Flag_of_Galicia.svg',
  eu: 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Flag_of_the_Basque_Country.svg',
};

// Idioma origen por defecto
export const DEFAULT_SOURCE_LANGUAGE: Language = {
  code: 'es',
  name: 'Español',
  flag: FLAGS.es,
  flagType: 'emoji',
};

// Idiomas origen disponibles (seleccionables)
export const SOURCE_LANGUAGES: Language[] = [
  { code: 'es', name: 'Español', flag: FLAGS.es, flagType: 'emoji' },
  { code: 'ca', name: 'Català', flag: FLAGS.ca, flagType: 'image' },
  { code: 'pt', name: 'Português (Portugal)', flag: FLAGS.pt, flagType: 'emoji' },
  { code: 'it', name: 'Italiano', flag: FLAGS.it, flagType: 'emoji' },
];

// Idiomas destino disponibles para traducción
export const TARGET_LANGUAGES: Language[] = [
  { code: 'es', name: 'Español', flag: FLAGS.es, flagType: 'emoji' },
  { code: 'ca', name: 'Català', flag: FLAGS.ca, flagType: 'image' },
  { code: 'gl', name: 'Galego', flag: FLAGS.gl, flagType: 'image' },
  { code: 'eu', name: 'Euskera', flag: FLAGS.eu, flagType: 'image' },
  { code: 'pt', name: 'Português (Portugal)', flag: FLAGS.pt, flagType: 'emoji' },
  { code: 'it', name: 'Italiano', flag: FLAGS.it, flagType: 'emoji' },
];

// Lista completa de idiomas (para compatibilidad y futuras expansiones)
export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'es', name: 'Español', flag: FLAGS.es, flagType: 'emoji' },
  { code: 'ca', name: 'Català', flag: FLAGS.ca, flagType: 'image' },
  { code: 'gl', name: 'Galego', flag: FLAGS.gl, flagType: 'image' },
  { code: 'eu', name: 'Euskera', flag: FLAGS.eu, flagType: 'image' },
  { code: 'pt', name: 'Português (Portugal)', flag: FLAGS.pt, flagType: 'emoji' },
  { code: 'it', name: 'Italiano', flag: FLAGS.it, flagType: 'emoji' },
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
