# Traductor SCORM CLI

Herramienta de línea de comandos para traducir paquetes SCORM a múltiples idiomas.

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# Modo batch: procesa todos los ZIPs en pendientes/
python traductor.py --idioma ca

# Traducir archivo específico
python traductor.py mi-curso.zip --idioma ca

# Traducir a múltiples idiomas
python traductor.py mi-curso.zip --idioma ca,en,fr

# Especificar carpeta de salida
python traductor.py mi-curso.zip --idioma ca --salida ./traducciones/
```

## Flujo Batch

1. Coloca archivos SCORM (.zip) en `pendientes/`
2. Ejecuta `python traductor.py --idioma ca`
3. Traducciones generadas en `traducidos/`
4. Originales movidos a `procesados/`

## Idiomas soportados

- `es` - Español
- `en` - Inglés
- `ca` - Catalán
- `fr` - Francés
- `de` - Alemán
- `it` - Italiano
- `pt` - Portugués
- `eu` - Euskera
- `gl` - Gallego

## Formatos soportados

- SCORM 1.2
- SCORM 2004
- Articulate Rise
- HTML estándar

## Documentación

Ver `manual.md` para instrucciones detalladas.
