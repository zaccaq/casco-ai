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
from config.settings import (
    MICROPHONE_INDEX, SPEECH_TIMEOUT, SPEECH_PHRASE_TIMEOUT,
    TTS_RATE, TTS_VOLUME, TTS_VOICE, WAKE_WORDS, DEBUG,
    WHISPER_MODEL, WHISPER_LANGUAGE, MINIMUM_AUDIO_LENGTH,
    SAMPLE_RATE, CHUNK_SIZE
)


class WhisperSpeechHandler:
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
        self.microphone_index = MICROPHONE_INDEX

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

        # Buffer per registrazione
        self.audio_buffer = []

        if DEBUG:
            print("[WHISPER] WhisperSpeechHandler inizializzato")
            self._list_audio_devices()

    def _setup_italian_voice(self):
        """Configura voce italiana se disponibile"""
        try:
            voices = self.tts_engine.getProperty('voices')
            italian_voice = None

            # Cerca voce italiana
            for voice in voices:
                if 'italian' in voice.name.lower() or 'it' in voice.id.lower():
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

        print("\n[AUDIO] Dispositivi audio disponibili:")
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  🎤 {i}: {info['name']} - Canali: {info['maxInputChannels']}")
            except:
                pass

    def _record_audio(self, duration=5, listen_for_silence=True):
        """
        Registra audio dal microfono

        Args:
            duration (int): Durata massima registrazione
            listen_for_silence (bool): Ferma alla rilevazione di silenzio

        Returns:
            numpy.array: Array audio o None se errore
        """
        try:
            if DEBUG:
                print(f"[WHISPER] Registrando audio per max {duration}s...")

            # Configura stream audio
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
                if listen_for_silence and len(frames) > 10:  # Aspetta almeno qualche frame
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    volume = np.sqrt(np.mean(audio_chunk ** 2))

                    if volume < 300:  # Soglia silenzio
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
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalizza

            # Controlla durata minima
            duration_seconds = len(audio_data) / SAMPLE_RATE
            if duration_seconds < MINIMUM_AUDIO_LENGTH:
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

    def listen_for_wake_word(self) -> bool:
        """
        Ascolta per parole di attivazione usando Whisper

        Returns:
            bool: True se rilevata parola di attivazione
        """
        try:
            # Registra audio breve per wake word
            audio_data = self._record_audio(duration=3, listen_for_silence=True)

            if audio_data is None:
                return False

            # Trascrivi con Whisper
            result = self.whisper_model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                fp16=False,
                verbose=False
            )

            text = result["text"].lower().strip()

            if DEBUG and text:
                print(f"[WHISPER] Rilevato: '{text}'")

            # Controlla se contiene una wake word
            for wake_word in WAKE_WORDS:
                if wake_word in text:
                    if DEBUG:
                        print(f"[WHISPER] Wake word rilevata: {wake_word}")
                    return True

            return False

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore rilevamento wake word: {e}")
            return False

    def listen_for_command(self) -> str:
        """
        Ascolta un comando vocale completo usando Whisper

        Returns:
            str: Il testo del comando o stringa vuota se errore
        """
        try:
            if DEBUG:
                print("[WHISPER] In ascolto per comando...")

            self.is_listening = True

            # Registra audio per comando
            audio_data = self._record_audio(
                duration=SPEECH_PHRASE_TIMEOUT,
                listen_for_silence=True
            )

            if audio_data is None:
                self.is_listening = False
                return ""

            # Trascrivi con Whisper
            result = self.whisper_model.transcribe(
                audio_data,
                language=WHISPER_LANGUAGE,
                fp16=False,
                verbose=False
            )

            command = result["text"].strip()

            if DEBUG:
                print(f"[WHISPER] Comando riconosciuto: '{command}'")

            self.is_listening = False
            return command

        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore riconoscimento comando: {e}")
            self.is_listening = False
            return ""

    def speak(self, text: str):
        """
        Pronuncia un testo usando text-to-speech

        Args:
            text (str): Il testo da pronunciare
        """
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

            thread = threading.Thread(target=speak_thread)
            thread.daemon = True
            thread.start()

            # Aspetta che finisca di parlare
            while self.is_speaking:
                time.sleep(0.1)

        except Exception as e:
            if DEBUG:
                print(f"[TTS] Errore TTS: {e}")
            self.is_speaking = False

    def is_busy(self) -> bool:
        """
        Controlla se il sistema è occupato (parlando o ascoltando)

        Returns:
            bool: True se occupato
        """
        return self.is_listening or self.is_speaking or self.is_recording

    def stop_all(self):
        """Ferma tutte le operazioni audio"""
        try:
            self.is_recording = False
            self.is_listening = False

            # Ferma TTS
            self.tts_engine.stop()
            self.is_speaking = False

            if DEBUG:
                print("[WHISPER] Tutte le operazioni audio fermate")
        except Exception as e:
            if DEBUG:
                print(f"[WHISPER] Errore stop: {e}")

    def test_microphone(self, duration=3):
        """
        Testa il microfono registrando e trascrivendo

        Args:
            duration (int): Durata del test in secondi
        """
        try:
            print(f"🎤 Test microfono per {duration} secondi...")
            print("   Parla ora!")

            audio_data = self._record_audio(duration=duration, listen_for_silence=False)

            if audio_data is None:
                print("❌ Nessun audio registrato")
                return

            print("🤖 Trascrizione in corso...")
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

        except Exception as e:
            print(f"❌ Errore test microfono: {e}")

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