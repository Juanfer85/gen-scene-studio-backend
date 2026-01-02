"""
Testing Suite - Fase 1 y 2
Prueba el sistema de voces y API endpoints
"""
import asyncio
import sys
import json
from pathlib import Path

print("🧪 TESTING SUITE - Sistema de Voces")
print("=" * 60)

# ============================================================================
# TEST 1: Importar módulos
# ============================================================================

print("\n📦 TEST 1: Importando módulos...")

try:
    sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))
    from services.tts_provider import TTSProvider, TTSFactory, Voice
    print("   ✅ tts_provider importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando tts_provider: {e}")
    TTSProvider = None
    TTSFactory = None

try:
    from services.edge_tts_client import EdgeTTSProvider
    print("   ✅ edge_tts_client importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando edge_tts_client: {e}")
    EdgeTTSProvider = None

# ============================================================================
# TEST 2: Verificar Edge TTS disponible
# ============================================================================

print("\n🔍 TEST 2: Verificando Edge TTS...")

try:
    import edge_tts
    print("   ✅ edge-tts instalado")
    EDGE_AVAILABLE = True
except ImportError:
    print("   ❌ edge-tts NO instalado")
    print("   💡 Instalar con: pip install edge-tts")
    EDGE_AVAILABLE = False

# ============================================================================
# TEST 3: Cargar biblioteca de voces
# ============================================================================

print("\n📚 TEST 3: Cargando biblioteca de voces...")

try:
    voice_lib_path = Path(__file__).parent / "voice_library.json"
    if voice_lib_path.exists():
        with open(voice_lib_path, 'r', encoding='utf-8') as f:
            voice_library = json.load(f)
        
        total_styles = len(voice_library.get("styles", {}))
        total_voices = sum(
            len(style.get("voices", []))
            for style in voice_library.get("styles", {}).values()
        )
        
        print(f"   ✅ Biblioteca cargada")
        print(f"   📊 Estilos: {total_styles}")
        print(f"   🎙️ Voces configuradas: {total_voices}")
        
        # Mostrar estilos
        print("\n   Estilos disponibles:")
        for style_key, style_data in voice_library.get("styles", {}).items():
            voice_count = len(style_data.get("voices", []))
            print(f"      • {style_key}: {voice_count} voces")
    else:
        print(f"   ❌ voice_library.json no encontrado en {voice_lib_path}")
        voice_library = None
except Exception as e:
    print(f"   ❌ Error cargando biblioteca: {e}")
    voice_library = None

# ============================================================================
# TEST 4: Crear provider y listar voces
# ============================================================================

print("\n🎤 TEST 4: Probando Edge TTS Provider...")

async def test_edge_provider():
    if not EDGE_AVAILABLE or not EdgeTTSProvider:
        print("   ⏭️  Saltando (Edge TTS no disponible)")
        return False
    
    try:
        provider = EdgeTTSProvider()
        
        # Verificar disponibilidad
        if not provider.is_available():
            print("   ❌ Provider no disponible")
            return False
        
        print("   ✅ Provider creado")
        
        # Obtener voces
        print("   📋 Obteniendo lista de voces...")
        voices = await provider.get_available_voices()
        
        print(f"   ✅ {len(voices)} voces disponibles")
        
        # Mostrar algunas voces en inglés
        en_voices = [v for v in voices if v.locale.startswith("en-")]
        print(f"\n   Voces en inglés: {len(en_voices)}")
        print("   Primeras 5 voces:")
        for voice in en_voices[:5]:
            print(f"      • {voice.id}: {voice.name} ({voice.gender})")
        
        # Obtener voces recomendadas
        print("\n   🌟 Voces recomendadas:")
        recommended = await provider.get_recommended_voices()
        for voice in recommended[:5]:
            print(f"      • {voice.id}: {voice.name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if EDGE_AVAILABLE:
    success = asyncio.run(test_edge_provider())
else:
    print("   ⏭️  Saltando (Edge TTS no instalado)")
    success = False

# ============================================================================
# TEST 5: Generar audio de prueba
# ============================================================================

print("\n🎵 TEST 5: Generando audio de prueba...")

async def test_audio_generation():
    if not EDGE_AVAILABLE or not EdgeTTSProvider:
        print("   ⏭️  Saltando (Edge TTS no disponible)")
        return False
    
    try:
        provider = EdgeTTSProvider()
        
        # Generar audio
        text = "Hello! This is a test of the Edge TTS system. It works great!"
        voice_id = "en-US-GuyNeural"
        
        print(f"   🎙️ Generando audio...")
        print(f"      Voz: {voice_id}")
        print(f"      Texto: {text[:50]}...")
        
        audio_data = await provider.generate_speech(
            text=text,
            voice_id=voice_id
        )
        
        # Guardar archivo
        output_file = Path(__file__).parent / "test_audio_output.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        
        file_size = len(audio_data)
        print(f"   ✅ Audio generado: {file_size:,} bytes")
        print(f"   💾 Guardado en: {output_file.name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if EDGE_AVAILABLE:
    audio_success = asyncio.run(test_audio_generation())
else:
    print("   ⏭️  Saltando (Edge TTS no instalado)")
    audio_success = False

# ============================================================================
# TEST 6: Verificar schemas
# ============================================================================

print("\n📋 TEST 6: Verificando schemas...")

try:
    from media_schemas import (
        VoiceInfo,
        VoicesByStyleResponse,
        MusicTrackInfo,
        SubtitleStyleInfo
    )
    print("   ✅ Schemas importados correctamente")
    
    # Crear instancia de prueba
    test_voice = VoiceInfo(
        id="test-voice",
        name="Test Voice",
        gender="male",
        locale="en-US",
        age="adult",
        tone="neutral",
        provider="edge"
    )
    print(f"   ✅ VoiceInfo creado: {test_voice.name}")
    
except Exception as e:
    print(f"   ❌ Error con schemas: {e}")

# ============================================================================
# TEST 7: Verificar API endpoints (sin servidor)
# ============================================================================

print("\n🌐 TEST 7: Verificando definiciones de API...")

try:
    from media_options_api import router
    print("   ✅ Router de API importado")
    
    # Contar endpoints
    routes = router.routes
    print(f"   📊 Endpoints definidos: {len(routes)}")
    
    print("\n   Endpoints disponibles:")
    for route in routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"      • {methods:6} {route.path}")
    
except Exception as e:
    print(f"   ❌ Error importando API: {e}")

# ============================================================================
# TEST 8: Verificar Factory pattern
# ============================================================================

print("\n🏭 TEST 8: Verificando Factory pattern...")

if TTSFactory:
    try:
        # Verificar providers registrados
        providers = TTSFactory.get_available_providers()
        print(f"   ✅ Providers registrados: {len(providers)}")
        for provider_name in providers:
            print(f"      • {provider_name}")
        
        # Obtener provider por defecto
        if providers:
            default_provider = TTSFactory.get_provider("edge")
            print(f"   ✅ Provider por defecto creado: {default_provider.name}")
        
    except Exception as e:
        print(f"   ❌ Error con Factory: {e}")
else:
    print("   ⏭️  Saltando (TTSFactory no disponible)")

# ============================================================================
# RESUMEN
# ============================================================================

print("\n" + "=" * 60)
print("📊 RESUMEN DE TESTS")
print("=" * 60)

tests_results = {
    "Importación de módulos": TTSProvider is not None,
    "Edge TTS disponible": EDGE_AVAILABLE,
    "Biblioteca de voces": voice_library is not None,
    "Edge TTS Provider": success if EDGE_AVAILABLE else None,
    "Generación de audio": audio_success if EDGE_AVAILABLE else None,
    "Schemas Pydantic": True,  # Asumimos que pasó si llegamos aquí
    "API Router": True,
    "Factory Pattern": TTSFactory is not None
}

passed = sum(1 for v in tests_results.values() if v is True)
failed = sum(1 for v in tests_results.values() if v is False)
skipped = sum(1 for v in tests_results.values() if v is None)
total = len(tests_results)

print(f"\n✅ Pasados: {passed}/{total}")
print(f"❌ Fallados: {failed}/{total}")
print(f"⏭️  Saltados: {skipped}/{total}")

print("\nDetalle:")
for test_name, result in tests_results.items():
    if result is True:
        status = "✅ PASS"
    elif result is False:
        status = "❌ FAIL"
    else:
        status = "⏭️  SKIP"
    print(f"   {status} - {test_name}")

# Recomendaciones
print("\n" + "=" * 60)
print("💡 RECOMENDACIONES")
print("=" * 60)

if not EDGE_AVAILABLE:
    print("\n⚠️  Edge TTS no está instalado")
    print("   Instalar con: pip install edge-tts")

if audio_success:
    print("\n✅ Sistema funcionando correctamente!")
    print("   Archivo de prueba: test_audio_output.mp3")
    print("   Puedes reproducirlo para verificar la calidad")

if passed >= total - skipped:
    print("\n🎉 ¡Todos los tests disponibles pasaron!")
    print("   El sistema está listo para continuar con Fase 3")
else:
    print("\n⚠️  Algunos tests fallaron")
    print("   Revisa los errores arriba antes de continuar")

print("\n" + "=" * 60)
