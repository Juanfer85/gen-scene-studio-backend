# 🎙️ PLAN DE IMPLEMENTACIÓN: Voces, Subtítulos y Música
**Fecha:** 2 de Enero de 2026, 17:14 PM  
**Inspiración:** AutoShorts.ai

---

## 🎯 OBJETIVO

Implementar 3 funcionalidades clave para mejorar la experiencia de creación de videos:

1. ✅ **Preview de Voces** - Escuchar narrador antes de generar
2. ✅ **Voces por Estilo** - Grupo de voces específicas para cada estilo
3. ✅ **Subtítulos Personalizables** - Múltiples estilos de subtítulos
4. ✅ **Música de Fondo** - Tracks específicos por estilo

---

## 🎙️ PARTE 1: SISTEMA DE VOCES

### **1.1 Voces Disponibles por Estilo**

#### **Estilo: Cinematic Realism** 🎬
```json
{
  "style": "cinematic_realism",
  "voices": [
    {
      "id": "morgan_freeman",
      "name": "Morgan Freeman (Narrador Épico)",
      "gender": "male",
      "age": "mature",
      "accent": "american",
      "tone": "deep, authoritative, cinematic",
      "preview_url": "/audio/previews/morgan_freeman.mp3",
      "provider": "elevenlabs",
      "voice_id": "VR6AewLTigWG4xSOukaG"
    },
    {
      "id": "david_attenborough",
      "name": "David Attenborough (Documental)",
      "gender": "male",
      "age": "senior",
      "accent": "british",
      "tone": "wise, calm, educational",
      "preview_url": "/audio/previews/david_attenborough.mp3",
      "provider": "elevenlabs",
      "voice_id": "XB0fDUnXU5powFXDhCwa"
    },
    {
      "id": "epic_narrator",
      "name": "Epic Narrator (Trailer)",
      "gender": "male",
      "age": "adult",
      "accent": "american",
      "tone": "powerful, dramatic, intense",
      "preview_url": "/audio/previews/epic_narrator.mp3",
      "provider": "elevenlabs",
      "voice_id": "pNInz6obpgDQGcFmaJgB"
    }
  ],
  "default_voice": "morgan_freeman"
}
```

#### **Estilo: Cyberpunk** 🤖
```json
{
  "style": "cyberpunk",
  "voices": [
    {
      "id": "ai_assistant",
      "name": "AI Assistant (Futurista)",
      "gender": "female",
      "age": "young",
      "accent": "neutral",
      "tone": "robotic, synthetic, tech",
      "preview_url": "/audio/previews/ai_assistant.mp3",
      "provider": "elevenlabs",
      "voice_id": "EXAVITQu4vr4xnSDxMaL"
    },
    {
      "id": "cyber_narrator",
      "name": "Cyber Narrator (Hacker)",
      "gender": "male",
      "age": "young",
      "accent": "american",
      "tone": "edgy, mysterious, tech-savvy",
      "preview_url": "/audio/previews/cyber_narrator.mp3",
      "provider": "elevenlabs",
      "voice_id": "TxGEqnHWrfWFTfGW9XjX"
    },
    {
      "id": "glitch_voice",
      "name": "Glitch (Distorsionado)",
      "gender": "neutral",
      "age": "ageless",
      "accent": "synthetic",
      "tone": "glitchy, digital, futuristic",
      "preview_url": "/audio/previews/glitch_voice.mp3",
      "provider": "elevenlabs",
      "voice_id": "N2lVS1w4EtoT3dr4eOWO"
    }
  ],
  "default_voice": "ai_assistant"
}
```

#### **Estilo: Fantasy Adventure** ✨
```json
{
  "style": "fantasy_adventure",
  "voices": [
    {
      "id": "storyteller",
      "name": "Storyteller (Cuentacuentos)",
      "gender": "male",
      "age": "mature",
      "accent": "british",
      "tone": "warm, magical, enchanting",
      "preview_url": "/audio/previews/storyteller.mp3",
      "provider": "elevenlabs",
      "voice_id": "flq6f7yk4E4fJM5XTYuZ"
    },
    {
      "id": "fairy_voice",
      "name": "Fairy (Hada Mágica)",
      "gender": "female",
      "age": "young",
      "accent": "irish",
      "tone": "whimsical, light, playful",
      "preview_url": "/audio/previews/fairy_voice.mp3",
      "provider": "elevenlabs",
      "voice_id": "jsCqWAovK2LkecY7zXl4"
    },
    {
      "id": "wizard",
      "name": "Wizard (Mago Sabio)",
      "gender": "male",
      "age": "senior",
      "accent": "british",
      "tone": "wise, mystical, powerful",
      "preview_url": "/audio/previews/wizard.mp3",
      "provider": "elevenlabs",
      "voice_id": "pqHfZKP75CvOlQylNhV4"
    }
  ],
  "default_voice": "storyteller"
}
```

#### **Estilo: Motivational** 💪
```json
{
  "style": "motivational",
  "voices": [
    {
      "id": "coach",
      "name": "Coach (Entrenador)",
      "gender": "male",
      "age": "adult",
      "accent": "american",
      "tone": "energetic, inspiring, powerful",
      "preview_url": "/audio/previews/coach.mp3",
      "provider": "elevenlabs",
      "voice_id": "ErXwobaYiN019PkySvjV"
    },
    {
      "id": "motivational_speaker",
      "name": "Motivational Speaker (Orador)",
      "gender": "female",
      "age": "adult",
      "accent": "american",
      "tone": "uplifting, confident, dynamic",
      "preview_url": "/audio/previews/motivational_speaker.mp3",
      "provider": "elevenlabs",
      "voice_id": "MF3mGyEYCl7XYWbV9V6O"
    }
  ],
  "default_voice": "coach"
}
```

#### **Estilo: Educational** 📚
```json
{
  "style": "educational",
  "voices": [
    {
      "id": "professor",
      "name": "Professor (Profesor)",
      "gender": "male",
      "age": "mature",
      "accent": "american",
      "tone": "clear, informative, friendly",
      "preview_url": "/audio/previews/professor.mp3",
      "provider": "elevenlabs",
      "voice_id": "2EiwWnXFnvU5JabPnv8n"
    },
    {
      "id": "teacher",
      "name": "Teacher (Maestra)",
      "gender": "female",
      "age": "adult",
      "accent": "american",
      "tone": "patient, warm, encouraging",
      "preview_url": "/audio/previews/teacher.mp3",
      "provider": "elevenlabs",
      "voice_id": "ThT5KcBeYPX3keUQqHPh"
    }
  ],
  "default_voice": "professor"
}
```

#### **Estilo: Horror** 👻
```json
{
  "style": "horror",
  "voices": [
    {
      "id": "creepy_narrator",
      "name": "Creepy Narrator (Narrador Siniestro)",
      "gender": "male",
      "age": "adult",
      "accent": "american",
      "tone": "dark, ominous, unsettling",
      "preview_url": "/audio/previews/creepy_narrator.mp3",
      "provider": "elevenlabs",
      "voice_id": "SOYHLrjzK2X1ezoPC6cr"
    },
    {
      "id": "whisper",
      "name": "Whisper (Susurro)",
      "gender": "female",
      "age": "young",
      "accent": "neutral",
      "tone": "whispering, eerie, haunting",
      "preview_url": "/audio/previews/whisper.mp3",
      "provider": "elevenlabs",
      "voice_id": "cgSgspJ2msm6clMCkdW9"
    }
  ],
  "default_voice": "creepy_narrator"
}
```

---

## 🎵 PARTE 2: MÚSICA DE FONDO POR ESTILO

### **2.1 Tracks de Música por Estilo**

#### **Cinematic Realism** 🎬
```json
{
  "style": "cinematic_realism",
  "music_tracks": [
    {
      "id": "epic_orchestral",
      "name": "Epic Orchestral",
      "description": "Orquesta épica con cuerdas y metales",
      "mood": "dramatic, powerful, inspiring",
      "tempo": "medium",
      "duration": "loop",
      "preview_url": "/audio/music/epic_orchestral_preview.mp3",
      "full_url": "/audio/music/epic_orchestral.mp3",
      "volume": 0.3
    },
    {
      "id": "cinematic_ambient",
      "name": "Cinematic Ambient",
      "description": "Ambiente cinematográfico con pads",
      "mood": "atmospheric, mysterious, deep",
      "tempo": "slow",
      "duration": "loop",
      "preview_url": "/audio/music/cinematic_ambient_preview.mp3",
      "full_url": "/audio/music/cinematic_ambient.mp3",
      "volume": 0.25
    },
    {
      "id": "heroic_theme",
      "name": "Heroic Theme",
      "description": "Tema heroico con trompetas",
      "mood": "triumphant, uplifting, bold",
      "tempo": "medium-fast",
      "duration": "loop",
      "preview_url": "/audio/music/heroic_theme_preview.mp3",
      "full_url": "/audio/music/heroic_theme.mp3",
      "volume": 0.35
    }
  ],
  "default_track": "epic_orchestral"
}
```

#### **Cyberpunk** 🤖
```json
{
  "style": "cyberpunk",
  "music_tracks": [
    {
      "id": "synthwave",
      "name": "Synthwave",
      "description": "Synth retro-futurista estilo 80s",
      "mood": "nostalgic, neon, energetic",
      "tempo": "medium",
      "duration": "loop",
      "preview_url": "/audio/music/synthwave_preview.mp3",
      "full_url": "/audio/music/synthwave.mp3",
      "volume": 0.4
    },
    {
      "id": "cyberpunk_bass",
      "name": "Cyberpunk Bass",
      "description": "Bass pesado con glitches",
      "mood": "dark, edgy, futuristic",
      "tempo": "fast",
      "duration": "loop",
      "preview_url": "/audio/music/cyberpunk_bass_preview.mp3",
      "full_url": "/audio/music/cyberpunk_bass.mp3",
      "volume": 0.35
    },
    {
      "id": "neon_dreams",
      "name": "Neon Dreams",
      "description": "Electrónica atmosférica",
      "mood": "dreamy, synthetic, cool",
      "tempo": "medium-slow",
      "duration": "loop",
      "preview_url": "/audio/music/neon_dreams_preview.mp3",
      "full_url": "/audio/music/neon_dreams.mp3",
      "volume": 0.3
    }
  ],
  "default_track": "synthwave"
}
```

#### **Fantasy Adventure** ✨
```json
{
  "style": "fantasy_adventure",
  "music_tracks": [
    {
      "id": "magical_forest",
      "name": "Magical Forest",
      "description": "Flauta y arpa mágica",
      "mood": "whimsical, enchanting, mystical",
      "tempo": "medium",
      "duration": "loop",
      "preview_url": "/audio/music/magical_forest_preview.mp3",
      "full_url": "/audio/music/magical_forest.mp3",
      "volume": 0.3
    },
    {
      "id": "epic_quest",
      "name": "Epic Quest",
      "description": "Aventura épica con cuerdas",
      "mood": "adventurous, exciting, grand",
      "tempo": "medium-fast",
      "duration": "loop",
      "preview_url": "/audio/music/epic_quest_preview.mp3",
      "full_url": "/audio/music/epic_quest.mp3",
      "volume": 0.35
    },
    {
      "id": "fairy_tale",
      "name": "Fairy Tale",
      "description": "Cuento de hadas delicado",
      "mood": "gentle, magical, innocent",
      "tempo": "slow",
      "duration": "loop",
      "preview_url": "/audio/music/fairy_tale_preview.mp3",
      "full_url": "/audio/music/fairy_tale.mp3",
      "volume": 0.25
    }
  ],
  "default_track": "magical_forest"
}
```

#### **Motivational** 💪
```json
{
  "style": "motivational",
  "music_tracks": [
    {
      "id": "pump_up",
      "name": "Pump Up",
      "description": "Energético con drums potentes",
      "mood": "energetic, powerful, inspiring",
      "tempo": "fast",
      "duration": "loop",
      "preview_url": "/audio/music/pump_up_preview.mp3",
      "full_url": "/audio/music/pump_up.mp3",
      "volume": 0.4
    },
    {
      "id": "rise_up",
      "name": "Rise Up",
      "description": "Construcción épica motivacional",
      "mood": "uplifting, triumphant, bold",
      "tempo": "medium-fast",
      "duration": "loop",
      "preview_url": "/audio/music/rise_up_preview.mp3",
      "full_url": "/audio/music/rise_up.mp3",
      "volume": 0.35
    },
    {
      "id": "determination",
      "name": "Determination",
      "description": "Piano inspirador con strings",
      "mood": "determined, hopeful, strong",
      "tempo": "medium",
      "duration": "loop",
      "preview_url": "/audio/music/determination_preview.mp3",
      "full_url": "/audio/music/determination.mp3",
      "volume": 0.3
    }
  ],
  "default_track": "pump_up"
}
```

#### **Educational** 📚
```json
{
  "style": "educational",
  "music_tracks": [
    {
      "id": "curious_minds",
      "name": "Curious Minds",
      "description": "Piano ligero y optimista",
      "mood": "curious, friendly, light",
      "tempo": "medium",
      "duration": "loop",
      "preview_url": "/audio/music/curious_minds_preview.mp3",
      "full_url": "/audio/music/curious_minds.mp3",
      "volume": 0.25
    },
    {
      "id": "learning_journey",
      "name": "Learning Journey",
      "description": "Acústica suave y positiva",
      "mood": "encouraging, warm, gentle",
      "tempo": "slow-medium",
      "duration": "loop",
      "preview_url": "/audio/music/learning_journey_preview.mp3",
      "full_url": "/audio/music/learning_journey.mp3",
      "volume": 0.2
    }
  ],
  "default_track": "curious_minds"
}
```

#### **Horror** 👻
```json
{
  "style": "horror",
  "music_tracks": [
    {
      "id": "dark_ambient",
      "name": "Dark Ambient",
      "description": "Drones oscuros y tensos",
      "mood": "ominous, dark, unsettling",
      "tempo": "very slow",
      "duration": "loop",
      "preview_url": "/audio/music/dark_ambient_preview.mp3",
      "full_url": "/audio/music/dark_ambient.mp3",
      "volume": 0.3
    },
    {
      "id": "creepy_strings",
      "name": "Creepy Strings",
      "description": "Cuerdas inquietantes",
      "mood": "eerie, tense, scary",
      "tempo": "slow",
      "duration": "loop",
      "preview_url": "/audio/music/creepy_strings_preview.mp3",
      "full_url": "/audio/music/creepy_strings.mp3",
      "volume": 0.35
    },
    {
      "id": "haunting_whispers",
      "name": "Haunting Whispers",
      "description": "Susurros y efectos de terror",
      "mood": "haunting, mysterious, chilling",
      "tempo": "slow",
      "duration": "loop",
      "preview_url": "/audio/music/haunting_whispers_preview.mp3",
      "full_url": "/audio/music/haunting_whispers.mp3",
      "volume": 0.25
    }
  ],
  "default_track": "dark_ambient"
}
```

---

## 📝 PARTE 3: ESTILOS DE SUBTÍTULOS

### **3.1 Estilos Disponibles (Inspirados en AutoShorts.ai)**

#### **Estilo 1: Classic** (Por defecto)
```json
{
  "id": "classic",
  "name": "Classic",
  "description": "Subtítulos clásicos centrados",
  "preview_image": "/images/subtitles/classic.png",
  "config": {
    "position": "bottom-center",
    "font_family": "Arial, sans-serif",
    "font_size": "48px",
    "font_weight": "bold",
    "text_color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": "3px",
    "background_color": "rgba(0, 0, 0, 0.7)",
    "background_padding": "10px 20px",
    "background_radius": "8px",
    "text_align": "center",
    "max_width": "80%",
    "animation": "fade",
    "shadow": "0 2px 4px rgba(0,0,0,0.5)"
  }
}
```

#### **Estilo 2: MrBeast** (Viral)
```json
{
  "id": "mrbeast",
  "name": "MrBeast Style",
  "description": "Subtítulos grandes y amarillos estilo MrBeast",
  "preview_image": "/images/subtitles/mrbeast.png",
  "config": {
    "position": "center",
    "font_family": "Impact, sans-serif",
    "font_size": "72px",
    "font_weight": "900",
    "text_color": "#FFFF00",
    "stroke_color": "#000000",
    "stroke_width": "6px",
    "background_color": "transparent",
    "text_align": "center",
    "max_width": "90%",
    "animation": "bounce",
    "text_transform": "uppercase",
    "shadow": "0 4px 8px rgba(0,0,0,0.8)",
    "word_highlight": true,
    "highlight_color": "#FF0000"
  }
}
```

#### **Estilo 3: TikTok Trendy**
```json
{
  "id": "tiktok_trendy",
  "name": "TikTok Trendy",
  "description": "Subtítulos palabra por palabra con highlight",
  "preview_image": "/images/subtitles/tiktok.png",
  "config": {
    "position": "center",
    "font_family": "Montserrat, sans-serif",
    "font_size": "56px",
    "font_weight": "800",
    "text_color": "#FFFFFF",
    "stroke_color": "#FF1493",
    "stroke_width": "4px",
    "background_color": "transparent",
    "text_align": "center",
    "max_width": "85%",
    "animation": "word_by_word",
    "word_highlight": true,
    "highlight_color": "#00F5FF",
    "highlight_scale": "1.2",
    "shadow": "0 3px 6px rgba(255,20,147,0.6)"
  }
}
```

#### **Estilo 4: Minimalist**
```json
{
  "id": "minimalist",
  "name": "Minimalist",
  "description": "Subtítulos minimalistas sin fondo",
  "preview_image": "/images/subtitles/minimalist.png",
  "config": {
    "position": "bottom-center",
    "font_family": "Helvetica Neue, sans-serif",
    "font_size": "42px",
    "font_weight": "500",
    "text_color": "#FFFFFF",
    "stroke_color": "transparent",
    "stroke_width": "0px",
    "background_color": "transparent",
    "text_align": "center",
    "max_width": "75%",
    "animation": "fade",
    "shadow": "0 2px 8px rgba(0,0,0,0.9)"
  }
}
```

#### **Estilo 5: Neon Glow**
```json
{
  "id": "neon_glow",
  "name": "Neon Glow",
  "description": "Subtítulos con efecto neón brillante",
  "preview_image": "/images/subtitles/neon.png",
  "config": {
    "position": "center",
    "font_family": "Orbitron, sans-serif",
    "font_size": "52px",
    "font_weight": "700",
    "text_color": "#00FFFF",
    "stroke_color": "transparent",
    "stroke_width": "0px",
    "background_color": "transparent",
    "text_align": "center",
    "max_width": "80%",
    "animation": "glow_pulse",
    "shadow": "0 0 20px #00FFFF, 0 0 40px #00FFFF, 0 0 60px #00FFFF",
    "text_shadow": "0 0 10px #00FFFF"
  }
}
```

#### **Estilo 6: Karaoke**
```json
{
  "id": "karaoke",
  "name": "Karaoke",
  "description": "Subtítulos que se llenan de color progresivamente",
  "preview_image": "/images/subtitles/karaoke.png",
  "config": {
    "position": "bottom-center",
    "font_family": "Roboto, sans-serif",
    "font_size": "50px",
    "font_weight": "700",
    "text_color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": "3px",
    "background_color": "rgba(0, 0, 0, 0.6)",
    "background_padding": "12px 24px",
    "background_radius": "10px",
    "text_align": "center",
    "max_width": "85%",
    "animation": "karaoke_fill",
    "fill_color": "#FFD700",
    "shadow": "0 2px 6px rgba(0,0,0,0.6)"
  }
}
```

#### **Estilo 7: Comic Book**
```json
{
  "id": "comic_book",
  "name": "Comic Book",
  "description": "Estilo cómic con borde irregular",
  "preview_image": "/images/subtitles/comic.png",
  "config": {
    "position": "top-center",
    "font_family": "Comic Sans MS, cursive",
    "font_size": "54px",
    "font_weight": "900",
    "text_color": "#000000",
    "stroke_color": "#FFFFFF",
    "stroke_width": "4px",
    "background_color": "#FFFFFF",
    "background_padding": "15px 25px",
    "background_radius": "0px",
    "background_border": "4px solid #000000",
    "text_align": "center",
    "max_width": "75%",
    "animation": "pop",
    "text_transform": "uppercase",
    "shadow": "4px 4px 0px #000000"
  }
}
```

#### **Estilo 8: Elegant**
```json
{
  "id": "elegant",
  "name": "Elegant",
  "description": "Subtítulos elegantes con serif",
  "preview_image": "/images/subtitles/elegant.png",
  "config": {
    "position": "bottom-center",
    "font_family": "Playfair Display, serif",
    "font_size": "46px",
    "font_weight": "600",
    "text_color": "#F5F5DC",
    "stroke_color": "transparent",
    "stroke_width": "0px",
    "background_color": "rgba(0, 0, 0, 0.75)",
    "background_padding": "14px 28px",
    "background_radius": "12px",
    "text_align": "center",
    "max_width": "70%",
    "animation": "fade",
    "shadow": "0 3px 10px rgba(0,0,0,0.7)",
    "letter_spacing": "1px"
  }
}
```

---

## 🏗️ PARTE 4: ARQUITECTURA DE IMPLEMENTACIÓN

### **4.1 Backend - Nuevos Endpoints**

#### **Endpoint 1: Obtener Voces por Estilo**
```python
@router.get("/api/voices/{style_key}")
async def get_voices_by_style(style_key: str):
    """
    Retorna las voces disponibles para un estilo específico
    """
    voices = VOICE_LIBRARY.get(style_key, VOICE_LIBRARY["default"])
    return {
        "success": True,
        "style": style_key,
        "voices": voices["voices"],
        "default_voice": voices["default_voice"]
    }
```

#### **Endpoint 2: Preview de Voz**
```python
@router.get("/api/voice-preview/{voice_id}")
async def get_voice_preview(voice_id: str):
    """
    Retorna el audio de preview de una voz
    """
    voice = find_voice_by_id(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return FileResponse(
        voice["preview_url"],
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={voice_id}_preview.mp3"}
    )
```

#### **Endpoint 3: Obtener Música por Estilo**
```python
@router.get("/api/music/{style_key}")
async def get_music_by_style(style_key: str):
    """
    Retorna los tracks de música disponibles para un estilo
    """
    music = MUSIC_LIBRARY.get(style_key, MUSIC_LIBRARY["default"])
    return {
        "success": True,
        "style": style_key,
        "tracks": music["music_tracks"],
        "default_track": music["default_track"]
    }
```

#### **Endpoint 4: Obtener Estilos de Subtítulos**
```python
@router.get("/api/subtitle-styles")
async def get_subtitle_styles():
    """
    Retorna todos los estilos de subtítulos disponibles
    """
    return {
        "success": True,
        "styles": SUBTITLE_STYLES,
        "default_style": "classic"
    }
```

### **4.2 Frontend - Componentes Nuevos**

#### **Componente 1: VoiceSelector**
```typescript
interface VoiceSelectorProps {
  styleKey: string;
  selectedVoice: string;
  onVoiceChange: (voiceId: string) => void;
}

function VoiceSelector({ styleKey, selectedVoice, onVoiceChange }: VoiceSelectorProps) {
  const [voices, setVoices] = useState([]);
  const [playingPreview, setPlayingPreview] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    // Fetch voices for this style
    fetch(`/api/voices/${styleKey}`)
      .then(res => res.json())
      .then(data => setVoices(data.voices));
  }, [styleKey]);

  const playPreview = (voiceId: string, previewUrl: string) => {
    if (playingPreview === voiceId) {
      audioRef.current?.pause();
      setPlayingPreview(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = previewUrl;
        audioRef.current.play();
        setPlayingPreview(voiceId);
      }
    }
  };

  return (
    <div className="voice-selector">
      <h3>🎙️ Seleccionar Narrador</h3>
      <div className="voice-grid">
        {voices.map(voice => (
          <div 
            key={voice.id}
            className={`voice-card ${selectedVoice === voice.id ? 'selected' : ''}`}
            onClick={() => onVoiceChange(voice.id)}
          >
            <div className="voice-info">
              <h4>{voice.name}</h4>
              <p className="voice-description">{voice.tone}</p>
              <span className="voice-accent">{voice.accent} • {voice.gender}</span>
            </div>
            <button
              className="preview-button"
              onClick={(e) => {
                e.stopPropagation();
                playPreview(voice.id, voice.preview_url);
              }}
            >
              {playingPreview === voice.id ? '⏸️ Pausar' : '▶️ Preview'}
            </button>
          </div>
        ))}
      </div>
      <audio ref={audioRef} onEnded={() => setPlayingPreview(null)} />
    </div>
  );
}
```

#### **Componente 2: MusicSelector**
```typescript
interface MusicSelectorProps {
  styleKey: string;
  selectedTrack: string;
  onTrackChange: (trackId: string) => void;
}

function MusicSelector({ styleKey, selectedTrack, onTrackChange }: MusicSelectorProps) {
  const [tracks, setTracks] = useState([]);
  const [playingPreview, setPlayingPreview] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    fetch(`/api/music/${styleKey}`)
      .then(res => res.json())
      .then(data => setTracks(data.tracks));
  }, [styleKey]);

  const playPreview = (trackId: string, previewUrl: string) => {
    if (playingPreview === trackId) {
      audioRef.current?.pause();
      setPlayingPreview(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = previewUrl;
        audioRef.current.play();
        setPlayingPreview(trackId);
      }
    }
  };

  return (
    <div className="music-selector">
      <h3>🎵 Música de Fondo</h3>
      <div className="music-grid">
        {tracks.map(track => (
          <div 
            key={track.id}
            className={`music-card ${selectedTrack === track.id ? 'selected' : ''}`}
            onClick={() => onTrackChange(track.id)}
          >
            <div className="music-info">
              <h4>{track.name}</h4>
              <p className="music-description">{track.description}</p>
              <div className="music-tags">
                <span className="mood-tag">{track.mood.split(',')[0]}</span>
                <span className="tempo-tag">{track.tempo}</span>
              </div>
            </div>
            <button
              className="preview-button"
              onClick={(e) => {
                e.stopPropagation();
                playPreview(track.id, track.preview_url);
              }}
            >
              {playingPreview === track.id ? '⏸️' : '▶️'}
            </button>
          </div>
        ))}
      </div>
      <audio ref={audioRef} loop onEnded={() => setPlayingPreview(null)} />
    </div>
  );
}
```

#### **Componente 3: SubtitleStyleSelector**
```typescript
interface SubtitleStyleSelectorProps {
  selectedStyle: string;
  onStyleChange: (styleId: string) => void;
}

function SubtitleStyleSelector({ selectedStyle, onStyleChange }: SubtitleStyleSelectorProps) {
  const [styles, setStyles] = useState([]);

  useEffect(() => {
    fetch('/api/subtitle-styles')
      .then(res => res.json())
      .then(data => setStyles(data.styles));
  }, []);

  return (
    <div className="subtitle-style-selector">
      <h3>📝 Estilo de Subtítulos</h3>
      <div className="subtitle-grid">
        {styles.map(style => (
          <div 
            key={style.id}
            className={`subtitle-card ${selectedStyle === style.id ? 'selected' : ''}`}
            onClick={() => onStyleChange(style.id)}
          >
            <div className="subtitle-preview">
              <img src={style.preview_image} alt={style.name} />
            </div>
            <div className="subtitle-info">
              <h4>{style.name}</h4>
              <p>{style.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 📋 PARTE 5: PLAN DE IMPLEMENTACIÓN

### **Fase 1: Backend (2-3 días)**

#### **Día 1: Estructura de Datos**
- [ ] Crear `voice_library.py` con todas las voces por estilo
- [ ] Crear `music_library.py` con todos los tracks por estilo
- [ ] Crear `subtitle_styles.py` con todos los estilos de subtítulos
- [ ] Crear endpoints API para voces, música y subtítulos

#### **Día 2: Integración con ElevenLabs**
- [ ] Configurar API de ElevenLabs para TTS
- [ ] Crear función para generar audio de narración
- [ ] Crear función para generar previews de voces
- [ ] Implementar cache de previews

#### **Día 3: Procesamiento de Video**
- [ ] Integrar FFmpeg para agregar subtítulos
- [ ] Crear función para renderizar subtítulos con estilos
- [ ] Integrar música de fondo con FFmpeg
- [ ] Implementar mezcla de audio (voz + música)

### **Fase 2: Frontend (2-3 días)**

#### **Día 1: Componentes Base**
- [ ] Crear componente `VoiceSelector`
- [ ] Crear componente `MusicSelector`
- [ ] Crear componente `SubtitleStyleSelector`
- [ ] Implementar preview de audio

#### **Día 2: Integración en Quick Create**
- [ ] Agregar selectores a la página de Quick Create
- [ ] Implementar lógica de cambio de estilo
- [ ] Conectar con API backend
- [ ] Implementar estados de carga

#### **Día 3: UI/UX Polish**
- [ ] Diseñar cards de voces con estilo Gen Scene
- [ ] Diseñar cards de música
- [ ] Diseñar previews de subtítulos
- [ ] Agregar animaciones y transiciones

### **Fase 3: Testing y Optimización (1-2 días)**

#### **Testing:**
- [ ] Probar cada voz con diferentes estilos
- [ ] Probar cada track de música
- [ ] Probar cada estilo de subtítulos
- [ ] Verificar sincronización de audio
- [ ] Verificar calidad de subtítulos

#### **Optimización:**
- [ ] Optimizar carga de previews
- [ ] Implementar lazy loading de audio
- [ ] Comprimir archivos de música
- [ ] Cachear voces frecuentes

---

## 💰 PARTE 6: COSTOS Y RECURSOS

### **Costos de API:**

**ElevenLabs (Voces):**
- Plan Creator: $22/mes (100,000 caracteres)
- Plan Pro: $99/mes (500,000 caracteres)
- Costo por video (5s narración ~50 caracteres): $0.01

**Música:**
- Epidemic Sound: $15/mes (música libre de derechos)
- Artlist: $14.99/mes (música + SFX)
- O usar música Creative Commons (gratis)

**Total Estimado:** ~$40-50/mes

---

## 🎯 PARTE 7: PRIORIZACIÓN

### **Must Have (Fase 1):**
1. ✅ Selector de voces con preview
2. ✅ 3-4 voces por estilo principal
3. ✅ Subtítulos básicos (Classic, MrBeast, TikTok)

### **Should Have (Fase 2):**
1. ✅ Música de fondo con preview
2. ✅ 2-3 tracks por estilo
3. ✅ Más estilos de subtítulos (6-8 total)

### **Nice to Have (Fase 3):**
1. ⏳ Personalización avanzada de subtítulos
2. ⏳ Upload de música personalizada
3. ⏳ Clonación de voz del usuario

---

## 📝 PRÓXIMOS PASOS INMEDIATOS

1. **Decidir** qué fase implementar primero
2. **Configurar** cuenta de ElevenLabs
3. **Obtener** música libre de derechos
4. **Crear** estructura de archivos backend
5. **Diseñar** componentes frontend en Lovable

---

**¿Quieres que empiece con alguna fase específica o prefieres un prompt para Lovable que incluya todo esto?** 🎙️🎵📝

*Documento generado: 2 de Enero de 2026, 17:14 PM*  
*Plan completo de implementación de voces, música y subtítulos*
