/**
 * Componente para mostrar banderas (emoji o imagen).
 *
 * Filepath: frontend/src/components/FlagIcon.tsx
 */

import type { Language } from '../types/translation';

interface FlagIconProps {
  language: Language;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4 text-base',
  md: 'w-5 h-5 text-xl',
  lg: 'w-6 h-6 text-2xl',
};

export function FlagIcon({ language, size = 'md', className = '' }: FlagIconProps) {
  const sizeClass = sizeClasses[size];

  if (language.flagType === 'image') {
    return (
      <img
        src={language.flag}
        alt={`Bandera de ${language.name}`}
        className={`${sizeClass} object-contain inline-block ${className}`}
        style={{ verticalAlign: 'middle' }}
      />
    );
  }

  // Emoji flag
  return (
    <span className={`${sizeClass} inline-flex items-center justify-center ${className}`}>
      {language.flag}
    </span>
  );
}
