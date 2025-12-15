/**
 * Componente de ruta protegida que requiere autenticación.
 *
 * Filepath: frontend/src/components/ProtectedRoute.tsx
 * Feature alignment: STORY-017 - Autenticación
 */

import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  // Mostrar loading mientras se verifica la sesión
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  // Si no hay usuario autenticado, redirigir a login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Usuario autenticado, mostrar contenido
  return <>{children}</>;
}
