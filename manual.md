# Manual de Usuario - Traductor SCORM CLI

## Requisitos del Sistema

- **Python 3.14** o superior
- Sistema operativo: macOS, Linux o Windows

## Instalación

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Modo Batch (Recomendado)

Procesa automáticamente todos los archivos ZIP en la carpeta `pendientes/`.

```bash
python traductor.py --idioma ca
```

**Flujo:**
1. Coloca los archivos SCORM (.zip) en `pendientes/`
2. Ejecuta el comando con el idioma deseado
3. Las traducciones se generan en `traducidos/`
4. Los originales se mueven a `procesados/`

### Modo Archivo Único

Traduce un archivo específico.

```bash
python traductor.py mi-curso.zip --idioma ca
```

**Opciones adicionales:**

| Opción | Descripción | Valor por defecto |
|:---|:---|:---|
| `--idioma`, `-i` | Idioma(s) destino (obligatorio) | - |
| `--origen`, `-o` | Idioma origen | `es` |
| `--salida`, `-s` | Carpeta de salida | `.` (actual) |

## Idiomas Soportados

| Código | Idioma |
|:---:|:---|
| `es` | Español |
| `en` | Inglés |
| `ca` | Catalán |
| `fr` | Francés |
| `de` | Alemán |
| `it` | Italiano |
| `pt` | Portugués |
| `eu` | Euskera |
| `gl` | Gallego |

## Ejemplos

```bash
# Traducir a catalán (modo batch)
python traductor.py --idioma ca

# Traducir archivo a inglés
python traductor.py curso.zip --idioma en

# Traducir a múltiples idiomas
python traductor.py curso.zip --idioma ca,en,fr

# Especificar carpeta de salida
python traductor.py curso.zip --idioma ca --salida ./traducciones/

# Traducir desde francés a español
python traductor.py curso-fr.zip --idioma es --origen fr
```

## Estructura de Carpetas

```
traductor-scorm-manual/
├── traductor.py          # Script principal
├── requirements.txt      # Dependencias
├── manual.md             # Este manual
├── README.md             # Documentación del proyecto
├── pendientes/           # Entrada: ZIPs a traducir
├── procesados/           # Originales ya procesados
└── traducidos/           # Salida: ZIPs traducidos
```

## Formatos SCORM Soportados

- **SCORM 1.2** — Paquetes estándar con `imsmanifest.xml`
- **SCORM 2004** — Versiones 2nd, 3rd y 4th Edition
- **Articulate Rise** — Cursos exportados con JSON embebido en base64

## Solución de Problemas

### El LMS no reconoce el archivo traducido

Verificar que el ZIP mantiene la estructura original. El traductor preserva todos los atributos del ZIP original.

### Caracteres mal codificados en nombres de archivo

El traductor corrige automáticamente problemas de Unicode (NFD/NFC) comunes en archivos creados en macOS.

### Error "No se encontró imsmanifest.xml"

El archivo ZIP no es un paquete SCORM válido. Verificar que contiene `imsmanifest.xml` en la raíz o en una subcarpeta.
