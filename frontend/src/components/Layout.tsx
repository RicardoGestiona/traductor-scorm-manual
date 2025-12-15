/**
 * Layout principal de la aplicación con autenticación.
 *
 * Filepath: frontend/src/components/Layout.tsx
 * Feature alignment: STORY-003 - Setup Frontend React, STORY-017 - Autenticación
 */

import type { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { user, signOut, loading } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link to="/">
                <h1 className="text-xl font-bold text-gray-900 hover:text-gray-700">
                  🌍 Traductor SCORM
                </h1>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                API Docs
              </a>
              <a
                href="https://github.com/RicardoGestiona/traductor-scorm-manual"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                GitHub
              </a>

              {!loading && (
                <>
                  {user ? (
                    <div className="flex items-center space-x-4">
                      <Link
                        to="/history"
                        className="text-sm text-gray-600 hover:text-gray-900"
                      >
                        Historial
                      </Link>
                      <span className="text-sm text-gray-700">
                        {user.email}
                      </span>
                      <button
                        onClick={handleSignOut}
                        className="text-sm px-4 py-2 rounded-md bg-gray-200 hover:bg-gray-300 text-gray-800"
                      >
                        Cerrar Sesión
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <Link
                        to="/login"
                        className="text-sm px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700"
                      >
                        Iniciar Sesión
                      </Link>
                      <Link
                        to="/signup"
                        className="text-sm px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Registrarse
                      </Link>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Traductor SCORM v0.1.0 - MVP en desarrollo
          </p>
        </div>
      </footer>
    </div>
  );
}
