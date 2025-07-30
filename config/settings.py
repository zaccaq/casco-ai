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

# Configurazione Audio
MICROPHONE_INDEX = None  # None = microfono di default
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# Configurazione Speech Recognition
SPEECH_TIMEOUT = 1  # Secondi di silenzio prima di processare
SPEECH_PHRASE_TIMEOUT = 5  # Timeout massimo per una frase
MINIMUM_AUDIO_LENGTH = 1.0  # Secondi minimi di audio per processare

# Configurazione Text-to-Speech
TTS_RATE = 150  # Velocità della voce (parole per minuto)
TTS_VOLUME = 0.8  # Volume (0.0 - 1.0)
TTS_VOICE = 0  # Indice voce (0 = prima voce disponibile)

# Parole di attivazione
WAKE_WORDS = ["jarvis", "assistente", "casco", "computer"]

# Configurazione generale
DEBUG = True
AUTO_DOWNLOAD_MODELS = True  # Scarica automaticamente modelli se mancanti