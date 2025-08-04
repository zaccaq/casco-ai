#!/usr/bin/env python3
"""
Jarvis Helmet - Assistente Personale AI - VERSIONE MIGLIORATA
Main entry point per il sistema casco intelligente
"""

import asyncio
import signal
import sys
import time
import keyboard
from datetime import datetime

from speech_handler import ImprovedWhisperSpeechHandler
from claude_api import OllamaAssistant
from audio_manager import AudioManager
from websocket_server import start_websocket_server_thread
from mobile_server import start_mobile_app_server
from config.settings import DEBUG, WAKE_WORDS


class ImprovedJarvisHelmet:
    def __init__(self):
        """Inizializza il sistema Jarvis Helmet Migliorato"""
        print("🤖 Inizializzando Jarvis Helmet...")

        try:
            # Inizializza componenti
            self.speech_handler = ImprovedWhisperSpeechHandler()
            self.ai_assistant = OllamaAssistant()
            self.audio_manager = AudioManager()

            # Collega callback per speech handler
            self.speech_handler.wake_word_callback = self._on_wake_word_detected
            self.speech_handler.command_callback = self._on_command_received

            # Avvia server per app mobile
            self.mobile_server = start_mobile_app_server(port=8766)
            self.websocket_thread = start_websocket_server_thread(self, port=8765)

            # Stato del sistema
            self.is_active = False
            self.is_running = True
            self.session_start = datetime.now()

            # Statistiche
            self.commands_processed = 0
            self.wake_words_detected = 0

            print("✅ Jarvis Helmet inizializzato con successo!")

            if self.mobile_server:
                print("📱 App mobile disponibile:")
                print(f"   🌐 http://{self.mobile_server.get_local_ip()}:8766")
                print("   💡 Apri questo URL sul tuo smartphone!")

        except Exception as e:
            print(f"❌ Errore inizializzazione: {e}")
            sys.exit(1)

    async def start_system(self):
        """Avvia il sistema principale di Jarvis"""
        print("\n🚀 Avvio Jarvis Helmet...")
        print("📝 Comandi disponibili:")
        print("   - Parla normalmente, Jarvis ti ascolta sempre! 🎧")
        print("   - Premi SPAZIO per comando forzato")
        print("   - Premi ESC per uscire")
        print("   - Premi 's' per statistiche")
        print("   - Premi 't' per test microfono")
        print("   - Premi 'm' per cambiare modello AI")
        print("   - Premi 'w' per aprire app mobile")
        print(f"   - Parole di attivazione: {', '.join(WAKE_WORDS)}")
        print(f"   - Modello AI: {self.ai_assistant.model}")

        # Info microfono
        mic_info = self.speech_handler.get_microphone_info()
        if mic_info:
            print(f"   - Microfono: {mic_info['name']} (Indice: {mic_info['index']})")

        print("\n🎧 Sistema in ascolto continuo...\n")

        # Avvia monitoraggio vocale intelligente
        self.speech_handler.start_intelligent_monitoring()

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
                await self._process_manual_voice_command()
                time.sleep(0.5)  # Evita attivazioni multiple

            if keyboard.is_pressed('s'):
                self._show_statistics()
                time.sleep(0.5)

            if keyboard.is_pressed('t'):
                print("\n🔊 Test microfono...")

                def test_mic():
                    self.speech_handler.test_microphone(duration=3)

                # Esegui in thread per non bloccare
                import threading
                threading.Thread(target=test_mic, daemon=True).start()
                time.sleep(0.5)

            if keyboard.is_pressed('m'):
                self._change_ai_model()
                time.sleep(0.5)

            if keyboard.is_pressed('w'):
                self._open_mobile_app()
                time.sleep(0.5)

        except Exception as e:
            if DEBUG:
                print(f"[MAIN] Errore gestione tastiera: {e}")

    def _on_wake_word_detected(self, text):
        """Callback per wake word rilevata"""
        asyncio.create_task(self._handle_wake_word(text))

    def _on_command_received(self, text):
        """Callback per comando ricevuto"""
        asyncio.create_task(self._handle_voice_command(text))

    async def _handle_wake_word(self, text):
        """Gestisce wake word rilevata"""
        try:
            self.wake_words_detected += 1
            print(f"🎯 Wake word rilevata! Audio: '{text}'")

            # Suono di conferma
            self.audio_manager.play_notification_sound(frequency=1200, duration=0.2)

            # Attiva modalità comando
            self.speech_handler.wait_for_command(timeout=10)

            # Conferma vocale
            self.speech_handler.speak("Sì?")

        except Exception as e:
            if DEBUG:
                print(f"[MAIN] Errore gestione wake word: {e}")

    async def _handle_voice_command(self, command):
        """Gestisce comando vocale ricevuto"""
        try:
            print(f"📝 Comando ricevuto: '{command}'")

            # Processa con AI
            print("🤖 Elaborando risposta...")
            response = await self.ai_assistant.process_command(command)

            if response:
                print(f"💬 Risposta: {response}")
                self.speech_handler.speak(response)
                self.commands_processed += 1

                # Suono completamento
                self.audio_manager.play_notification_sound(frequency=800, duration=0.2)
            else:
                print("❌ Errore nell'elaborazione")
                self.speech_handler.speak("Mi dispiace, non sono riuscito a elaborare la richiesta.")

        except Exception as e:
            print(f"❌ Errore comando: {e}")
            self.speech_handler.speak("Si è verificato un errore tecnico.")

    async def _process_manual_voice_command(self):
        """Processa un comando vocale manuale (SPAZIO)"""
        try:
            print("🎙️  In ascolto per comando manuale...")

            # Usa il nuovo metodo per comando manuale
            command = self.speech_handler.manual_voice_command()

            if not command.strip():
                print("❌ Nessun comando rilevato")
                self.speech_handler.speak("Non ho sentito nulla. Riprova.")
                return

            await self._handle_voice_command(command)

        except Exception as e:
            error_msg = f"Errore nel processare il comando: {e}"
            print(f"❌ {error_msg}")
            if DEBUG:
                print(f"[MAIN] Dettagli errore: {e}")
            self.speech_handler.speak("Si è verificato un errore tecnico.")

    def _show_statistics(self):
        """Mostra statistiche del sistema"""
        uptime = datetime.now() - self.session_start
        mic_info = self.speech_handler.get_microphone_info()

        print("\n📊 STATISTICHE JARVIS HELMET")
        print("=" * 40)
        print(f"⏱️  Tempo attivo: {uptime}")
        print(f"🎯 Wake words rilevate: {self.wake_words_detected}")
        print(f"📝 Comandi processati: {self.commands_processed}")
        print(f"🔊 Livello audio corrente: {self.audio_manager.get_audio_level():.2%}")
        print(f"🤖 Modello AI: {self.ai_assistant.model}")

        if mic_info:
            print(f"🎤 Microfono: {mic_info['name']} (Indice: {mic_info['index']})")
            print(f"   Canali: {mic_info['channels']}, Sample Rate: {mic_info['sample_rate']}")

        print(f"🎧 Monitoraggio: {'Attivo' if self.speech_handler.is_monitoring else 'Inattivo'}")
        print(f"🎙️  Modalità comando: {'Attiva' if self.speech_handler.waiting_for_command else 'Wake Word'}")
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

            print(f"\n✅ Modello attuale: {self.ai_assistant.model}")

        except Exception as e:
            print(f"❌ Errore cambio modello: {e}")

    def _open_mobile_app(self):
        """Apre l'app mobile nel browser"""
        try:
            import webbrowser
            if self.mobile_server:
                url = f"http://localhost:8766"
                webbrowser.open(url)
                print(f"🌐 App mobile aperta: {url}")
            else:
                print("❌ Server app mobile non disponibile")
        except Exception as e:
            print(f"❌ Errore apertura app mobile: {e}")

    # Metodi per integrazione con WebSocket (chiamati dall'app mobile)
    async def _on_mobile_wake_word(self):
        """Gestisce attivazione da app mobile"""
        await self._handle_wake_word("Attivazione da app mobile")

    async def _on_mobile_listening_start(self):
        """Gestisce inizio ascolto da app mobile"""
        self.speech_handler.wait_for_command(timeout=15)

    async def _shutdown(self):
        """Arresta il sistema in modo pulito"""
        print("🔄 Arresto sistema in corso...")

        try:
            # Ferma monitoraggio vocale
            self.speech_handler.stop_monitoring()

            # Ferma tutti i componenti
            self.speech_handler.stop_all()
            self.audio_manager.cleanup()

            # Ferma server mobile
            if hasattr(self, 'mobile_server') and self.mobile_server:
                self.mobile_server.stop_server()

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
        jarvis = ImprovedJarvisHelmet()

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