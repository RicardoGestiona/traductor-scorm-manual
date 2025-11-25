/**
 * Página principal de la aplicación.
 *
 * Filepath: frontend/src/pages/Home.tsx
 * Feature alignment: STORY-003 - Setup Frontend React
 */

import { useState, useEffect } from 'react';
import { api } from '../services/api';

export function Home() {
  const [apiStatus, setApiStatus] = useState<{
    connected: boolean;
    info?: { name: string; version: string; status: string };
    error?: string;
  }>({
    connected: false,
  });

  useEffect(() => {
    // Verificar conexión con el backend
    const checkBackend = async () => {
      try {
        const [health, info] = await Promise.all([
          api.healthCheck(),
          api.getApiInfo(),
        ]);

        if (health.status === 'healthy') {
          setApiStatus({ connected: true, info });
        }
      } catch (error) {
        setApiStatus({
          connected: false,
          error: error instanceof Error ? error.message : 'Error desconocido',
        });
      }
    };

    checkBackend();
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Traductor SCORM
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Traduce tus paquetes SCORM a múltiples idiomas usando IA de forma
          rápida y precisa
        </p>
      </div>

      {/* Backend Status Card */}
      <div className="bg-white rounded-lg shadow p-6 max-w-xl mx-auto">
        <h2 className="text-lg font-semibold mb-4">Estado del Backend</h2>
        {apiStatus.connected ? (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-green-700 font-medium">Conectado</span>
            </div>
            {apiStatus.info && (
              <div className="text-sm text-gray-600 space-y-1">
                <p>
                  <span className="font-medium">Nombre:</span>{' '}
                  {apiStatus.info.name}
                </p>
                <p>
                  <span className="font-medium">Versión:</span>{' '}
                  {apiStatus.info.version}
                </p>
                <p>
                  <span className="font-medium">Estado:</span>{' '}
                  {apiStatus.info.status}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-red-700 font-medium">Desconectado</span>
            </div>
            {apiStatus.error && (
              <p className="text-sm text-gray-600">{apiStatus.error}</p>
            )}
            <p className="text-sm text-gray-500">
              Asegúrate de que el backend esté corriendo en{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">
                http://127.0.0.1:8000
              </code>
            </p>
          </div>
        )}
      </div>

      {/* Features (Coming Soon) */}
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-3xl mb-3">📤</div>
          <h3 className="font-semibold mb-2">Upload SCORM</h3>
          <p className="text-sm text-gray-600">
            Sube tu paquete SCORM (.zip) y selecciona idiomas de destino
          </p>
          <span className="inline-block mt-3 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            Próximamente
          </span>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-3xl mb-3">🤖</div>
          <h3 className="font-semibold mb-2">Traducción con IA</h3>
          <p className="text-sm text-gray-600">
            Traducción automática contextual usando Claude AI
          </p>
          <span className="inline-block mt-3 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            Próximamente
          </span>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-3xl mb-3">📥</div>
          <h3 className="font-semibold mb-2">Download Traducido</h3>
          <p className="text-sm text-gray-600">
            Descarga tus paquetes SCORM traducidos listos para usar
          </p>
          <span className="inline-block mt-3 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
            Próximamente
          </span>
        </div>
      </div>
    </div>
  );
}
