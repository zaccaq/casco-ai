import pyaudio
import wave
import threading
import time
from config.settings import SAMPLE_RATE, CHUNK_SIZE, DEBUG


class AudioManager:
    def __init__(self):
        """Inizializza il gestore audio per controllo avanzato"""
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.is_playing = False
        self.recording_thread = None
        self.playback_thread = None

        # Buffer per registrazione
        self.audio_buffer = []

        if DEBUG:
            print("[AUDIO] AudioManager inizializzato")
            self._list_audio_devices()

    def _list_audio_devices(self):
        """Lista tutti i dispositivi audio disponibili"""
        if not DEBUG:
            return

        print("\n[AUDIO] Dispositivi audio disponibili:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} - Canali: {info['maxInputChannels']}/{info['maxOutputChannels']}")

    def get_default_microphone(self):
        """Restituisce informazioni sul microfono di default"""
        try:
            default_mic = self.audio.get_default_input_device_info()
            if DEBUG:
                print(f"[AUDIO] Microfono default: {default_mic['name']}")
            return default_mic
        except Exception as e:
            if DEBUG:
                print(f"[AUDIO] Errore nel trovare microfono default: {e}")
            return None

    def test_microphone(self, duration=3):
        """
        Testa il microfono registrando per alcuni secondi

        Args:
            duration (int): Durata del test in secondi
        """
        try:
            if DEBUG:
                print(f"[AUDIO] Test microfono per {duration} secondi...")

            # Configurazione stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )

            frames = []
            for i in range(0, int(SAMPLE_RATE / CHUNK_SIZE * duration)):
                data = stream.read(CHUNK_SIZE)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            # Salva file di test
            self._save_wav_file("test_microphone.wav", frames)

            if DEBUG:
                print("[AUDIO] Test microfono completato - file salvato come test_microphone.wav")

        except Exception as e:
            if DEBUG:
                print(f"[AUDIO] Errore test microfono: {e}")

    def _save_wav_file(self, filename, frames):
        """Salva frame audio in file WAV"""
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
        except Exception as e:
            if DEBUG:
                print(f"[AUDIO] Errore salvataggio WAV: {e}")

    def start_continuous_recording(self):
        """Avvia registrazione continua in background"""
        if self.is_recording:
            return

        self.is_recording = True
        self.audio_buffer = []

        def record_audio():
            try:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE
                )

                if DEBUG:
                    print("[AUDIO] Registrazione continua avviata")

                while self.is_recording:
                    data = stream.read(CHUNK_SIZE)
                    self.audio_buffer.append(data)

                    # Mantieni solo gli ultimi 10 secondi di audio
                    max_frames = int(SAMPLE_RATE / CHUNK_SIZE * 10)
                    if len(self.audio_buffer) > max_frames:
                        self.audio_buffer.pop(0)

                stream.stop_stream()
                stream.close()

                if DEBUG:
                    print("[AUDIO] Registrazione continua fermata")

            except Exception as e:
                if DEBUG:
                    print(f"[AUDIO] Errore registrazione continua: {e}")
                self.is_recording = False

        self.recording_thread = threading.Thread(target=record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_continuous_recording(self):
        """Ferma la registrazione continua"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2)

    def get_audio_level(self):
        """
        Restituisce il livello audio corrente (per visualizzazione)

        Returns:
            float: Livello audio normalizzato (0.0 - 1.0)
        """
        if not self.audio_buffer:
            return 0.0

        try:
            # Prendi l'ultimo chunk
            import numpy as np
            last_chunk = np.frombuffer(self.audio_buffer[-1], dtype=np.int16)

            # Calcola RMS (Root Mean Square)
            rms = np.sqrt(np.mean(last_chunk ** 2))

            # Normalizza (valore tipico massimo ~3000)
            normalized = min(rms / 3000.0, 1.0)

            return normalized

        except Exception as e:
            if DEBUG:
                print(f"[AUDIO] Errore calcolo livello audio: {e}")
            return 0.0

    def play_notification_sound(self, frequency=800, duration=0.2):
        """
        Riproduce un suono di notifica

        Args:
            frequency (int): Frequenza del tono in Hz
            duration (float): Durata in secondi
        """

        def play_tone():
            try:
                import numpy as np

                # Genera onda sinusoidale
                sample_rate = 44100
                frames = int(duration * sample_rate)

                # Crea il tono
                tone = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))
                tone = (tone * 32767).astype(np.int16)

                # Riproduci
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True
                )

                stream.write(tone.tobytes())
                stream.stop_stream()
                stream.close()

            except Exception as e:
                if DEBUG:
                    print(f"[AUDIO] Errore riproduzione tono: {e}")

        if not self.is_playing:
            self.is_playing = True
            tone_thread = threading.Thread(target=play_tone)
            tone_thread.daemon = True
            tone_thread.start()

            # Reset flag dopo la durata
            def reset_flag():
                time.sleep(duration + 0.1)
                self.is_playing = False

            reset_thread = threading.Thread(target=reset_flag)
            reset_thread.daemon = True
            reset_thread.start()

    def cleanup(self):
        """Pulisce le risorse audio"""
        try:
            self.stop_continuous_recording()
            self.audio.terminate()
            if DEBUG:
                print("[AUDIO] Risorse audio rilasciate")
        except Exception as e:
            if DEBUG:
                print(f"[AUDIO] Errore cleanup: {e}")

    def __del__(self):
        """Destructor per pulizia automatica"""
        self.cleanup()