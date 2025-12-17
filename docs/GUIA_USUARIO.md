# Guía Rápida de Usuario - Traductor SCORM

## Introducción

El **Traductor SCORM** es una aplicación web que permite traducir paquetes de contenido e-learning (SCORM 1.2, 2004 y xAPI) a múltiples idiomas de forma automática usando inteligencia artificial.

**Tiempo estimado**: De horas de trabajo manual a **5 minutos automáticos**.

---

## Requisitos Previos

- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Paquete SCORM en formato `.zip` (máximo 500MB)
- Cuenta de usuario registrada

---

## Inicio Rápido

### 1. Acceder a la Aplicación

Abre tu navegador y ve a la URL de la aplicación:
- **Desarrollo**: http://localhost:5173
- **Producción**: (URL de producción cuando esté desplegada)

### 2. Crear una Cuenta

Si es tu primera vez:

1. Haz clic en **"Crear Cuenta"** o **"Registrarse"**
2. Introduce tu email
3. Crea una contraseña segura que cumpla:
   - Mínimo 8 caracteres
   - Al menos una letra mayúscula
   - Al menos una letra minúscula
   - Al menos un número
   - Al menos un carácter especial (!@#$%^&*...)
4. Confirma la contraseña
5. Haz clic en **"Crear Cuenta"**

### 3. Iniciar Sesión

1. Introduce tu email y contraseña
2. Haz clic en **"Iniciar Sesión"**

---

## Traducir un Paquete SCORM

### Paso 1: Subir el Archivo

1. En la página principal, verás la zona de upload
2. Puedes:
   - **Arrastrar y soltar** tu archivo `.zip` en la zona indicada
   - **Hacer clic** en la zona para abrir el selector de archivos

> **Nota**: Solo se aceptan archivos `.zip` de hasta 500MB

### Paso 2: Seleccionar Idiomas

1. Selecciona el **idioma de origen** de tu contenido
2. Selecciona los **idiomas de destino** (puedes elegir varios)

**Idiomas disponibles**:
| Código | Idioma |
|--------|--------|
| es | Español |
| en | Inglés |
| fr | Francés |
| de | Alemán |
| it | Italiano |
| pt | Portugués |
| nl | Neerlandés |
| pl | Polaco |
| zh | Chino |
| ja | Japonés |
| ko | Coreano |
| ar | Árabe |

### Paso 3: Iniciar Traducción

1. Haz clic en el botón **"Traducir"**
2. La traducción comenzará automáticamente

### Paso 4: Seguir el Progreso

Verás una barra de progreso que muestra:
- **Porcentaje completado** (0-100%)
- **Estado actual** del proceso:
  - `uploaded` - Archivo recibido
  - `validating` - Validando estructura SCORM
  - `parsing` - Extrayendo contenido traducible
  - `translating` - Traduciendo con IA
  - `rebuilding` - Reconstruyendo paquete
  - `completed` - ¡Listo para descargar!

> **Tiempo estimado**: 2-10 minutos dependiendo del tamaño del paquete

### Paso 5: Descargar Traducciones

Una vez completada la traducción:

1. **Descarga individual**: Haz clic en el botón de cada idioma para descargar ese paquete específico
2. **Descarga todo**: Haz clic en **"Descargar Todo"** para obtener un ZIP con todos los idiomas

---

## Gestión de Cuenta

### Ver Historial

- Accede a la sección **"Historial"** para ver todas tus traducciones anteriores
- Puedes volver a descargar traducciones completadas

### Cerrar Sesión

1. Haz clic en tu perfil o en **"Cerrar Sesión"**
2. Tu sesión se cerrará de forma segura

---

## Solución de Problemas

### El archivo no se sube

- **Verifica la extensión**: Debe ser `.zip`
- **Verifica el tamaño**: Máximo 500MB
- **Verifica la conexión**: Asegúrate de tener conexión a internet

### Error "SCORM inválido"

- El archivo ZIP debe contener un archivo `imsmanifest.xml` válido
- Asegúrate de que el paquete SCORM funcione correctamente en un LMS antes de traducirlo

### La traducción falla

- **Intenta de nuevo**: Algunos errores son temporales
- **Verifica el contenido**: El SCORM debe tener contenido de texto traducible
- **Contacta soporte**: Si el problema persiste

### "Sesión expirada"

- Tu sesión ha caducado por inactividad
- Inicia sesión nuevamente

---

## Consejos y Mejores Prácticas

### Antes de traducir

1. **Prueba el SCORM original** en tu LMS para verificar que funciona
2. **Revisa el contenido** para asegurarte de que el texto es correcto
3. **Considera el contexto**: La IA traduce mejor con contenido claro y bien estructurado

### Después de traducir

1. **Revisa las traducciones** antes de publicar en producción
2. **Prueba en tu LMS** para verificar que el SCORM traducido funciona correctamente
3. **Guarda los originales** por si necesitas hacer cambios

### Para mejores resultados

- Usa texto claro y sin ambigüedades
- Evita jerga muy específica o abreviaturas poco comunes
- El contenido con buena estructura HTML se traduce mejor

---

## Formatos Soportados

| Formato | Soporte | Notas |
|---------|---------|-------|
| SCORM 1.2 | ✅ Completo | Formato más común |
| SCORM 2004 | ✅ Completo | Incluye sequencing |
| xAPI/TinCan | 🔄 Parcial | Soporte básico |

---

## Seguridad

Tu contenido está protegido:

- ✅ Conexión cifrada (HTTPS)
- ✅ Autenticación segura con tokens JWT
- ✅ Tus archivos son privados y solo tú puedes acceder a ellos
- ✅ Los archivos se eliminan automáticamente después de 7 días

---

## Soporte

Si necesitas ayuda:

1. Revisa esta guía
2. Consulta la documentación técnica
3. Contacta al administrador del sistema

---

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl/Cmd + V` | Pegar archivo desde portapapeles |
| `Escape` | Cancelar operación actual |
| `Enter` | Confirmar acción |

---

**Versión de la aplicación**: 1.1.0
**Última actualización**: 2025-12-17
