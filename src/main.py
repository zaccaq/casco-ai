#!/usr/bin/env python3
"""
Jarvis Helmet - Assistente Personale AI
Main entry point per il sistema casco intelligente
"""

import asyncio
import signal
import sys
import time
import keyboard
from datetime import datetime

from speech_handler import WhisperSpeechHandler
from claude_api import OllamaAssistant
from audio_manager import AudioManager
from config.settings import DEBUG, WAKE_WORDS


class JarvisHelmet:
    def __init__(self):
        """Inizializza il sistema Jarvis Helmet"""
        print("🤖 Inizializzando Jarvis Helmet...")

        try:
            # Inizializza componenti
            self.speech_handler = WhisperSpeechHandler()
            self.ai_assistant = OllamaAssistant()
            self.audio_manager = AudioManager()

            # Stato del sistema
            self.is_active = False
            self.is_running = True
            self.session_start = datetime.now()

            # Statistiche
            self.commands_processed = 0
            self.wake_words_detected = 0

            print("✅ Jarvis Helmet inizializzato con successo!")

        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            sys.exit(1)

    async def start_system(self):
        """Avvia il sistema principale di Jarvis"""
        print("\n🚀 Avvio Jarvis Helmet...")
        print("📝 Comandi disponibili:")
        print("   - Premi SPAZIO per attivazione manuale")
        print("   - Premi ESC per uscire")
        print("   - Premi 's' per statistiche")
        print("   - Premi 't' per test microfono")
        print("   - Premi 'm' per cambiare modello AI")
        print(f"   - Parole di attivazione: {', '.join(WAKE_WORDS)}")
        print(f"   - Modello AI: {self.ai_assistant.model}")
        print("\n🎧 Sistema in ascolto...\n")

        # Avvia registrazione continua per monitoraggio
        self.audio_manager.start_continuous_recording()

        # Suono di avvio
        self.audio_manager.play_notification_sound(frequency=1000, duration=0.3)

        try:
            while self.is_running:
                await self._main_loop()
                await asyncio.sleep(0.1)  # Piccola pausa per non sovraccaricare CPU

        except KeyboardInterrupt:
            print("\n🛑 Arresto sistema richiesto...")
        finally:
            await self._shutdown()

    async def _main_loop(self):
        """Loop principale del sistema"""
        try:
            # Controlla comandi da tastiera
            await self._handle_keyboard_input()

            # Se non stiamo già processando, ascolta per wake words
            if not self.speech_handler.is_busy():
                await self._listen_for_activation()

        except Exception as e:
            if DEBUG:
                print(f"[MAIN] Errore main loop: {e}")

    async def _handle_keyboard_input(self):
        """Gestisce input da tastiera"""
        try:
            if keyboard.is_pressed('esc'):
                print("\n🛑 Uscita tramite ESC...")
                self.is_running = False
                return

            if keyboard.is_pressed('space'):
                print("\n🎤 Attivazione manuale...")
                await self._process_voice_command()
                time.sleep(0.5)  # Evita attivazioni multiple

            if keyboard.is_pressed('s'):
                self._show_statistics()
                time.sleep(0.5)

            if keyboard.is_pressed('t'):
                print("\n🔊 Test microfono...")
                self.speech_handler.test_microphone(duration=3)
                time.sleep(0.5)

            if keyboard.is_pressed('m'):
                self._change_ai_model()
                time.sleep(0.5)

        except Exception as e:
            if DEBUG:
                print(f"[MAIN] Errore gestione tastiera: {e}")

    async def _listen_for_activation(self):
        """Ascolta per parole di attivazione"""
        try:
            # Controlla livello audio per debug
            if DEBUG:
                audio_level = self.audio_manager.get_audio_level()
                if audio_level > 0.1:  # Solo se c'è audio significativo
                    print(f"[AUDIO] Livello: {'█' * int(audio_level * 20)}")

            # Ascolta per wake word
            if self.speech_handler.listen_for_wake_word():
                self.wake_words_detected += 1
                print("🎯 Wake word rilevata!")

                # Suono di conferma
                self.audio_manager.play_notification_sound(frequency=1200, duration=0.2)

                # Processa comando
                await self._process_voice_command()

        except Exception as e:
            if DEBUG:
                print(f"[MAIN] Errore ascolto attivazione: {e}")

    async def _process_voice_command(self):
        """Processa un comando vocale completo"""
        try:
            print("🎙️  In ascolto per comando...")

            # Ascolta il comando
            command = self.speech_handler.listen_for_command()

            if not command.strip():
                print("❌ Nessun comando rilevato")
                self.speech_handler.speak("Non ho sentito nulla. Riprova.")
                return

            print(f"📝 Comando: '{command}'")

            # Processa con Ollama
            print("🤖 Elaborando risposta...")
            response = await self.ai_assistant.process_command(command)

            if response:
                print(f"💬 Risposta: {response}")

                # Pronuncia la risposta
                self.speech_handler.speak(response)

                self.commands_processed += 1

                # Suono di completamento
                self.audio_manager.play_notification_sound(frequency=800, duration=0.2)
            else:
                print("❌ Errore nell'elaborazione del comando")
                self.speech_handler.speak("Mi dispiace, non sono riuscito a elaborare la richiesta.")

        except Exception as e:
            error_msg = f"Errore nel processare il comando: {e}"
            print(f"❌ {error_msg}")
            if DEBUG:
                print(f"[MAIN] Dettagli errore: {e}")

            self.speech_handler.speak("Si è verificato un errore tecnico.")

    def _show_statistics(self):
        """Mostra statistiche del sistema"""
        uptime = datetime.now() - self.session_start

        print("\n📊 STATISTICHE JARVIS HELMET")
        print("=" * 40)
        print(f"⏱️  Tempo attivo: {uptime}")
        print(f"🎯 Wake words rilevate: {self.wake_words_detected}")
        print(f"📝 Comandi processati: {self.commands_processed}")
        print(f"🔊 Livello audio corrente: {self.audio_manager.get_audio_level():.2%}")
        print(f"🤖 Modello AI: {self.ai_assistant.model}")
        print(
            f"🎤 Microfono: {self.audio_manager.get_default_microphone()['name'] if self.audio_manager.get_default_microphone() else 'N/A'}")
        print("=" * 40 + "\n")

    def _change_ai_model(self):
        """Permette di cambiare il modello AI"""
        try:
            print("\n🤖 MODELLI AI DISPONIBILI")
            print("=" * 30)

            available_models = self.ai_assistant.list_available_models()
            if not available_models:
                print("❌ Nessun modello trovato in Ollama")
                print("💡 Scarica un modello con: ollama pull llama3.2:1b")
                return

            for i, model in enumerate(available_models):
                current = " (ATTUALE)" if model == self.ai_assistant.model else ""
                print(f"  {i + 1}. {model}{current}")

            print("\n📝 Modelli consigliati per il casco:")
            print("   - llama3.2:1b (veloce, 1.3GB)")
            print("   - llama3.2:3b (bilanciato, 2GB)")
            print("   - qwen2.5:1.5b (molto veloce, 934MB)")

            # Per ora manteniamo il modello corrente
            # In futuro si potrebbe aggiungere input utente qui
            print(f"\n✅ Modello attuale: {self.ai_assistant.model}")

        except Exception as e:
            print(f"❌ Errore cambio modello: {e}")

    async def _shutdown(self):
        """Arresta il sistema in modo pulito"""
        print("🔄 Arresto sistema in corso...")

        try:
            # Ferma tutti i componenti
            self.speech_handler.stop_all()
            self.audio_manager.cleanup()

            # Mostra statistiche finali
            self._show_statistics()

            print("✅ Jarvis Helmet arrestato correttamente")

        except Exception as e:
            print(f"❌ Errore durante arresto: {e}")


def setup_signal_handlers(jarvis):
    """Configura gestori per segnali di sistema"""

    def signal_handler(signum, frame):
        print(f"\n🛑 Ricevuto segnale {signum}")
        jarvis.is_running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Funzione principale"""
    print("🤖 JARVIS HELMET - Assistente Personale AI")
    print("=" * 50)

    try:
        # Crea istanza Jarvis
        jarvis = JarvisHelmet()

        # Configura gestori segnali
        setup_signal_handlers(jarvis)

        # Avvia sistema
        await jarvis.start_system()

    except Exception as e:
        print(f"❌ Errore critico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Avvia il sistema con asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Arrivederci!")
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        sys.exit(1)