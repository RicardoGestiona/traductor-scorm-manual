/**
 * Página principal de la aplicación - Flujo completo de traducción SCORM.
 *
 * Filepath: frontend/src/pages/Home.tsx
 * Feature alignment: Sprint 3 - Frontend Integration
 */

import { useState } from 'react';
import { UploadZone } from '../components/UploadZone';
import { LanguageSelector } from '../components/LanguageSelector';
import { TranslationProgress } from '../components/TranslationProgress';
import { DownloadButtons } from '../components/DownloadButtons';
import { api } from '../services/api';

type WorkflowStep = 'upload' | 'translating' | 'completed' | 'error';

export function Home() {
  // Workflow state
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');

  // Upload & language selection
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceLanguage, setSourceLanguage] = useState('es'); // Español por defecto
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Translation state
  const [jobId, setJobId] = useState<string | null>(null);
  const [originalFilename, setOriginalFilename] = useState('');

  // Completion state
  const [downloadUrls, setDownloadUrls] = useState<Record<string, string>>({});

  // Error state
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };

  const handleStartTranslation = async () => {
    if (!selectedFile || targetLanguages.length === 0) {
      setError('Por favor selecciona un archivo y al menos un idioma destino');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const response = await api.uploadScorm(
        selectedFile,
        sourceLanguage,
        targetLanguages
      );

      setJobId(response.job_id);
      setOriginalFilename(response.original_filename);
      setCurrentStep('translating');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir archivo');
      setCurrentStep('error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleTranslationComplete = (urls: Record<string, string>) => {
    setDownloadUrls(urls);
    setCurrentStep('completed');
  };

  const handleTranslationError = (errorMessage: string) => {
    setError(errorMessage);
    setCurrentStep('error');
  };

  const handleStartNew = () => {
    setCurrentStep('upload');
    setSelectedFile(null);
    setSourceLanguage('es'); // Reset a español por defecto
    setTargetLanguages([]);
    setJobId(null);
    setOriginalFilename('');
    setDownloadUrls({});
    setError(null);
  };

  const canSubmit =
    selectedFile !== null && targetLanguages.length > 0 && !isUploading;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Traductor SCORM
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Traduce tus paquetes SCORM a múltiples idiomas usando IA de forma
            rápida y precisa
          </p>
        </div>

        {/* Workflow Steps Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            <StepIndicator
              number={1}
              label="Upload"
              active={currentStep === 'upload'}
              completed={
                currentStep === 'translating' ||
                currentStep === 'completed' ||
                currentStep === 'error'
              }
            />
            <div className="flex-1 h-1 bg-gray-300 max-w-xs"></div>
            <StepIndicator
              number={2}
              label="Traducción"
              active={currentStep === 'translating'}
              completed={currentStep === 'completed'}
            />
            <div className="flex-1 h-1 bg-gray-300 max-w-xs"></div>
            <StepIndicator
              number={3}
              label="Descarga"
              active={currentStep === 'completed'}
              completed={false}
            />
          </div>
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Step 1: Upload & Language Selection */}
          {currentStep === 'upload' && (
            <div className="space-y-6 animate-fade-in">
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h2 className="text-2xl font-semibold mb-6 text-gray-900">
                  1. Sube tu paquete SCORM
                </h2>
                <UploadZone
                  onFileSelect={handleFileSelect}
                  disabled={isUploading}
                />

                {selectedFile && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800 flex items-center">
                      <svg
                        className="w-5 h-5 mr-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="font-medium">Archivo seleccionado:</span>
                      <span className="ml-2">{selectedFile.name}</span>
                      <span className="ml-2 text-gray-600">
                        ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                      </span>
                    </p>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl shadow-lg p-8">
                <h2 className="text-2xl font-semibold mb-6 text-gray-900">
                  2. Selecciona los idiomas
                </h2>
                <LanguageSelector
                  sourceLanguage={sourceLanguage}
                  targetLanguages={targetLanguages}
                  onSourceChange={setSourceLanguage}
                  onTargetChange={setTargetLanguages}
                  disabled={isUploading}
                />
              </div>

              <button
                onClick={handleStartTranslation}
                disabled={!canSubmit}
                className={`w-full py-4 px-6 rounded-xl text-white font-semibold text-lg transition-all ${
                  canSubmit
                    ? 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg transform hover:-translate-y-0.5'
                    : 'bg-gray-300 cursor-not-allowed'
                }`}
              >
                {isUploading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin h-5 w-5 mr-3"
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
                    Subiendo archivo...
                  </span>
                ) : (
                  'Iniciar Traducción 🚀'
                )}
              </button>
            </div>
          )}

          {/* Step 2: Translation Progress */}
          {currentStep === 'translating' && jobId && (
            <div className="animate-fade-in">
              <TranslationProgress
                jobId={jobId}
                onComplete={handleTranslationComplete}
                onError={handleTranslationError}
              />
            </div>
          )}

          {/* Step 3: Download Results */}
          {currentStep === 'completed' && (
            <div className="space-y-6 animate-fade-in">
              <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                <div className="text-6xl mb-4">🎉</div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  ¡Traducción completada!
                </h2>
                <p className="text-gray-600 mb-6">
                  Tus paquetes SCORM están listos para descargar
                </p>
              </div>

              {jobId && (
                <DownloadButtons
                  jobId={jobId}
                  downloadUrls={downloadUrls}
                  originalFilename={originalFilename}
                />
              )}

              <button
                onClick={handleStartNew}
                className="w-full py-4 px-6 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold transition-all"
              >
                Traducir otro archivo
              </button>
            </div>
          )}

          {/* Error State */}
          {currentStep === 'error' && (
            <div className="space-y-6 animate-fade-in">
              <div className="bg-white rounded-xl shadow-lg p-8">
                <div className="text-center">
                  <div className="text-6xl mb-4">❌</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Ocurrió un error
                  </h2>
                  <p className="text-gray-600 mb-6">{error}</p>
                  <button
                    onClick={handleStartNew}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Intentar de nuevo
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface StepIndicatorProps {
  number: number;
  label: string;
  active: boolean;
  completed: boolean;
}

function StepIndicator({
  number,
  label,
  active,
  completed,
}: StepIndicatorProps) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg transition-all ${
          completed
            ? 'bg-green-500 text-white'
            : active
            ? 'bg-blue-600 text-white ring-4 ring-blue-200'
            : 'bg-gray-300 text-gray-600'
        }`}
      >
        {completed ? '✓' : number}
      </div>
      <span
        className={`text-sm mt-2 font-medium ${
          active ? 'text-blue-600' : 'text-gray-500'
        }`}
      >
        {label}
      </span>
    </div>
  );
}
