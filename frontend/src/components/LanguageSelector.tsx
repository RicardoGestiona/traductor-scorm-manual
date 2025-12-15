/**
 * Componente de selección de idiomas para traducción.
 *
 * Filepath: frontend/src/components/LanguageSelector.tsx
 * Feature alignment: STORY-012 - Language Selector
 *
 * Idiomas origen: Español (predeterminado), Català, Português, Italiano
 * Idiomas destino: Español, Català, Galego, Euskera, Português, Italiano
 */

import { useState, useRef, useEffect } from 'react';
import {
  SOURCE_LANGUAGES,
  TARGET_LANGUAGES,
  SUPPORTED_LANGUAGES
} from '../types/translation';
import { FlagIcon } from './FlagIcon';

interface LanguageSelectorProps {
  sourceLanguage: string;
  targetLanguages: string[];
  onSourceChange: (lang: string) => void;
  onTargetChange: (langs: string[]) => void;
  disabled?: boolean;
}

export function LanguageSelector({
  sourceLanguage,
  targetLanguages,
  onSourceChange,
  onTargetChange,
  disabled = false,
}: LanguageSelectorProps) {
  const [isSourceOpen, setIsSourceOpen] = useState(false);
  const [isTargetOpen, setIsTargetOpen] = useState(false);
  const sourceRef = useRef<HTMLDivElement>(null);
  const targetRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdowns al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sourceRef.current && !sourceRef.current.contains(event.target as Node)) {
        setIsSourceOpen(false);
      }
      if (targetRef.current && !targetRef.current.contains(event.target as Node)) {
        setIsTargetOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getSourceLanguage = () => {
    return SOURCE_LANGUAGES.find((l) => l.code === sourceLanguage) || SOURCE_LANGUAGES[0];
  };

  const handleSourceSelect = (code: string) => {
    onSourceChange(code);
    setIsSourceOpen(false);
    // Si el nuevo idioma origen estaba seleccionado como destino, quitarlo
    if (targetLanguages.includes(code)) {
      onTargetChange(targetLanguages.filter((l) => l !== code));
    }
  };

  const handleTargetToggle = (code: string) => {
    if (targetLanguages.includes(code)) {
      onTargetChange(targetLanguages.filter((l) => l !== code));
    } else {
      onTargetChange([...targetLanguages, code]);
    }
  };

  // Filtrar idiomas destino (excluir el idioma origen seleccionado)
  const availableTargetLanguages = TARGET_LANGUAGES.filter(
    (lang) => lang.code !== sourceLanguage
  );

  const selectedSourceLang = getSourceLanguage();

  return (
    <div className="space-y-6">
      {/* Source Language - Dropdown personalizado */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Idioma origen
        </label>
        <div className="relative" ref={sourceRef}>
          <button
            type="button"
            onClick={() => !disabled && setIsSourceOpen(!isSourceOpen)}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-left focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between bg-white"
          >
            <span className="text-gray-700 flex items-center gap-3">
              <FlagIcon language={selectedSourceLang} size="md" />
              {selectedSourceLang.name}
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${
                isSourceOpen ? 'transform rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Dropdown menu */}
          {isSourceOpen && !disabled && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {SOURCE_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => handleSourceSelect(lang.code)}
                  className={`w-full flex items-center px-4 py-3 hover:bg-gray-50 text-left ${
                    sourceLanguage === lang.code ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                  }`}
                >
                  <FlagIcon language={lang} size="md" className="mr-3" />
                  <span>{lang.name}</span>
                  {sourceLanguage === lang.code && (
                    <svg className="w-5 h-5 ml-auto text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          El idioma del paquete SCORM original
        </p>
      </div>

      {/* Target Languages - Dropdown personalizado */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Idiomas destino {targetLanguages.length > 0 && `(${targetLanguages.length} seleccionados)`}
        </label>
        <div className="relative" ref={targetRef}>
          <button
            type="button"
            onClick={() => !disabled && setIsTargetOpen(!isTargetOpen)}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-left focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between bg-white"
          >
            <span className="text-gray-700">
              {targetLanguages.length === 0
                ? 'Selecciona uno o más idiomas'
                : targetLanguages.map((code) => {
                    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
                    return lang?.name || code;
                  }).join(', ')}
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${
                isTargetOpen ? 'transform rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Dropdown menu */}
          {isTargetOpen && !disabled && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {availableTargetLanguages.map((lang) => (
                <label
                  key={lang.code}
                  className="flex items-center px-4 py-3 hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={targetLanguages.includes(lang.code)}
                    onChange={() => handleTargetToggle(lang.code)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <FlagIcon language={lang} size="md" className="ml-3 mr-2" />
                  <span className="text-gray-700">{lang.name}</span>
                </label>
              ))}

              {/* Select All / Clear All */}
              <div className="border-t border-gray-200 p-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => onTargetChange(availableTargetLanguages.map((l) => l.code))}
                  className="flex-1 px-3 py-2 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded"
                >
                  Seleccionar todos
                </button>
                <button
                  type="button"
                  onClick={() => onTargetChange([])}
                  className="flex-1 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 rounded"
                >
                  Limpiar
                </button>
              </div>
            </div>
          )}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Puedes seleccionar múltiples idiomas
        </p>

        {/* Selected languages chips */}
        {targetLanguages.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {targetLanguages.map((code) => {
              const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
              if (!lang) return null;

              return (
                <span
                  key={code}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                >
                  <FlagIcon language={lang} size="sm" className="mr-1" />
                  {lang.name}
                  {!disabled && (
                    <button
                      type="button"
                      onClick={() => handleTargetToggle(code)}
                      className="ml-2 inline-flex items-center justify-center w-4 h-4 text-blue-600 hover:bg-blue-200 hover:text-blue-900 rounded-full"
                    >
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  )}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
