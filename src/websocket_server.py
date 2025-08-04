#!/usr/bin/env python3
"""
WebSocket Server per comunicazione tra app mobile e casco Jarvis - VERSIONE CORRETTA
"""

import asyncio
import websockets
import json
import threading
import time
from datetime import datetime
from config.settings import DEBUG


class JarvisWebSocketServer:
    def __init__(self, main_system=None):
        """Inizializza il server WebSocket"""
        self.main_system = main_system
        self.connected_clients = set()
        self.server = None
        self.is_running = False

        # Statistiche da condividere
        self.stats = {
            'commands_processed': 0,
            'wake_words_detected': 0,
            'start_time': datetime.now(),
            'ai_model': 'llama3.2:1b',
            'status': 'online'
        }

        if DEBUG:
            print("[WEBSOCKET] Server inizializzato")

    async def start_server(self, host='0.0.0.0', port=8765):
        """Avvia il server WebSocket"""
        try:
            self.server = await websockets.serve(
                self.handle_client,  # ← FIX: Rimosso 'path' parameter
                host,
                port,
                ping_interval=20,
                ping_timeout=10
            )

            self.is_running = True

            if DEBUG:
                print(f"[WEBSOCKET] Server avviato su {host}:{port}")
                print(f"[WEBSOCKET] App mobile: http://{self.get_local_ip()}:{port + 1}")

            # Avvia broadcast periodico statistiche
            asyncio.create_task(self.broadcast_stats_periodically())

            return self.server

        except Exception as e:
            if DEBUG:
                print(f"[WEBSOCKET] Errore avvio server: {e}")
            raise

    async def handle_client(self, websocket):  # ← FIX: Rimosso parameter 'path'
        """Gestisce connessione client - VERSIONE CORRETTA"""
        client_ip = websocket.remote_address[0]

        try:
            # Registra client
            self.connected_clients.add(websocket)

            if DEBUG:
                print(f"[WEBSOCKET] Client connesso: {client_ip}")
                print(f"[WEBSOCKET] Client totali: {len(self.connected_clients)}")

            # Invia stato iniziale
            await self.send_to_client(websocket, {
                'type': 'connection_established',
                'message': 'Connesso al casco Jarvis',
                'stats': self.get_current_stats()
            })

            # Loop gestione messaggi
            async for message in websocket:
                await self.process_client_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            if DEBUG:
                print(f"[WEBSOCKET] Client disconnesso: {client_ip}")
        except Exception as e:
            if DEBUG:
                print(f"[WEBSOCKET] Errore gestione client {client_ip}: {e}")
        finally:
            # Rimuovi client
            self.connected_clients.discard(websocket)
            if DEBUG:
                print(f"[WEBSOCKET] Client rimosso. Totali: {len(self.connected_clients)}")

    async def process_client_message(self, websocket, message):
        """Processa messaggio dal client mobile"""
        try:
            data = json.loads(message)
            message_type = data.get('type', '')

            if DEBUG:
                print(f"[WEBSOCKET] Messaggio ricevuto: {message_type}")

            # Gestisci diversi tipi di messaggio
            if message_type == 'activate_jarvis':
                await self.handle_activate_jarvis(websocket)

            elif message_type == 'start_listening':
                await self.handle_start_listening(websocket)

            elif message_type == 'end_listening':
                await self.handle_end_listening(websocket)

            elif message_type == 'test_microphone':
                await self.handle_test_microphone(websocket)

            elif message_type == 'emergency_stop':
                await self.handle_emergency_stop(websocket)

            elif message_type == 'list_models':
                await self.handle_list_models(websocket)

            elif message_type == 'setting_change':
                await self.handle_setting_change(websocket, data)

            elif message_type == 'get_stats':
                await self.send_stats_update(websocket)

            elif message_type == 'ping':
                await self.send_to_client(websocket, {'type': 'pong'})

            else:
                if DEBUG:
                    print(f"[WEBSOCKET] Tipo messaggio sconosciuto: {message_type}")

        except json.JSONDecodeError:
            if DEBUG:
                print("[WEBSOCKET] Errore parsing JSON")
        except Exception as e:
            if DEBUG:
                print(f"[WEBSOCKET] Errore processamento messaggio: {e}")

    async def handle_activate_jarvis(self, websocket):
        """Gestisce attivazione Jarvis"""
        if self.main_system:
            # Simula attivazione wake word
            self.stats['wake_words_detected'] += 1

            # Notifica sistema principale se disponibile
            if hasattr(self.main_system, '_on_mobile_wake_word'):
                await self.main_system._on_mobile_wake_word()

            await self.send_to_client(websocket, {
                'type': 'jarvis_activated',
                'message': 'Jarvis attivato con successo'
            })

            # Notifica tutti i client
            await self.broadcast_to_all({
                'type': 'wake_word_detected',
                'stats': self.get_current_stats()
            })

    async def handle_start_listening(self, websocket):
        """Gestisce inizio ascolto comando vocale"""
        await self.send_to_client(websocket, {
            'type': 'listening_started',
            'message': 'In ascolto per comando vocale...'
        })

        # Se collegato al sistema principale, avvia ascolto
        if self.main_system and hasattr(self.main_system, '_on_mobile_listening_start'):
            await self.main_system._on_mobile_listening_start()

    async def handle_end_listening(self, websocket):
        """Gestisce fine ascolto comando vocale"""
        self.stats['commands_processed'] += 1

        await self.send_to_client(websocket, {
            'type': 'command_processed',
            'message': 'Comando processato con successo',
            'stats': self.get_current_stats()
        })

    async def handle_test_microphone(self, websocket):
        """Gestisce test microfono"""
        await self.send_to_client(websocket, {
            'type': 'microphone_test_started',
            'message': 'Test microfono avviato'
        })

        # Esegui test microfono se sistema principale disponibile
        if self.main_system and hasattr(self.main_system, 'speech_handler'):
            def test_mic():
                try:
                    self.main_system.speech_handler.test_microphone(3)
                    asyncio.create_task(self.send_to_client(websocket, {
                        'type': 'microphone_test_completed',
                        'message': 'Test microfono completato con successo'
                    }))
                except Exception as e:
                    asyncio.create_task(self.send_to_client(websocket, {
                        'type': 'microphone_test_failed',
                        'message': f'Test microfono fallito: {str(e)}'
                    }))

            threading.Thread(target=test_mic, daemon=True).start()

    async def handle_emergency_stop(self, websocket):
        """Gestisce stop di emergenza"""
        self.stats['status'] = 'stopped'

        await self.broadcast_to_all({
            'type': 'emergency_stop_executed',
            'message': 'Sistema fermato con stop di emergenza',
            'stats': self.get_current_stats()
        })

        # Se collegato al sistema principale, ferma tutto
        if self.main_system:
            self.main_system.is_running = False

    async def handle_list_models(self, websocket):
        """Gestisce richiesta lista modelli AI"""
        models = ['llama3.2:1b', 'llama3.2:3b', 'qwen2.5:1.5b', 'mistral:7b']

        # Se sistema principale disponibile, usa modelli reali
        if self.main_system and hasattr(self.main_system, 'ai_assistant'):
            try:
                models = self.main_system.ai_assistant.list_available_models()
            except:
                pass

        await self.send_to_client(websocket, {
            'type': 'models_list',
            'models': models,
            'current_model': self.stats['ai_model']
        })

    async def handle_setting_change(self, websocket, data):
        """Gestisce cambio impostazioni"""
        setting = data.get('setting', '')
        value = data.get('value', False)

        if DEBUG:
            print(f"[WEBSOCKET] Cambio impostazione: {setting} = {value}")

        await self.send_to_client(websocket, {
            'type': 'setting_changed',
            'setting': setting,
            'value': value,
            'message': f'Impostazione {setting} aggiornata'
        })

    async def send_to_client(self, websocket, data):
        """Invia messaggio a un client specifico"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            self.connected_clients.discard(websocket)
        except Exception as e:
            if DEBUG:
                print(f"[WEBSOCKET] Errore invio messaggio: {e}")

    async def broadcast_to_all(self, data):
        """Invia messaggio a tutti i client connessi"""
        if not self.connected_clients:
            return

        message = json.dumps(data)
        disconnected = set()

        for websocket in self.connected_clients:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                if DEBUG:
                    print(f"[WEBSOCKET] Errore broadcast: {e}")
                disconnected.add(websocket)

        # Rimuovi client disconnessi
        self.connected_clients -= disconnected

    async def broadcast_stats_periodically(self):
        """Invia statistiche aggiornate periodicamente"""
        while self.is_running:
            await asyncio.sleep(5)  # Ogni 5 secondi

            if self.connected_clients:
                # Aggiorna stats dal sistema principale se disponibile
                if self.main_system:
                    self.update_stats_from_main()

                await self.broadcast_to_all({
                    'type': 'stats_update',
                    'stats': self.get_current_stats()
                })

    async def send_stats_update(self, websocket):
        """Invia aggiornamento statistiche a client specifico"""
        await self.send_to_client(websocket, {
            'type': 'stats_update',
            'stats': self.get_current_stats()
        })

    def update_stats_from_main(self):
        """Aggiorna statistiche dal sistema principale"""
        if self.main_system:
            try:
                self.stats['commands_processed'] = self.main_system.commands_processed
                self.stats['wake_words_detected'] = self.main_system.wake_words_detected
                if hasattr(self.main_system, 'ai_assistant'):
                    self.stats['ai_model'] = self.main_system.ai_assistant.model
                self.stats['status'] = 'online' if self.main_system.is_running else 'offline'
            except:
                pass

    def get_current_stats(self):
        """Ottieni statistiche attuali"""
        uptime = datetime.now() - self.stats['start_time']

        return {
            'commands_processed': self.stats['commands_processed'],
            'wake_words_detected': self.stats['wake_words_detected'],
            'uptime_seconds': int(uptime.total_seconds()),
            'ai_model': self.stats['ai_model'],
            'status': self.stats['status'],
            'connected_clients': len(self.connected_clients)
        }

    def update_stats(self, **kwargs):
        """Aggiorna statistiche dal sistema principale"""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value

    def get_local_ip(self):
        """Ottieni IP locale per visualizzare nell'app mobile"""
        import socket
        try:
            # Connessione fittizia per ottenere IP locale
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

    async def stop_server(self):
        """Ferma il server WebSocket"""
        self.is_running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Disconnetti tutti i client
        for websocket in list(self.connected_clients):
            try:
                await websocket.close()
            except:
                pass

        self.connected_clients.clear()

        if DEBUG:
            print("[WEBSOCKET] Server fermato")


# Funzione per avviare server in thread separato
def start_websocket_server_thread(main_system=None, host='0.0.0.0', port=8765):
    """Avvia server WebSocket in thread separato"""

    def run_server():
        websocket_server = JarvisWebSocketServer(main_system)

        async def start():
            await websocket_server.start_server(host, port)
            await asyncio.Future()  # Run forever

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start())
        except Exception as e:
            if DEBUG:
                print(f"[WEBSOCKET] Errore thread server: {e}")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    if DEBUG:
        print(f"[WEBSOCKET] Thread server avviato su {host}:{port}")

    return thread


# Test standalone
if __name__ == "__main__":
    async def main():
        server = JarvisWebSocketServer()
        await server.start_server()

        print("🚀 Server WebSocket avviato!")
        print("📱 Connetti l'app mobile a: ws://localhost:8765")
        print("⏹️  Premi Ctrl+C per fermare")

        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            print("\n🛑 Arresto server...")
            await server.stop_server()


    asyncio.run(main())