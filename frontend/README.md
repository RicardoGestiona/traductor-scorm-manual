# Frontend - Traductor SCORM

Interfaz web construida con React + Vite + TypeScript para el sistema de traducción de paquetes SCORM.

## 🚀 Quick Start

### Desarrollo Local

\`\`\`bash
# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env

# Ejecutar servidor de desarrollo
npm run dev
\`\`\`

Frontend disponible en: \`http://localhost:5173\`

---

## 📁 Estructura del Proyecto

\`\`\`
frontend/
├── src/
│   ├── components/       # Componentes React reutilizables
│   │   └── Layout.tsx   # Layout principal con navbar y footer
│   ├── pages/           # Páginas de la aplicación
│   │   └── Home.tsx     # Página principal
│   ├── services/        # Servicios y clientes API
│   │   └── api.ts       # Cliente para backend FastAPI
│   ├── types/           # TypeScript types y interfaces
│   ├── App.tsx          # Componente raíz
│   ├── main.tsx         # Entry point
│   └── index.css        # Estilos globales (Tailwind)
├── public/              # Assets estáticos
├── index.html           # HTML template
├── vite.config.ts       # Configuración de Vite
├── tailwind.config.js   # Configuración de Tailwind CSS
├── tsconfig.json        # Configuración de TypeScript
└── package.json
\`\`\`

---

## 🎨 Stack Tecnológico

- **React 18** - Librería UI
- **TypeScript** - Type safety
- **Vite** - Build tool y dev server (HMR rápido)
- **Tailwind CSS** - Utility-first CSS
- **ESLint** - Linting

---

## 📝 Scripts Disponibles

\`\`\`bash
# Desarrollo
npm run dev          # Servidor de desarrollo en http://localhost:5173

# Build
npm run build        # Build de producción en dist/
npm run preview      # Preview del build de producción

# Linting
npm run lint         # Lint con ESLint
\`\`\`

---

## 🔗 Conexión con Backend

El frontend se conecta al backend FastAPI en \`http://127.0.0.1:8000\` por defecto.

Para cambiar la URL del backend, edita \`.env\`:

\`\`\`bash
VITE_API_URL=http://127.0.0.1:8000
\`\`\`

---

**Mantenido por**: Ricardo
**Última actualización**: 2025-11-25
