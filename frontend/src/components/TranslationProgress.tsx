/**
 * Componente de progreso de traducción con polling en tiempo real.
 *
 * Filepath: frontend/src/components/TranslationProgress.tsx
 * Feature alignment: STORY-013 - Progress Tracker
 */

import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { STATUS_COLORS, STATUS_LABELS } from '../types/translation';
import type { TranslationStatus } from '../types/translation';

interface TranslationProgressProps {
  jobId: string;
  onComplete: (downloadUrls: Record<string, string>) => void;
  onError: (error: string) => void;
}

// SECURITY FIX: Max retries to prevent infinite polling (MED-004)
const MAX_POLL_RETRIES = 180; // 6 minutes at 2s intervals
const POLL_INTERVAL_MS = 2000;

export function TranslationProgress({
  jobId,
  onComplete,
  onError,
}: TranslationProgressProps) {
  const [status, setStatus] = useState<TranslationStatus>('uploaded');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('Iniciando traduccion...');
  const [isPolling, setIsPolling] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (!isPolling) return;

    // SECURITY FIX: Check max retries to prevent infinite loop (MED-004)
    if (retryCount >= MAX_POLL_RETRIES) {
      setIsPolling(false);
      onError('Tiempo de espera agotado. La traduccion esta tardando demasiado.');
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        setRetryCount(prev => prev + 1);
        const jobStatus = await api.getJobStatus(jobId);

        setStatus(jobStatus.status as TranslationStatus);
        setProgress(jobStatus.progress_percentage);
        setCurrentStep(jobStatus.current_step);

        // Si completo o fallo, dejar de hacer polling
        if (jobStatus.status === 'completed') {
          setIsPolling(false);
          clearInterval(pollInterval);
          onComplete(jobStatus.download_urls);
        } else if (jobStatus.status === 'failed') {
          setIsPolling(false);
          clearInterval(pollInterval);
          onError(jobStatus.error_message || 'Error desconocido en la traduccion');
        }
      } catch (error) {
        // SECURITY FIX: Environment-aware logging (MED-002)
        if (import.meta.env.DEV) {
          console.error('Error polling job status:', error);
        }
        setIsPolling(false);
        clearInterval(pollInterval);
        onError(error instanceof Error ? error.message : 'Error al obtener estado');
      }
    }, POLL_INTERVAL_MS);

    // Cleanup al desmontar
    return () => clearInterval(pollInterval);
  }, [jobId, isPolling, retryCount, onComplete, onError]);

  const statusColor = STATUS_COLORS[status];
  const statusLabel = STATUS_LABELS[status];

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Traducción en progreso
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium text-white ${statusColor}`}
        >
          {statusLabel}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            {currentStep}
          </span>
          <span className="text-sm font-bold text-gray-900">{progress}%</span>
        </div>

        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${statusColor} transition-all duration-500 ease-out`}
            style={{ width: `${progress}%` }}
          >
            {/* Animated shine effect */}
            <div className="w-full h-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shine" />
          </div>
        </div>
      </div>

      {/* Status details */}
      <div className="space-y-2">
        {status === 'validating' && (
          <StatusItem
            icon="🔍"
            title="Validando SCORM"
            description="Verificando estructura del paquete..."
          />
        )}
        {status === 'parsing' && (
          <StatusItem
            icon="📄"
            title="Analizando contenido"
            description="Extrayendo textos traducibles..."
          />
        )}
        {status === 'translating' && (
          <StatusItem
            icon="🌐"
            title="Traduciendo"
            description="Usando IA para traducir el contenido..."
          />
        )}
        {status === 'rebuilding' && (
          <StatusItem
            icon="🔨"
            title="Reconstruyendo"
            description="Generando paquetes SCORM traducidos..."
          />
        )}
        {status === 'completed' && (
          <StatusItem
            icon="✅"
            title="Completado"
            description="Tu traducción está lista para descargar"
            success
          />
        )}
        {status === 'failed' && (
          <StatusItem
            icon="❌"
            title="Error"
            description="Ocurrió un problema durante la traducción"
            error
          />
        )}
      </div>

      {/* Loading indicator */}
      {isPolling && status !== 'failed' && (
        <div className="mt-4 flex items-center justify-center text-sm text-gray-500">
          <svg
            className="animate-spin h-4 w-4 mr-2 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Actualizando cada 2 segundos...
        </div>
      )}

      {/* Job ID (for debugging) */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-400">
          ID del trabajo: <code className="font-mono">{jobId}</code>
        </p>
      </div>
    </div>
  );
}

interface StatusItemProps {
  icon: string;
  title: string;
  description: string;
  success?: boolean;
  error?: boolean;
}

function StatusItem({
  icon,
  title,
  description,
  success = false,
  error = false,
}: StatusItemProps) {
  return (
    <div
      className={`flex items-start p-3 rounded-md ${
        success
          ? 'bg-green-50 border border-green-200'
          : error
          ? 'bg-red-50 border border-red-200'
          : 'bg-blue-50 border border-blue-200'
      }`}
    >
      <span className="text-2xl mr-3">{icon}</span>
      <div>
        <p className={`text-sm font-medium ${
          success ? 'text-green-800' : error ? 'text-red-800' : 'text-blue-800'
        }`}>
          {title}
        </p>
        <p className={`text-xs ${
          success ? 'text-green-600' : error ? 'text-red-600' : 'text-blue-600'
        }`}>
          {description}
        </p>
      </div>
    </div>
  );
}

// SECURITY FIX: Removed dynamic style injection (CRIT-001)
// Animation styles are now defined in index.css or tailwind.config.js
// The animate-shine class should be added to your CSS file:
// @keyframes shine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
// .animate-shine { animation: shine 2s infinite; }
