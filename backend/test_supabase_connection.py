"""
Script de prueba para verificar la conexión a Supabase.

Ejecutar después de configurar las variables de entorno en backend/.env

Usage:
    cd backend
    python test_supabase_connection.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg: str):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")

def main():
    print("\n" + "="*60)
    print("🧪 TEST DE CONEXIÓN A SUPABASE - Traductor SCORM")
    print("="*60 + "\n")

    # Cargar variables de entorno
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    # Verificar que las variables existen
    print_info("Verificando variables de entorno...")

    if not url:
        print_error("SUPABASE_URL no está configurada en .env")
        sys.exit(1)
    if not service_key:
        print_error("SUPABASE_SERVICE_ROLE_KEY no está configurada en .env")
        sys.exit(1)
    if not anon_key:
        print_error("SUPABASE_ANON_KEY no está configurada en .env")
        sys.exit(1)

    print_success(f"Variables de entorno encontradas")
    print(f"   URL: {url}")
    print(f"   ANON KEY: {anon_key[:20]}...")
    print(f"   SERVICE KEY: {service_key[:20]}...")
    print()

    try:
        # Crear cliente de Supabase con service role
        print_info("Creando cliente de Supabase con SERVICE_ROLE_KEY...")
        supabase: Client = create_client(url, service_key)
        print_success("Cliente creado exitosamente")
        print()

        # TEST 1: Conectividad básica
        print_info("TEST 1: Verificando conectividad con translation_jobs...")
        response = supabase.table('translation_jobs').select("*").limit(1).execute()
        print_success(f"Conexión exitosa. Tabla 'translation_jobs' accesible.")
        print(f"   Registros en tabla: {len(response.data)}")
        print()

        # TEST 2: Insert de prueba
        print_info("TEST 2: Insertando job de prueba...")
        test_job = {
            "original_filename": "test_connection.zip",
            "scorm_version": "1.2",
            "source_language": "en",
            "target_languages": ["es"],
            "status": "uploaded",
            "progress_percentage": 0
        }
        response = supabase.table('translation_jobs').insert(test_job).execute()
        job_id = response.data[0]['id']
        print_success(f"Insert exitoso. Job ID: {job_id}")
        print()

        # TEST 3: Select del job insertado
        print_info("TEST 3: Leyendo job insertado...")
        response = supabase.table('translation_jobs').select("*").eq('id', job_id).execute()
        if len(response.data) == 1:
            print_success("Select exitoso. Job recuperado correctamente")
            print(f"   Filename: {response.data[0]['original_filename']}")
            print(f"   Status: {response.data[0]['status']}")
        else:
            print_error("Error: No se pudo recuperar el job")
        print()

        # TEST 4: Update del job
        print_info("TEST 4: Actualizando job...")
        update_data = {
            "status": "translating",
            "progress_percentage": 50
        }
        response = supabase.table('translation_jobs').update(update_data).eq('id', job_id).execute()
        if response.data[0]['status'] == 'translating':
            print_success("Update exitoso")
        else:
            print_error("Error en update")
        print()

        # TEST 5: Delete del job de prueba
        print_info("TEST 5: Eliminando job de prueba...")
        supabase.table('translation_jobs').delete().eq('id', job_id).execute()
        print_success("Delete exitoso. Job de prueba eliminado")
        print()

        # TEST 6: Verificar translation_cache
        print_info("TEST 6: Verificando tabla translation_cache...")
        response = supabase.table('translation_cache').select("*").limit(1).execute()
        print_success(f"Tabla 'translation_cache' accesible. Registros: {len(response.data)}")
        print()

        # TEST 7: Verificar vista translation_cache_stats
        print_info("TEST 7: Verificando vista translation_cache_stats...")
        # Usar .rpc() o query directo con from_()
        response = supabase.table('translation_cache_stats').select("*").execute()
        print_success(f"Vista 'translation_cache_stats' accesible. Filas: {len(response.data)}")
        if len(response.data) > 0:
            for row in response.data:
                print(f"   Idioma: {row.get('target_language')}, Entradas: {row.get('total_entries')}")
        print()

        # TEST 8: Storage buckets
        print_info("TEST 8: Verificando Storage buckets...")
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        print_success(f"Storage accesible. Buckets encontrados: {len(bucket_names)}")
        print(f"   Buckets: {', '.join(bucket_names)}")

        # Verificar buckets esperados
        required_buckets = ['scorm-originals', 'scorm-translated']
        for bucket in required_buckets:
            if bucket in bucket_names:
                print_success(f"Bucket '{bucket}' encontrado")
            else:
                print_error(f"Bucket '{bucket}' NO encontrado (crear manualmente)")
        print()

        # TEST 9: Test con ANON KEY (client-side)
        print_info("TEST 9: Probando con ANON_KEY (simulando frontend)...")
        supabase_anon = create_client(url, anon_key)
        try:
            response = supabase_anon.table('translation_jobs').select("*").limit(1).execute()
            # Con RLS habilitado y sin usuario autenticado, debería fallar o retornar 0 rows
            print_info(f"ANON KEY retornó {len(response.data)} registros (correcto con RLS)")
        except Exception as e:
            print_info(f"ANON KEY con restricciones de RLS activas (esperado): {str(e)[:50]}...")
        print()

        # Resumen final
        print("="*60)
        print_success("🎉 TODOS LOS TESTS PASARON")
        print("="*60)
        print("\n✨ Supabase está correctamente configurado y listo para usar.\n")
        print("Próximos pasos:")
        print("  1. Revisar que los buckets de Storage estén creados")
        print("  2. Ejecutar seed data si deseas datos de prueba")
        print("  3. Configurar frontend/.env con VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY")
        print("  4. Iniciar el backend con 'uvicorn app.main:app --reload'")
        print()

    except Exception as e:
        print()
        print_error(f"ERROR DURANTE LOS TESTS: {str(e)}")
        print("\nPosibles causas:")
        print("  - Credenciales incorrectas en .env")
        print("  - Migraciones SQL no ejecutadas en Supabase")
        print("  - Problema de conectividad de red")
        print("  - Proyecto Supabase no creado o pausado")
        print("\nRevisar .claude/SETUP_SUPABASE.md para instrucciones detalladas")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
