import whisper
import pyttsx3
import threading
import time
import numpy as np
import pyaudio
import wave
import io
import tempfile
import os
from collections import deque
from config.settings import (
    MICROPHONE_INDEX, SPEECH_TIMEOUT, SPEECH_PHRASE_TIMEOUT,
    TTS_RATE, TTS_VOLUME, TTS_VOICE, WAKE_WORDS, DEBUG,
    WHISPER_MODEL, WHISPER_LANGUAGE, MINIMUM_AUDIO_LENGTH,
    SAMPLE_RATE, CHUNK_SIZE
)


class ImprovedWhisperSpeechHandler:
    def __init__(self):
        """Inizializza il gestore per speech-to-text con Whisper e text-to-speech"""

        # Inizializza Whisper
        if DEBUG:
            print(f"[WHISPER] Caricando modello {WHISPER_MODEL}...")

        try:
            self.whisper_model = whisper.load_model(WHISPER_MODEL)
            if DEBUG:
                print(f"[WHISPER] Modello {WHISPER_MODEL} caricato con successo")
        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore caricamento modello: {e}")
            raise Exception(f"Impossibile caricare Whisper: {e}")

        # Inizializza PyAudio per registrazione
        self.audio = pyaudio.PyAudio()
        self.microphone_index = self._get_best_microphone()

        # Inizializza Text-to-Speech
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', TTS_RATE)
        self.tts_engine.setProperty('volume', TTS_VOLUME)

        # Configura voce italiana se disponibile
        self._setup_italian_voice()

        # Stato del sistema
        self.is_listening = False
        self.is_speaking = False
        self.is_recording = False
        self.is_monitoring = False

        # Nuovo: Sistema ascolto intelligente
        self.voice_detected = False
        self.waiting_for_command = False
        self.silence_threshold = 300  # Soglia per rilevare voce (più sensibile)
        self.voice_chunks_needed = 3  # Chunks consecutivi per confermare voce
        self.silence_chunks_max = 15  # Chunks silenzio per fermare registrazione

        # Callbacks per sistema principale
        self.wake_word_callback = None
        self.command_callback = None

        # Buffer per registrazione
        self.audio_buffer = deque(maxlen=int(SAMPLE_RATE * 10))  # 10 secondi max

        if DEBUG:
            print("[WHISPER] ImprovedWhisperSpeechHandler inizializzato")
            print(f"[WHISPER] Microfono selezionato: {self.microphone_index}")
            self._list_audio_devices()

    def _get_best_microphone(self):
        """Trova il microfono migliore disponibile"""
        if MICROPHONE_INDEX is not None:
            if DEBUG:
                print(f"[WHISPER] Uso microfono configurato: {MICROPHONE_INDEX}")
            return MICROPHONE_INDEX

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

        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
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
                    print(f"[WHISPER] Mic {i}: {info['name']} - Score: {score}")

                if score > best_score:
                    best_score = score
                    best_mic = i

            except Exception as e:
                continue

        if best_mic is not None:
            if DEBUG:
                print(f"[WHISPER] Microfono auto-selezionato: {best_mic}")
            return best_mic
        else:
            if DEBUG:
                print("[WHISPER] Uso microfono di default")
            return None

    def _setup_italian_voice(self):
        """Configura voce italiana se disponibile"""
        try:
            voices = self.tts_engine.getProperty('voices')
            italian_voice = None

            # Cerca voce italiana
            for voice in voices:
                voice_name = voice.name.lower() if voice.name else ""
                voice_id = voice.id.lower() if voice.id else ""

                if ('italian' in voice_name or 'italia' in voice_name or
                        'it' in voice_id or 'ita' in voice_id):
                    italian_voice = voice
                    break

            if italian_voice:
                self.tts_engine.setProperty('voice', italian_voice.id)
                if DEBUG:
                    print(f"[TTS] Voce italiana configurata: {italian_voice.name}")
            else:
                # Usa la prima voce disponibile
                if voices and len(voices) > TTS_VOICE:
                    self.tts_engine.setProperty('voice', voices[TTS_VOICE].id)
                    if DEBUG:
                        print(f"[TTS] Voce configurata: {voices[TTS_VOICE].name}")

        except Exception as e:
            if DEBUG:
                print(f"[TTS] Errore configurazione voce: {e}")

    def _list_audio_devices(self):
        """Lista tutti i dispositivi audio disponibili"""
        if not DEBUG:
            return

        print("\n[WHISPER] Dispositivi audio disponibili:")
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    selected = " ← SELEZIONATO" if i == self.microphone_index else ""
                    print(f"  🎤 {i}: {info['name']} - Canali: {info['maxInputChannels']}{selected}")
            except:
                pass

    def start_intelligent_monitoring(self):
        """Avvia monitoraggio vocale continuo e intelligente"""
        if self.is_monitoring:
            return

        self.is_monitoring = True

        def monitor_voice():
            try:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    input_device_index=self.microphone_index,
                    frames_per_buffer=CHUNK_SIZE
                )

                if DEBUG:
                    print("[WHISPER] 🎧 Monitoraggio vocale intelligente avviato")

                silence_chunks = 0
                voice_chunks = 0
                audio_frames = []
                recording_voice = False

                while self.is_monitoring and not self.is_speaking:
                    try:
                        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        audio_chunk = np.frombuffer(data, dtype=np.int16)
                        volume = np.sqrt(np.mean(audio_chunk ** 2))

                        # Rileva se c'è voce
                        if volume > self.silence_threshold:
                            silence_chunks = 0
                            voice_chunks += 1

                            # Inizia registrazione quando rileva voce consistente
                            if not recording_voice and voice_chunks >= self.voice_chunks_needed:
                                recording_voice = True
                                audio_frames = []  # Reset buffer
                                if DEBUG:
                                    print("[WHISPER] 🎤 Voce rilevata, registrazione avviata...")

                            # Se stiamo registrando, aggiungi frame
                            if recording_voice:
                                audio_frames.append(data)

                        else:
                            # Silenzio rilevato
                            voice_chunks = max(0, voice_chunks - 1)  # Decremento graduale

                            if recording_voice:
                                silence_chunks += 1
                                # Continua a registrare per un po' in caso di pause
                                if silence_chunks < self.silence_chunks_max:
                                    audio_frames.append(data)
                                else:
                                    # Fine registrazione - processa audio
                                    if len(audio_frames) > 0:
                                        self._process_voice_buffer(audio_frames)

                                    # Reset stato
                                    audio_frames = []
                                    recording_voice = False
                                    silence_chunks = 0
                                    voice_chunks = 0

                    except Exception as e:
                        if DEBUG:
                            print(f"[WHISPER] Errore chunk audio: {e}")
                        continue

                stream.stop_stream()
                stream.close()

                if DEBUG:
                    print("[WHISPER] Monitoraggio vocale fermato")

            except Exception as e:
                if DEBUG:
                    print(f"[WHISPER] Errore monitoraggio: {e}")
            finally:
                self.is_monitoring = False

        self.monitor_thread = threading.Thread(target=monitor_voice, daemon=True)
        self.monitor_thread.start()

    def _process_voice_buffer(self, audio_frames):
        """Processa buffer audio quando rileva fine parlato"""
        try:
            if not audio_frames:
                return

            # Converti in numpy array
            audio_data = np.frombuffer(b''.join(audio_frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0

            duration = len(audio_data) / SAMPLE_RATE
            if duration < 0.5:  # Troppo breve, probabilmente rumore
                if DEBUG:
                    print(f"[WHISPER] Audio troppo breve ({duration:.1f}s), ignorato")
                return

            if DEBUG:
                print(f"[WHISPER] 🤖 Processando audio ({duration:.1f}s)...")

            # Preprocessing audio per migliorare riconoscimento
            audio_data = self._preprocess_audio(audio_data)

            # Trascrivi con Whisper
            result = self.whisper_model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                fp16=False,
                verbose=False,
                no_speech_threshold=0.5,  # Più permissivo
                logprob_threshold=-1.0,  # Filtro per risultati incerti
                condition_on_previous_text=False  # Non condizionare su testo precedente
            )

            text = result["text"].strip()
            if not text or len(text) < 2:
                if DEBUG:
                    print("[WHISPER] Testo troppo breve o vuoto, ignorato")
                return

            if DEBUG:
                print(f"[WHISPER] 📝 Trascrizione: '{text}'")

            # Controlla wake words
            if not self.waiting_for_command:
                for wake_word in WAKE_WORDS:
                    if wake_word.lower() in text.lower():
                        if DEBUG:
                            print(f"[WHISPER] 🎯 Wake word '{wake_word}' rilevata!")
                        self._notify_wake_word_detected(text)
                        return
            else:
                # Siamo in modalità comando - processa come comando
                if DEBUG:
                    print(f"[WHISPER] 📋 Comando ricevuto: '{text}'")
                self._notify_command_received(text)

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore processamento buffer: {e}")

    def _preprocess_audio(self, audio_data):
        """Preprocessing audio per migliorare riconoscimento"""
        try:
            # Normalizza volume
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 0.8

            # Applica filtro passa-alto per rimuovere rumori bassi
            try:
                from scipy import signal
                b, a = signal.butter(3, 300, 'high', fs=SAMPLE_RATE)
                audio_data = signal.filtfilt(b, a, audio_data)
            except ImportError:
                pass  # Scipy non disponibile, salta filtro

            return audio_data

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore preprocessing: {e}")
            return audio_data

    def _notify_wake_word_detected(self, text):
        """Notifica rilevazione wake word al sistema principale"""
        if self.wake_word_callback:
            self.wake_word_callback(text)

    def _notify_command_received(self, text):
        """Notifica comando ricevuto al sistema principale"""
        if self.command_callback:
            self.command_callback(text)
        self.waiting_for_command = False

    def wait_for_command(self, timeout=10):
        """Attiva modalità ascolto comando dopo wake word"""
        self.waiting_for_command = True
        if DEBUG:
            print("[WHISPER] 🎤 Modalità comando attivata...")

        # Auto-reset dopo timeout
        def reset_command_mode():
            time.sleep(timeout)
            if self.waiting_for_command:
                self.waiting_for_command = False
                if DEBUG:
                    print("[WHISPER] Timeout comando - ritorno a modalità wake word")

        threading.Thread(target=reset_command_mode, daemon=True).start()

    def speak(self, text: str):
        """Pronuncia un testo usando text-to-speech"""
        try:
            if DEBUG:
                print(f"[TTS] Pronunciando: '{text}'")

            self.is_speaking = True

            # Avvia TTS in un thread separato per non bloccare
            def speak_thread():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    if DEBUG:
                        print(f"[TTS] Errore riproduzione: {e}")
                finally:
                    self.is_speaking = False

            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()

            # Aspetta che finisca di parlare
            while self.is_speaking:
                time.sleep(0.1)

        except Exception as e:
            if DEBUG:
                print(f"[TTS] Errore TTS: {e}")
            self.is_speaking = False

    def listen_for_wake_word(self) -> bool:
        """Ascolta per parole di attivazione - DEPRECATO, usa monitoraggio intelligente"""
        if DEBUG:
            print("[WHISPER] ⚠️ Metodo deprecato - usa start_intelligent_monitoring()")
        return False

    def listen_for_command(self) -> str:
        """Ascolta un comando vocale completo - DEPRECATO"""
        if DEBUG:
            print("[WHISPER] ⚠️ Metodo deprecato - usa wait_for_command() con callback")
        return ""

    def _record_audio_manual(self, duration=5, listen_for_silence=True):
        """Registra audio manualmente per test o comandi forzati"""
        try:
            if DEBUG:
                print(f"[WHISPER] Registrazione manuale per {duration}s...")

            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.microphone_index,
                frames_per_buffer=CHUNK_SIZE
            )

            frames = []
            silent_chunks = 0
            max_silent_chunks = int(SPEECH_TIMEOUT * SAMPLE_RATE / CHUNK_SIZE)
            max_frames = int(duration * SAMPLE_RATE / CHUNK_SIZE)

            self.is_recording = True

            for i in range(max_frames):
                if not self.is_recording:
                    break

                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                frames.append(data)

                # Rilevazione silenzio per stop automatico
                if listen_for_silence and len(frames) > 10:
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    volume = np.sqrt(np.mean(audio_chunk ** 2))

                    if volume < self.silence_threshold:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0

                    # Se silenzio troppo lungo, ferma
                    if silent_chunks > max_silent_chunks and len(frames) > 20:
                        if DEBUG:
                            print("[WHISPER] Silenzio rilevato, stop registrazione")
                        break

            stream.stop_stream()
            stream.close()
            self.is_recording = False

            if not frames:
                return None

            # Converti in numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0

            # Controlla durata minima
            duration_seconds = len(audio_data) / SAMPLE_RATE
            if duration_seconds < 0.5:
                if DEBUG:
                    print(f"[WHISPER] Audio troppo breve ({duration_seconds:.1f}s), scartato")
                return None

            if DEBUG:
                print(f"[WHISPER] Audio registrato: {duration_seconds:.1f}s")

            return audio_data

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore registrazione: {e}")
            self.is_recording = False
            return None

    def manual_voice_command(self):
        """Registra e processa un comando vocale manualmente (per SPAZIO)"""
        try:
            if DEBUG:
                print("[WHISPER] 🎤 Comando vocale manuale...")

            # Registra audio
            audio_data = self._record_audio_manual(duration=SPEECH_PHRASE_TIMEOUT)

            if audio_data is None:
                return ""

            # Preprocessing
            audio_data = self._preprocess_audio(audio_data)

            # Trascrivi
            result = self.whisper_model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                fp16=False,
                verbose=False
            )

            command = result["text"].strip()

            if DEBUG:
                print(f"[WHISPER] Comando manuale: '{command}'")

            return command

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore comando manuale: {e}")
            return ""

    def is_busy(self) -> bool:
        """Controlla se il sistema è occupato"""
        return self.is_listening or self.is_speaking or self.is_recording

    def stop_monitoring(self):
        """Ferma il monitoraggio vocale"""
        self.is_monitoring = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)

    def stop_all(self):
        """Ferma tutte le operazioni audio"""
        try:
            self.is_recording = False
            self.is_listening = False
            self.is_monitoring = False
            self.waiting_for_command = False

            # Ferma TTS
            try:
                self.tts_engine.stop()
            except:
                pass
            self.is_speaking = False

            if DEBUG:
                print("[WHISPER] Tutte le operazioni audio fermate")
        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore stop: {e}")

    def test_microphone(self, duration=3):
        """Testa il microfono registrando e trascrivendo"""
        try:
            print(f"🎤 Test microfono per {duration} secondi...")
            print("   📢 Parla ora!")

            # Ferma temporaneamente il monitoraggio
            was_monitoring = self.is_monitoring
            if was_monitoring:
                self.stop_monitoring()
                time.sleep(0.5)

            audio_data = self._record_audio_manual(duration=duration, listen_for_silence=False)

            if audio_data is None:
                print("❌ Nessun audio registrato")
                return

            print("🤖 Trascrizione in corso...")

            # Preprocessing
            audio_data = self._preprocess_audio(audio_data)

            result = self.whisper_model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                fp16=False
            )

            transcription = result["text"]
            print(f"📝 Trascrizione: '{transcription}'")

            if transcription.strip():
                print("✅ Microfono funziona correttamente!")

                # Test TTS
                print("🔊 Test sintesi vocale...")
                self.speak("Test completato con successo!")
            else:
                print("⚠️  Nessun parlato rilevato")

            # Riavvia monitoraggio se era attivo
            if was_monitoring:
                time.sleep(1)
                self.start_intelligent_monitoring()

        except Exception as e:
            print(f"❌ Errore test microfono: {e}")

    def get_microphone_info(self):
        """Restituisce informazioni sul microfono in uso"""
        try:
            if self.microphone_index is not None:
                info = self.audio.get_device_info_by_index(self.microphone_index)
                return {
                    'index': self.microphone_index,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': info['defaultSampleRate']
                }
            else:
                default_info = self.audio.get_default_input_device_info()
                return {
                    'index': None,
                    'name': default_info['name'],
                    'channels': default_info['maxInputChannels'],
                    'sample_rate': default_info['defaultSampleRate']
                }
        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore info microfono: {e}")
            return None

    def cleanup(self):
        """Pulisce le risorse"""
        try:
            self.stop_all()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            if DEBUG:
                print("[WHISPER] Risorse pulite")
        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore cleanup: {e}")

    def __del__(self):
        """Destructor per pulizia automatica"""
        self.cleanup()


# Alias per compatibilità
WhisperSpeechHandler = ImprovedWhisperSpeechHandler