import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione Ollama
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')  # Modello leggero

# Configurazione Whisper
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
WHISPER_LANGUAGE = 'it'  # Italiano


# Configurazione Audio Migliorata
def get_microphone_index():
    """Ottieni indice microfono da configurazione o auto-selezione"""
    env_mic = os.getenv('MICROPHONE_INDEX')
    if env_mic is not None:
        try:
            return int(env_mic)
        except ValueError:
            pass
    return None  # Auto-selezione


MICROPHONE_INDEX = get_microphone_index()
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# Configurazione Speech Recognition Ottimizzata
SPEECH_TIMEOUT = 1.5  # Secondi di silenzio prima di processare (ridotto)
SPEECH_PHRASE_TIMEOUT = 8  # Timeout massimo per una frase (aumentato)
MINIMUM_AUDIO_LENGTH = 0.5  # Secondi minimi di audio per processare (ridotto)

# Configurazione Text-to-Speech
TTS_RATE = 180  # Velocità della voce (parole per minuto) - leggermente più veloce
TTS_VOLUME = 0.9  # Volume (0.0 - 1.0) - più alto
TTS_VOICE = 0  # Indice voce (0 = prima voce disponibile)

# Parole di attivazione (tutte lowercase)
WAKE_WORDS = ["jarvis", "assistente", "casco", "computer", "hey jarvis"]

# Configurazione Monitoraggio Vocale Intelligente
VOICE_DETECTION_THRESHOLD = 300  # Soglia volume per rilevare voce (più sensibile)
VOICE_CHUNKS_NEEDED = 3  # Chunks consecutivi per confermare voce
SILENCE_CHUNKS_MAX = 15  # Chunks silenzio prima di fermare registrazione
COMMAND_TIMEOUT = 10  # Secondi timeout per comando dopo wake word

# Configurazione generale
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
AUTO_DOWNLOAD_MODELS = True  # Scarica automaticamente modelli se mancanti

# Configurazione Performance
AUDIO_BUFFER_SIZE = 10  # Secondi di buffer audio
TRANSCRIPTION_THREADS = 1  # Thread per trascrizione (1 = sequenziale)

# Configurazione Filtri Audio
ENABLE_AUDIO_PREPROCESSING = True  # Abilita preprocessing audio
HIGH_PASS_FREQUENCY = 300  # Frequenza filtro passa-alto (Hz)
NOISE_REDUCTION_ENABLED = True  # Abilita riduzione rumore

# Configurazione WebSocket
WEBSOCKET_HOST = '0.0.0.0'
WEBSOCKET_PORT = 8765
WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 10

# Configurazione Server Mobile
MOBILE_SERVER_HOST = '0.0.0.0'
MOBILE_SERVER_PORT = 8766

# Configurazione Avanzata per Debug
SAVE_AUDIO_RECORDINGS = os.getenv('SAVE_AUDIO_RECORDINGS', 'False').lower() == 'true'
AUDIO_RECORDINGS_PATH = 'recordings'  # Cartella per salvare registrazioni

# Configurazione Sistema
MAX_CONSECUTIVE_ERRORS = 5  # Errori consecutivi prima di reset
ERROR_RECOVERY_DELAY = 2  # Secondi di attesa dopo errore

# Messaggi di Sistema
WAKE_CONFIRMATION_MESSAGES = [
    "Sì?", "Dimmi", "Ti ascolto", "Comando?", "Sono qui"
]

ERROR_MESSAGES = {
    'audio_error': "Problema con l'audio, riprova.",
    'ai_error': "Errore del sistema AI, riprova.",
    'network_error': "Problema di connessione, riprova.",
    'timeout_error': "Tempo scaduto, riprova.",
    'generic_error': "Si è verificato un errore, riprova."
}

SUCCESS_SOUNDS = {
    'wake_word': {'frequency': 1200, 'duration': 0.2},
    'command_complete': {'frequency': 800, 'duration': 0.2},
    'system_ready': {'frequency': 1000, 'duration': 0.3},
    'error': {'frequency': 400, 'duration': 0.5}
}


# Funzioni Helper
def get_best_microphone():
    """Trova il microfono migliore disponibile (funzione standalone)"""
    try:
        import pyaudio
        audio = pyaudio.PyAudio()

        # Priorità microfoni (dal migliore al peggiore)
        preferred_keywords = [
            "realtek",
            "microphone",
            "mic",
            "input"
        ]

        # Parole da evitare (dispositivi con latenza)
        avoid_keywords = [
            "bluetooth", "bt", "airpods", "wireless", "hands-free"
        ]

        best_mic = None
        best_score = -1

        for i in range(audio.get_device_count()):
            try:
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] == 0:
                    continue

                name = info['name'].lower()
                score = 0

                # Bonus per parole preferite
                for j, keyword in enumerate(preferred_keywords):
                    if keyword in name:
                        score += (len(preferred_keywords) - j) * 2
                        break

                # Bonus per canali stereo
                if info['maxInputChannels'] >= 2:
                    score += 3

                # Malus per dispositivi da evitare
                for keyword in avoid_keywords:
                    if keyword in name:
                        score -= 5
                        break

                if DEBUG:
                    print(f"[MIC] {i}: {info['name']} - Score: {score}")

                if score > best_score:
                    best_score = score
                    best_mic = i

            except:
                continue

        audio.terminate()

        if best_mic is not None:
            if DEBUG:
                print(f"[MIC] Microfono auto-selezionato: {best_mic}")
            return best_mic
        else:
            if DEBUG:
                print("[MIC] Uso microfono di default")
            return None

    except Exception as e:
        if DEBUG:
            print(f"[MIC] Errore selezione automatica: {e}")
        return None


def validate_settings():
    """Valida le impostazioni e mostra avvisi se necessario"""
    if DEBUG:
        print("[SETTINGS] Validazione configurazione...")

        # Controlla Ollama
        try:
            import requests
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code == 200:
                print("[SETTINGS] ✅ Ollama raggiungibile")
            else:
                print("[SETTINGS] ⚠️ Ollama non risponde correttamente")
        except:
            print("[SETTINGS] ❌ Ollama non raggiungibile")

        # Controlla microfono
        if MICROPHONE_INDEX is not None:
            print(f"[SETTINGS] ✅ Microfono configurato: {MICROPHONE_INDEX}")
        else:
            print("[SETTINGS] ⚠️ Microfono auto-selezione")

        # Controlla Whisper model
        if WHISPER_MODEL in ['tiny', 'base', 'small']:
            print(f"[SETTINGS] ✅ Modello Whisper ottimale: {WHISPER_MODEL}")
        elif WHISPER_MODEL in ['medium', 'large']:
            print(f"[SETTINGS] ⚠️ Modello Whisper pesante: {WHISPER_MODEL} (potrebbe essere lento)")

        print("[SETTINGS] Configurazione validata")


# Auto-validazione all'import se debug attivo
if DEBUG:
    validate_settings()

# Export delle configurazioni principali
__all__ = [
    'OLLAMA_HOST', 'OLLAMA_MODEL',
    'WHISPER_MODEL', 'WHISPER_LANGUAGE',
    'MICROPHONE_INDEX', 'SAMPLE_RATE', 'CHUNK_SIZE',
    'SPEECH_TIMEOUT', 'SPEECH_PHRASE_TIMEOUT', 'MINIMUM_AUDIO_LENGTH',
    'TTS_RATE', 'TTS_VOLUME', 'TTS_VOICE',
    'WAKE_WORDS', 'DEBUG',
    'VOICE_DETECTION_THRESHOLD', 'VOICE_CHUNKS_NEEDED', 'SILENCE_CHUNKS_MAX',
    'COMMAND_TIMEOUT', 'get_best_microphone'
]