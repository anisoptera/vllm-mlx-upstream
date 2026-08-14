# Soporte de Audio

vllm-mlx soporta el procesamiento de audio mediante [mlx-audio](https://github.com/Blaizzy/mlx-audio), y ofrece:

- **STT (Speech-to-Text)**: Whisper, Parakeet
- **TTS (Text-to-Speech)**: Kokoro, Chatterbox, VibeVoice, VoxCPM
- **Procesamiento de audio**: SAM-Audio (separación de voz)

## Instalación

```bash
# Soporte de audio principal
pip install mlx-audio>=0.2.9

# Dependencias requeridas para TTS
pip install sounddevice soundfile scipy numba tiktoken misaki spacy num2words loguru phonemizer

# Descargar el modelo de inglés de spacy
python -m spacy download en_core_web_sm

# Para TTS en idiomas distintos al inglés (español, francés, etc.), instalar espeak-ng:
# macOS
brew install espeak-ng

# Ubuntu/Debian
# sudo apt-get install espeak-ng
```

O instalar todas las dependencias de audio de una sola vez:

```bash
pip install vllm-mlx[audio]
python -m spacy download en_core_web_sm
brew install espeak-ng  # macOS, para idiomas distintos al inglés
```

## Inicio Rápido

### Speech-to-Text (Transcripción)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")

# Transcribir un archivo de audio
with open("audio.mp3", "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=f,
        language="en"  # opcional
    )
print(transcript.text)
```

### Text-to-Speech (Generación)

```python
# Generar voz
audio = client.audio.speech.create(
    model="kokoro",
    input="Hello, how are you?",
    voice="af_heart",
    speed=1.0
)

# Guardar en archivo
with open("output.wav", "wb") as f:
    f.write(audio.content)
```

### Separación de Voz (SAM-Audio)

Aislar la voz del ruido de fondo, música u otros sonidos:

```python
from vllm_mlx.audio import AudioProcessor

# Cargar el modelo SAM-Audio
processor = AudioProcessor("mlx-community/sam-audio-large-fp16")
processor.load()

# Separar el habla del audio
result = processor.separate("meeting_with_music.mp3", description="speech")

# Guardar la voz aislada y el fondo
processor.save(result.target, "voice_only.wav")
processor.save(result.residual, "background_only.wav")
```

**Ejemplo de CLI:**
```bash
python examples/audio_separation_example.py meeting.mp3 --play
python examples/audio_separation_example.py song.mp3 --description music -o music.wav
```

### Demo de Separación de Batería

Aislar la batería de una canción de rock usando SAM-Audio:

| Audio | Descripción | Escuchar |
|-------|-------------|----------|
| Original | "Get Ready" de David Fesliyan (30s, libre de regalías) | [🎵 rock_get_ready.mp3](https://github.com/waybarrios/vllm-mlx/blob/main/examples/rock_get_ready.mp3?raw=1) |
| Batería aislada | Batería extraída por SAM-Audio | [🥁 drums_isolated.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/drums_isolated.wav?raw=1) |
| Sin batería | Pista con la batería eliminada | [🎸 rock_no_drums.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/rock_no_drums.wav?raw=1) |

```bash
# Aislar la batería de una canción de rock
python examples/audio_separation_example.py examples/rock_get_ready.mp3 \
  --description "drums" \
  --output drums_isolated.wav \
  --background rock_no_drums.wav
```

**Rendimiento:** 30 segundos de audio procesados en ~20 segundos en M4 Max.

## Modelos Soportados

### Modelos STT (Speech-to-Text)

| Modelo | Alias | Idiomas | Velocidad | Calidad |
|--------|-------|---------|-----------|---------|
| `mlx-community/whisper-large-v3-mlx` | `whisper-large-v3` | 99+ | Media | Mejor |
| `mlx-community/whisper-large-v3-turbo` | `whisper-large-v3-turbo` | 99+ | Rápida | Muy buena |
| `mlx-community/whisper-medium-mlx` | `whisper-medium` | 99+ | Rápida | Buena |
| `mlx-community/whisper-small-mlx` | `whisper-small` | 99+ | Muy rápida | Aceptable |
| `mlx-community/parakeet-tdt-0.6b-v2` | `parakeet` | Inglés | La más rápida | Muy buena |
| `mlx-community/parakeet-tdt-0.6b-v3` | `parakeet-v3` | Inglés | La más rápida | Mejor |

**Recomendación:**
- Multilingüe: `whisper-large-v3`
- Solo inglés: `parakeet` (3x más rápido)

### Modelos TTS (Text-to-Speech)

#### Kokoro (Rápido y ligero) - Recomendado

| Modelo | Alias | Tamaño | Idiomas |
|--------|-------|--------|---------|
| `mlx-community/Kokoro-82M-bf16` | `kokoro` | 82M | EN, ES, FR, JA, ZH, HI, IT, PT |
| `mlx-community/Kokoro-82M-4bit` | `kokoro-4bit` | 82M | EN, ES, FR, JA, ZH, HI, IT, PT |

**Voces (11):**
- Femenino estadounidense: `af_heart`, `af_bella`, `af_nicole`, `af_sarah`, `af_sky`
- Masculino estadounidense: `am_adam`, `am_michael`
- Femenino británico: `bf_emma`, `bf_isabella`
- Masculino británico: `bm_george`, `bm_lewis`

**Códigos de idioma:**
| Código | Idioma | Código | Idioma |
|--------|--------|--------|--------|
| `a` / `en` | English (US) | `e` / `es` | Español |
| `b` / `en-gb` | English (UK) | `f` / `fr` | Français |
| `j` / `ja` | 日本語 | `z` / `zh` | 中文 |
| `i` / `it` | Italiano | `p` / `pt` | Português |
| `h` / `hi` | हिन्दी | | |

#### Chatterbox (Multilingüe y expresivo)

| Modelo | Alias | Tamaño | Idiomas |
|--------|-------|--------|---------|
| `mlx-community/chatterbox-turbo-fp16` | `chatterbox` | 134M | 15+ idiomas |
| `mlx-community/chatterbox-turbo-4bit` | `chatterbox-4bit` | 134M | 15+ idiomas |

**Idiomas soportados:** EN, ES, FR, DE, IT, PT, RU, JA, ZH, KO, AR, HI, NL, PL, TR

#### VibeVoice (Tiempo real)

| Modelo | Alias | Tamaño | Caso de uso |
|--------|-------|--------|-------------|
| `mlx-community/VibeVoice-Realtime-0.5B-4bit` | `vibevoice` | 200M | Baja latencia, inglés |

#### VoxCPM (Chino/Inglés)

| Modelo | Alias | Tamaño | Idiomas |
|--------|-------|--------|---------|
| `mlx-community/VoxCPM1.5` | `voxcpm` | 0.9B | ZH, EN |
| `mlx-community/VoxCPM1.5-4bit` | `voxcpm-4bit` | 200M | ZH, EN |

### Modelos de Procesamiento de Audio

#### SAM-Audio (Separación de Voz)

| Modelo | Tamaño | Caso de uso |
|--------|--------|-------------|
| `mlx-community/sam-audio-large-fp16` | 3B | Mejor calidad |
| `mlx-community/sam-audio-large` | 3B | Estándar |
| `mlx-community/sam-audio-small-fp16` | 0.6B | Rápido |
| `mlx-community/sam-audio-small` | 0.6B | Ligero |

## Referencia de API

### POST /v1/audio/transcriptions

Transcribir audio a texto (compatible con la API OpenAI Whisper).

**Parámetros:**
- `file`: Archivo de audio (mp3, wav, m4a, webm)
- `model`: Nombre o alias del modelo
- `language`: Código de idioma (opcional, se detecta automáticamente)
- `response_format`: `json` o `text`

**Límites:**
- Tamaño máximo de carga por defecto: 25 MiB
- Se puede ajustar con `--max-audio-upload-mb`

**Ejemplo:**
```bash
curl http://localhost:8000/v1/audio/transcriptions \
  -F file=@audio.mp3 \
  -F model=whisper-large-v3
```

### POST /v1/audio/speech

Generar voz a partir de texto (compatible con la API OpenAI TTS).

**Parámetros:**
- `model`: Nombre o alias del modelo
- `input`: Texto a sintetizar
- `voice`: ID de la voz
- `speed`: Velocidad del habla (0.5 a 2.0)
- `response_format`: `wav`, `mp3`

**Límites:**
- Límite de entrada por defecto: 4096 caracteres
- Se puede ajustar con `--max-tts-input-chars`

**Ejemplo:**
```bash
curl http://localhost:8000/v1/audio/speech \
  -d '{"model": "kokoro", "input": "Hello world", "voice": "af_heart"}' \
  -H "Content-Type: application/json" \
  --output speech.wav
```

### GET /v1/audio/voices

Listar las voces disponibles para un modelo.

**Ejemplo:**
```bash
curl http://localhost:8000/v1/audio/voices?model=kokoro
```

## Ejemplos de CLI

### Transcripción en Vivo / Subtítulos

Transcripción de voz a texto en tiempo real desde el micrófono:

```bash
# Subtítulos con whisper-large-v3 (mejor calidad)
python examples/closed_captions.py --language es --chunk 5

# Modelo más rápido para menor latencia
python examples/closed_captions.py --language en --model whisper-turbo --chunk 3

# Transcripción básica por micrófono (grabar y luego transcribir)
python examples/mic_transcribe.py --language es

# Transcripción en fragmentos en tiempo real
python examples/mic_realtime.py --language es --chunk 3

# Transcripción en vivo con detección de actividad de voz
python examples/mic_live.py --language es
```

**Requisitos:**
```bash
pip install sounddevice soundfile numpy
```

### TTS Básico

```bash
# Ejemplo simple de TTS
python examples/tts_example.py "Hello, how are you?" --play

# Con una voz diferente
python examples/tts_example.py "Hello!" --voice am_michael --play

# Guardar en archivo
python examples/tts_example.py "Welcome to the demo" -o greeting.wav

# Listar las voces disponibles
python examples/tts_example.py --list-voices
```

### TTS Multilingüe

```bash
# Inglés (selecciona automáticamente el mejor modelo)
python examples/tts_multilingual.py "Hello world" --play

# Español
python examples/tts_multilingual.py "Hola mundo" --lang es --play

# Francés
python examples/tts_multilingual.py "Bonjour le monde" --lang fr --play

# Japonés
python examples/tts_multilingual.py "こんにちは" --lang ja --play

# Chino
python examples/tts_multilingual.py "你好世界" --lang zh --play

# Usar un modelo específico
python examples/tts_multilingual.py "Hello" --model chatterbox --play

# Listar todos los modelos
python examples/tts_multilingual.py --list-models

# Listar todos los idiomas
python examples/tts_multilingual.py --list-languages
```

### Ejemplos de Asistente de Voz para Negocios

Muestras de voz pregeneradas con **voces nativas** para casos de uso empresariales comunes:

| Idioma | Voz | Mensaje | Escuchar |
|--------|-----|---------|----------|
| 🇺🇸 Inglés | af_heart | "Welcome to First National Bank. How may I assist you today?" | [▶️ assistant_bank_en.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/assistant_bank_en.wav?raw=1) |
| 🇪🇸 Español | ef_dora | "Gracias por llamar a servicio al cliente. Un agente le atenderá pronto." | [▶️ assistant_service_es.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/assistant_service_es.wav?raw=1) |
| 🇫🇷 Francés | ff_siwis | "Bienvenue. Votre appel est important pour nous." | [▶️ assistant_callcenter_fr.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/assistant_callcenter_fr.wav?raw=1) |
| 🇨🇳 Chino | zf_xiaobei | "欢迎致电技术支持中心。我们将竭诚为您服务。" | [▶️ assistant_support_zh.wav](https://github.com/waybarrios/vllm-mlx/blob/main/examples/assistant_support_zh.wav?raw=1) |

**Genera tus propias muestras con voces nativas:**
```bash
# Inglés - Asistente bancario (voz nativa: af_heart)
python -m mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 \
  --text "Welcome to First National Bank. How may I assist you today?" \
  --voice af_heart --lang_code a --file_prefix assistant_bank_en

# Español - Atención al cliente (voz nativa: ef_dora)
python -m mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 \
  --text "Gracias por llamar a servicio al cliente. Un agente le atendera pronto." \
  --voice ef_dora --lang_code e --file_prefix assistant_service_es

# Francés - Centro de llamadas (voz nativa: ff_siwis)
python -m mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 \
  --text "Bienvenue. Votre appel est important pour nous." \
  --voice ff_siwis --lang_code f --file_prefix assistant_callcenter_fr

# Chino - Soporte técnico (voz nativa: zf_xiaobei)
python -m mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 \
  --text "欢迎致电技术支持中心。我们将竭诚为您服务。" \
  --voice zf_xiaobei --lang_code z --file_prefix assistant_support_zh
```

### Referencia de Voces Nativas

| Idioma | Código | Voces |
|--------|--------|-------|
| English (US) | `a` | af_heart, af_bella, af_nicole, am_adam, am_michael |
| English (UK) | `b` | bf_emma, bf_isabella, bm_george, bm_lewis |
| Español | `e` | ef_dora, em_alex, em_santa |
| Français | `f` | ff_siwis |
| 中文 | `z` | zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zm_yunjian, zm_yunxi |
| 日本語 | `j` | jf_alpha, jf_gongitsune, jm_kumo |
| Italiano | `i` | if_sara, im_nicola |
| Português | `p` | pf_dora, pm_alex |
| हिन्दी | `h` | hf_alpha, hf_beta, hm_omega |

## API de Python

### Uso Directo (sin servidor)

```python
from vllm_mlx.audio import STTEngine, TTSEngine, AudioProcessor

# Speech-to-Text
stt = STTEngine("mlx-community/whisper-large-v3-mlx")
stt.load()
result = stt.transcribe("audio.mp3")
print(result.text)

# Text-to-Speech
tts = TTSEngine("mlx-community/Kokoro-82M-bf16")
tts.load()
audio = tts.generate("Hello world", voice="af_heart")
tts.save(audio, "output.wav")

# Separación de voz
processor = AudioProcessor("mlx-community/sam-audio-large-fp16")
processor.load()
result = processor.separate("mixed_audio.mp3", description="speech")
processor.save(result.target, "voice_only.wav")
processor.save(result.residual, "background.wav")
```

### Funciones de Conveniencia

```python
from vllm_mlx.audio import transcribe_audio, generate_speech, separate_voice

# Transcripción rápida
result = transcribe_audio("audio.mp3")
print(result.text)

# TTS rápido
audio = generate_speech("Hello world", voice="af_heart")

# Separación de voz rápida
voice, background = separate_voice("mixed.mp3")
```

## Audio en el Chat

Incluir audio en mensajes de chat (se transcribe automáticamente):

```python
response = client.chat.completions.create(
    model="default",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Summarize this audio"},
            {"type": "audio_url", "audio_url": {"url": "file://meeting.mp3"}}
        ]
    }]
)
```

## Benchmarks

Probado en Apple M2 Max (32GB).

### Benchmarks de TTS (Kokoro-82M-bf16)

| Longitud del texto | Duración del audio | Tiempo de generación | RTF | Chars/seg |
|--------------------|--------------------|----------------------|-----|-----------|
| 25 chars | 1.95s | 0.43s | 4.6x | 58.5 |
| 88 chars | 6.00s | 0.32s | 18.6x | 272.4 |
| 117 chars | 7.92s | 0.27s | 29.0x | 427.4 |

**Resumen:**
- Tiempo de carga del modelo: ~1.0s
- RTF promedio: **17.4x** (17 veces más rápido que en tiempo real)
- Chars/seg promedio: **252.8**

### Benchmarks de STT

| Modelo | Tiempo de carga | Transcripción (audio de 6s) | RTF |
|--------|-----------------|------------------------------|-----|
| whisper-small | 0.25s | 0.20s | 30.2x |
| whisper-medium | 18.1s | 0.38s | 15.5x |
| whisper-large-v3 | ~30s | ~0.6s | ~10x |
| parakeet | ~0.5s | ~0.15s | ~40x |

**Notas:**
- RTF (Real-Time Factor) indica cuántas veces más rápido que en tiempo real es el procesamiento
- La primera carga incluye la descarga del modelo desde HuggingFace
- Las cargas siguientes usan los modelos en caché

### Recomendaciones por Caso de Uso

| Caso de uso | Modelo recomendado | Motivo |
|-------------|-------------------|--------|
| STT en inglés rápido | `parakeet` | RTF de 40x, bajo consumo de memoria |
| STT multilingüe | `whisper-large-v3` | 99+ idiomas |
| STT de baja latencia | `whisper-small` | RTF de 30x, carga rápida |
| TTS general | `kokoro` | RTF de 17x, buena calidad |
| TTS con poca memoria | `kokoro-4bit` | Cuantizado a 4 bits |

## Consejos de Rendimiento

1. **Usa Parakeet para inglés**: 40x más rápido que en tiempo real
2. **Usa modelos de 4 bits** para menor uso de memoria
3. **Usa SAM-Audio small** para una separación de voz más rápida
4. **Guarda los modelos en caché**: los motores se cargan de forma diferida y quedan en caché
5. **Descarga los modelos previamente** para evitar la latencia en la primera ejecución

## Solución de Problemas

### mlx-audio no está instalado
```
pip install mlx-audio>=0.2.9
```

### La descarga del modelo es lenta
Los modelos se descargan desde HuggingFace en el primer uso. Usa `huggingface-cli download` para descargarlos previamente:
```bash
huggingface-cli download mlx-community/whisper-large-v3-mlx
huggingface-cli download mlx-community/Kokoro-82M-bf16
```

### Sin memoria suficiente
Usa modelos más pequeños o versiones cuantizadas a 4 bits:
- `whisper-small-mlx` en lugar de `whisper-large-v3-mlx`
- `Kokoro-82M-4bit` en lugar de `Kokoro-82M-bf16`
- `sam-audio-small` en lugar de `sam-audio-large`

### Error multilingüe de Kokoro (mlx-audio 0.2.9)

Si obtienes `ValueError: too many values to unpack` al usar idiomas distintos al inglés (español, chino, japonés, etc.) con Kokoro, aplica esta corrección:

```python
# Corrección para mlx_audio/tts/models/kokoro/pipeline.py línea 443
# Cambia:
#     ps, _ = self.g2p(chunk)
# Por:
g2p_result = self.g2p(chunk)
ps = g2p_result[0] if isinstance(g2p_result, tuple) else g2p_result
```

**Corrección en una sola línea:**
```bash
python -c "
import os
path = os.path.join(os.path.dirname(__import__('mlx_audio').__file__), 'tts/models/kokoro/pipeline.py')
with open(path, 'r') as f: content = f.read()
old = '                    ps, _ = self.g2p(chunk)'
new = '''                    # Fix: handle both tuple (en) and string (zh/ja/es) returns from g2p
                    g2p_result = self.g2p(chunk)
                    ps = g2p_result[0] if isinstance(g2p_result, tuple) else g2p_result'''
if old in content:
    with open(path, 'w') as f: f.write(content.replace(old, new))
    print('Fix applied!')
"
```

Este error ocurre porque el g2p para inglés devuelve una tupla `(phonemes, tokens)` mientras que otros idiomas devuelven solo una cadena de texto.
