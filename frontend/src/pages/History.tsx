/**
 * Página de historial de traducciones.
 *
 * Filepath: frontend/src/pages/History.tsx
 * Feature alignment: STORY-015 - Página de Historial
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { SUPPORTED_LANGUAGES } from '../types/translation';

interface Job {
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
}

type StatusFilter = 'all' | 'completed' | 'failed' | 'translating';

const STATUS_COLORS: Record<string, string> = {
  uploaded: 'bg-gray-100 text-gray-800',
  validating: 'bg-blue-100 text-blue-800',
  parsing: 'bg-blue-100 text-blue-800',
  translating: 'bg-yellow-100 text-yellow-800',
  rebuilding: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const STATUS_LABELS: Record<string, string> = {
  uploaded: 'Subido',
  validating: 'Validando',
  parsing: 'Procesando',
  translating: 'Traduciendo',
  rebuilding: 'Reconstruyendo',
  completed: 'Completado',
  failed: 'Error',
};

export function History() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(0);
  const limit = 10;

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const filterValue = statusFilter === 'all' ? undefined : statusFilter;
      const response = await api.getHistory(limit, page * limit, filterValue);
      setJobs(response.jobs);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar historial');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [statusFilter, page]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getLanguageName = (code: string) => {
    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
    return lang ? lang.name : code.toUpperCase();
  };

  const handleDownload = async (jobId: string, language: string) => {
    try {
      await api.downloadTranslatedPackage(jobId, language);
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Historial</h1>
            <p className="text-gray-600 mt-2">
              Tus traducciones anteriores ({total} total)
            </p>
          </div>
          <Link
            to="/"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Nueva traduccion
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filtrar por estado:</span>
            <div className="flex gap-2">
              {(['all', 'completed', 'translating', 'failed'] as StatusFilter[]).map((filter) => (
                <button
                  key={filter}
                  onClick={() => {
                    setStatusFilter(filter);
                    setPage(0);
                  }}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    statusFilter === filter
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {filter === 'all' ? 'Todos' : STATUS_LABELS[filter] || filter}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Cargando historial...</p>
          </div>
        ) : error ? (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="text-red-500 text-5xl mb-4">!</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={fetchHistory}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Reintentar
            </button>
          </div>
        ) : jobs.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              No hay traducciones
            </h2>
            <p className="text-gray-600 mb-6">
              {statusFilter === 'all'
                ? 'Aun no has realizado ninguna traduccion.'
                : `No hay traducciones con estado "${STATUS_LABELS[statusFilter] || statusFilter}".`}
            </p>
            <Link
              to="/"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Crear primera traduccion
            </Link>
          </div>
        ) : (
          <>
            {/* Jobs Table */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                      Archivo
                    </th>
                    <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                      Idiomas
                    </th>
                    <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                      Estado
                    </th>
                    <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">
                      Fecha
                    </th>
                    <th className="text-right px-6 py-4 text-sm font-semibold text-gray-900">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                            <svg
                              className="w-5 h-5 text-blue-600"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                              />
                            </svg>
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 truncate max-w-xs">
                              {job.original_filename}
                            </p>
                            <p className="text-sm text-gray-500">
                              {getLanguageName(job.source_language)} →{' '}
                              {job.target_languages.map(getLanguageName).join(', ')}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {job.target_languages.map((lang) => (
                            <span
                              key={lang}
                              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                            >
                              {lang.toUpperCase()}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            STATUS_COLORS[job.status] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {STATUS_LABELS[job.status] || job.status}
                        </span>
                        {job.status === 'translating' && (
                          <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-blue-600 h-1.5 rounded-full transition-all"
                              style={{ width: `${job.progress_percentage}%` }}
                            ></div>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {job.status === 'completed' &&
                          Object.keys(job.download_urls).length > 0 && (
                            <div className="flex justify-end gap-2">
                              {Object.entries(job.download_urls).map(([lang]) => (
                                <button
                                  key={lang}
                                  onClick={() => handleDownload(job.id, lang)}
                                  className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 transition-colors"
                                  title={`Descargar ${getLanguageName(lang)}`}
                                >
                                  {lang.toUpperCase()}
                                </button>
                              ))}
                            </div>
                          )}
                        {job.status === 'failed' && (
                          <span className="text-sm text-red-600" title={job.error_message}>
                            Error
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-gray-600">
                  Mostrando {page * limit + 1} - {Math.min((page + 1) * limit, total)} de{' '}
                  {total}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      page === 0
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 shadow'
                    }`}
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= totalPages - 1}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      page >= totalPages - 1
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 shadow'
                    }`}
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default History;
