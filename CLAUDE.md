# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Traductor SCORM CLI** — Herramienta de línea de comandos (Python 3.14) para traducir paquetes SCORM (1.2, 2004, Articulate Rise) a múltiples idiomas usando Google Translate, preservando la estructura e integridad del contenido e-learning.

**Ámbito activo:** Solo `traductor-scorm-cli/`. El resto de directorios (pendientes/, ficheros raíz) son auxiliares.

## Build & Development Commands

```bash
# Setup
cd traductor-scorm-cli
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Ejecutar traducción
python traductor.py <archivo.zip> --idioma <código>
python traductor.py mi-curso.zip --idioma ca,en,fr
python traductor.py mi-curso.zip --idioma ca --salida ./traducciones/

# Verificación de sintaxis
python -m py_compile traductor.py
```

## Tech Stack

- **Python 3.14** — Runtime
- **lxml** — Parsing XML/SCORM manifests (etree, XPath)
- **BeautifulSoup4** — Parsing HTML para extracción de segmentos
- **deep-translator** — Google Translate API wrapper (async)
- **asyncio** — Procesamiento concurrente de segmentos

## Architecture

Archivo único `traductor.py` con arquitectura de clases pipeline:

```
ZIP Input → ScormParser → ContentExtractor → Translator → ScormRebuilder → ZIP Output
```

| Clase | Responsabilidad |
|:---|:---|
| `ScormParser` | Extrae ZIP, detecta versión SCORM (1.2/2004), localiza manifest y HTML |
| `ContentExtractor` | Extrae segmentos traducibles de manifest XML, HTML y Articulate Rise (base64 JSON) |
| `Translator` | Traduce segmentos async via Google Translate con rate limiting |
| `ScormRebuilder` | Aplica traducciones a los ficheros originales y reempaqueta ZIP |

**Modelos de datos** (dataclasses): `Segment`, `ScormPackage`, `ExtractionResult`

**Logging:** JSON estructurado via `JsonFormatter` (clase custom de `logging.Formatter`)

## Formatos Soportados

- **SCORM 1.2** — Manifest `imsmanifest.xml` con namespace `adlcp`
- **SCORM 2004** — Manifest con namespace `adlcp` v2004
- **Articulate Rise** — HTML con JSON embebido en base64 (patrón `window.defined_data`)
- **HTML estándar** — Extracción directa con BeautifulSoup

## Idiomas

`es`, `en`, `ca`, `fr`, `de`, `it`, `pt`, `eu`, `gl`

## Convenciones de Código

- Funciones ≤ 20 líneas (SOLID/SRP). Si excede, refactorizar en métodos privados.
- Excepciones específicas (prohibido bare `except:` o `except Exception` genérico).
- Logging JSON estructurado (prohibido `print()`).
- Reemplazo contextual de strings (primera ocurrencia, no `.replace()` global en HTML).
- Type hints completos en todas las firmas.
- Nomenclatura de código en inglés; interfaz/comentarios en español.
