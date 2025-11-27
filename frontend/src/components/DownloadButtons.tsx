/**
 * Componente de botones de descarga para paquetes SCORM traducidos.
 *
 * Filepath: frontend/src/components/DownloadButtons.tsx
 * Feature alignment: STORY-014 - Download Buttons
 */

import { useState } from 'react';
import { api } from '../services/api';
import { SUPPORTED_LANGUAGES } from '../types/translation';

interface DownloadButtonsProps {
  jobId: string;
  downloadUrls: Record<string, string>;
  originalFilename: string;
}

export function DownloadButtons({
  jobId,
  downloadUrls,
  originalFilename,
}: DownloadButtonsProps) {
  const [downloadingAll, setDownloadingAll] = useState(false);

  const languages = Object.keys(downloadUrls);

  const getLanguageInfo = (code: string) => {
    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
    return lang || { code, name: code.toUpperCase(), flag: '🌐' };
  };

  const handleDownload = (language: string) => {
    const url = api.getDownloadUrl(jobId, language);
    window.open(url, '_blank');
  };

  const handleDownloadAll = () => {
    setDownloadingAll(true);
    const url = api.getDownloadAllUrl(jobId);

    // Trigger download
    window.open(url, '_blank');

    // Reset state after a delay
    setTimeout(() => {
      setDownloadingAll(false);
    }, 2000);
  };

  if (languages.length === 0) {
    return (
      <div className="text-center p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800">
          No hay descargas disponibles todavía
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Descargar paquetes traducidos
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            {languages.length} idioma{languages.length > 1 ? 's' : ''} disponible
            {languages.length > 1 ? 's' : ''}
          </p>
        </div>

        {/* Download All button */}
        {languages.length > 1 && (
          <button
            onClick={handleDownloadAll}
            disabled={downloadingAll}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {downloadingAll ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 mr-2"
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
                Descargando...
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Descargar todos
              </>
            )}
          </button>
        )}
      </div>

      {/* Individual download buttons */}
      <div className="space-y-3">
        {languages.map((langCode) => {
          const langInfo = getLanguageInfo(langCode);
          const filename = `${originalFilename.replace('.zip', '')}_${langCode.toUpperCase()}.zip`;

          return (
            <div
              key={langCode}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-center">
                <span className="text-3xl mr-3">{langInfo.flag}</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {langInfo.name}
                  </p>
                  <p className="text-xs text-gray-500">{filename}</p>
                </div>
              </div>

              <button
                onClick={() => handleDownload(langCode)}
                className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:ring-4 focus:ring-gray-200 transition-colors flex items-center"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Descargar
              </button>
            </div>
          );
        })}
      </div>

      {/* Info footer */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600 flex items-start">
          <svg
            className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <span>
            Los enlaces de descarga son válidos por 7 días. Descarga tus archivos
            pronto o vuelve a realizar la traducción si expiran.
          </span>
        </p>
      </div>
    </div>
  );
}
