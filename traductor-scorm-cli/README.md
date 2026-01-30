# Traductor SCORM CLI

Herramienta de línea de comandos para traducir paquetes SCORM a múltiples idiomas.

## Instalación

```bash
cd traductor-scorm-cli
pip install -r requirements.txt
```

## Uso

```bash
# Traducir SCORM al catalán
python traductor.py mi-curso.zip --idioma ca

# Traducir SCORM al inglés
python traductor.py mi-curso.zip --idioma en

# Traducir a múltiples idiomas
python traductor.py mi-curso.zip --idioma ca,en,fr

# Especificar carpeta de salida
python traductor.py mi-curso.zip --idioma ca --salida ./traducciones/
```

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

- SCORM 1.2 ✅
- SCORM 2004 ✅
- Articulate Rise ✅
- HTML estándar ✅
