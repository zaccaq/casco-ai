#!/usr/bin/env python3
"""
Server HTTP per servire l'app mobile Jarvis Helmet Controller
"""

import http.server
import socketserver
import os
import threading
import webbrowser
import socket
from config.settings import DEBUG


class JarvisMobileServer:
    def __init__(self, port=8766, mobile_app_dir="mobile_app"):
        self.port = port
        self.mobile_app_dir = mobile_app_dir
        self.server = None
        self.thread = None
        self.original_dir = os.getcwd()

        # Crea directory mobile_app se non esiste
        if not os.path.exists(mobile_app_dir):
            os.makedirs(mobile_app_dir)
            if DEBUG:
                print(f"[HTTP] Creata directory: {mobile_app_dir}")

    def start_server(self, open_browser=True):
        """Avvia server HTTP per app mobile"""
        try:
            def run_server():
                try:
                    # Cambia directory di lavoro per servire i file
                    os.chdir(self.mobile_app_dir)

                    with socketserver.TCPServer(("", self.port), http.server.SimpleHTTPRequestHandler) as httpd:
                        self.server = httpd

                        if DEBUG:
                            print(f"[HTTP] Server mobile avviato su porta {self.port}")
                            print(f"[HTTP] URL locale: http://localhost:{self.port}")
                            print(f"[HTTP] URL rete: http://{self.get_local_ip()}:{self.port}")

                        httpd.serve_forever()

                except Exception as e:
                    if DEBUG:
                        print(f"[HTTP] Errore server: {e}")
                finally:
                    # Ripristina directory originale
                    os.chdir(self.original_dir)

            # Avvia server in thread separato
            self.thread = threading.Thread(target=run_server, daemon=True)
            self.thread.start()

            # Pausa per permettere l'avvio del server
            threading.Event().wait(0.5)

            # Apri browser se richiesto
            if open_browser:
                local_url = f"http://localhost:{self.port}"
                threading.Timer(1.5, lambda: webbrowser.open(local_url)).start()

            return True

        except Exception as e:
            if DEBUG:
                print(f"[HTTP] Errore avvio server mobile: {e}")
            return False

    def stop_server(self):
        """Ferma il server HTTP"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            if DEBUG:
                print("[HTTP] Server mobile fermato")

    def get_local_ip(self):
        """Ottieni IP locale della macchina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

    def create_mobile_files(self):
        """Crea i file dell'app mobile se non esistono"""
        files_to_create = {
            'index.html': self.get_index_html(),
            'manifest.json': self.get_manifest_json(),
            'sw.js': self.get_service_worker()
        }

        for filename, content in files_to_create.items():
            filepath = os.path.join(self.mobile_app_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                if DEBUG:
                    print(f"[HTTP] Creato file: {filename}")

    def get_index_html(self):
        """Restituisce il contenuto HTML completo dell'app mobile"""
        return '''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#1a1a2e">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Jarvis Helmet">

    <title>Jarvis Helmet Controller</title>

    <link rel="manifest" href="manifest.json">
    <link rel="icon" type="image/png" sizes="192x192" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='%2300d4ff'/%3E%3Ctext x='50' y='65' text-anchor='middle' font-size='40' fill='white'%3E🤖%3C/text%3E%3C/svg%3E">

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f4c75 100%);
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }

        .logo {
            font-size: 4rem;
            margin-bottom: 10px;
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { text-shadow: 0 0 20px #00d4ff; }
            to { text-shadow: 0 0 30px #00d4ff, 0 0 40px #00d4ff; }
        }

        .title {
            font-size: 1.8rem;
            font-weight: 300;
            margin-bottom: 5px;
            background: linear-gradient(45deg, #00d4ff, #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 0.9rem;
            opacity: 0.7;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 0;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }

        .status-dot.online { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .status-dot.offline { background: #ff4757; box-shadow: 0 0 10px #ff4757; }
        .status-dot.pending { background: #ffa502; box-shadow: 0 0 10px #ffa502; }

        .control-section {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 1.2rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }

        .section-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(45deg, #00d4ff, #ffffff);
            margin-right: 10px;
            border-radius: 2px;
        }

        .control-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .control-btn {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(255, 255, 255, 0.1));
            border: 2px solid rgba(0, 212, 255, 0.3);
            border-radius: 15px;
            padding: 20px;
            color: white;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            min-height: 80px;
            backdrop-filter: blur(10px);
            user-select: none;
        }

        .control-btn:hover, .control-btn:active {
            transform: translateY(-2px);
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.4), rgba(255, 255, 255, 0.2));
            border-color: rgba(0, 212, 255, 0.6);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .control-btn.primary {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            border-color: #00d4ff;
            font-size: 1.1rem;
            min-height: 60px;
        }

        .control-btn.primary:hover {
            background: linear-gradient(135deg, #00b8e6, #0088bb);
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 212, 255, 0.4);
        }

        .control-btn .icon {
            font-size: 1.5rem;
        }

        .voice-button {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            border: 4px solid rgba(255, 255, 255, 0.3);
            color: white;
            font-size: 2.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            user-select: none;
        }

        .voice-button:hover, .voice-button.active {
            transform: scale(1.1);
            box-shadow: 0 12px 35px rgba(0, 212, 255, 0.5);
        }

        .voice-button.listening {
            animation: pulse 1.5s ease-in-out infinite;
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.8rem;
            opacity: 0.7;
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            backdrop-filter: blur(10px);
            z-index: 1000;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.9);
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            backdrop-filter: blur(10px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            opacity: 1;
        }

        @media (max-width: 480px) {
            .container {
                padding: 15px;
            }

            .control-grid {
                grid-template-columns: 1fr;
            }

            .voice-button {
                width: 100px;
                height: 100px;
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">
        <span class="status-dot offline"></span>
        Disconnesso
    </div>

    <div class="container">
        <div class="header">
            <div class="logo">🤖</div>
            <div class="title">JARVIS HELMET</div>
            <div class="subtitle">Controller Mobile</div>
        </div>

        <!-- Status Card -->
        <div class="status-card">
            <div class="status-indicator">
                <div style="display: flex; align-items: center;">
                    <div class="status-dot offline" id="helmetStatus"></div>
                    <span>Stato Casco</span>
                </div>
                <span id="helmetStatusText">Offline</span>
            </div>
            <div class="status-indicator">
                <div style="display: flex; align-items: center;">
                    <div class="status-dot offline" id="aiStatus"></div>
                    <span>AI Assistant</span>
                </div>
                <span id="aiStatusText">Disconnesso</span>
            </div>
            <div class="status-indicator">
                <div style="display: flex; align-items: center;">
                    <div class="status-dot offline" id="audioStatus"></div>
                    <span>Sistema Audio</span>
                </div>
                <span id="audioStatusText">Inattivo</span>
            </div>
        </div>

        <!-- Voice Control -->
        <div class="control-section">
            <div class="section-title">🎤 Controllo Vocale</div>
            <div style="text-align: center;">
                <button class="voice-button" id="voiceButton">
                    🎙️
                </button>
                <div style="margin-top: 10px; opacity: 0.7;">
                    Tocca per attivare comando vocale
                </div>
            </div>
        </div>

        <!-- Quick Controls -->
        <div class="control-section">
            <div class="section-title">⚡ Controlli Rapidi</div>
            <div class="control-grid">
                <button class="control-btn primary" onclick="activateJarvis()">
                    <span class="icon">🚀</span>
                    Attiva Jarvis
                </button>
                <button class="control-btn" onclick="testMicrophone()">
                    <span class="icon">🎤</span>
                    Test Mic
                </button>
                <button class="control-btn" onclick="showStatistics()">
                    <span class="icon">📊</span>
                    Statistiche
                </button>
                <button class="control-btn" onclick="emergencyStop()">
                    <span class="icon">🛑</span>
                    Stop
                </button>
            </div>
        </div>

        <!-- Statistics -->
        <div class="control-section">
            <div class="section-title">📈 Statistiche</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="commandsCount">0</div>
                    <div class="stat-label">Comandi</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="wakeWordsCount">0</div>
                    <div class="stat-label">Wake Words</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uptime">00:00</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="aiModel">-</div>
                    <div class="stat-label">Modello AI</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast"></div>

    <script>
        // WebSocket connection per comunicazione con il casco
        let ws = null;
        let isConnected = false;
        let isListening = false;
        let stats = {
            commands: 0,
            wakeWords: 0,
            startTime: Date.now(),
            aiModel: 'llama3.2:1b'
        };

        // Initialize app
        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();

            // PWA install prompt
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('sw.js').catch(e => console.log('SW registration failed'));
            }
        });

        function initializeApp() {
            // Update initial stats
            updateStatistics();

            // Voice button events
            const voiceButton = document.getElementById('voiceButton');
            voiceButton.addEventListener('touchstart', startVoiceCommand);
            voiceButton.addEventListener('touchend', endVoiceCommand);
            voiceButton.addEventListener('mousedown', startVoiceCommand);
            voiceButton.addEventListener('mouseup', endVoiceCommand);

            // Auto-connect
            setTimeout(connectToHelmet, 1000);
        }

        function connectToHelmet() {
            try {
                const wsUrl = `ws://${window.location.hostname}:8765`;
                console.log('Connessione WebSocket:', wsUrl);

                ws = new WebSocket(wsUrl);

                ws.onopen = function() {
                    isConnected = true;
                    updateConnectionStatus();
                    updateSystemStatus('online');
                    showToast('✅ Connesso al casco Jarvis!');
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };

                ws.onclose = function() {
                    isConnected = false;
                    updateConnectionStatus();
                    updateSystemStatus('offline');
                    showToast('❌ Connessione persa');

                    // Riconnessione automatica dopo 5 secondi
                    setTimeout(connectToHelmet, 5000);
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    showToast('❌ Errore connessione');
                };

            } catch (error) {
                console.error('Errore connessione:', error);
                showToast('❌ Impossibile connettersi al casco');
            }
        }

        function updateConnectionStatus() {
            const statusEl = document.getElementById('connectionStatus');
            const dot = statusEl.querySelector('.status-dot');

            if (isConnected) {
                dot.className = 'status-dot online';
                statusEl.innerHTML = '<span class="status-dot online"></span>Connesso';
            } else {
                dot.className = 'status-dot offline';
                statusEl.innerHTML = '<span class="status-dot offline"></span>Disconnesso';
            }
        }

        function updateSystemStatus(status) {
            const elements = {
                helmet: { dot: document.getElementById('helmetStatus'), text: document.getElementById('helmetStatusText') },
                ai: { dot: document.getElementById('aiStatus'), text: document.getElementById('aiStatusText') },
                audio: { dot: document.getElementById('audioStatus'), text: document.getElementById('audioStatusText') }
            };

            Object.values(elements).forEach(el => {
                if (status === 'online') {
                    el.dot.className = 'status-dot online';
                    el.text.textContent = 'Attivo';
                } else {
                    el.dot.className = 'status-dot offline';
                    el.text.textContent = 'Offline';
                }
            });
        }

        function startVoiceCommand(e) {
            e.preventDefault();
            if (!isConnected) {
                showToast('❌ Casco non connesso');
                return;
            }

            isListening = true;
            const voiceButton = document.getElementById('voiceButton');
            voiceButton.classList.add('listening');
            voiceButton.innerHTML = '⏹️';

            showToast('🎤 In ascolto...');
            sendToHelmet({type: 'start_listening'});
        }

        function endVoiceCommand(e) {
            e.preventDefault();
            if (!isListening) return;

            isListening = false;
            const voiceButton = document.getElementById('voiceButton');
            voiceButton.classList.remove('listening');
            voiceButton.innerHTML = '🎙️';

            stats.commands++;
            updateStatistics();

            showToast('📝 Comando inviato');
            sendToHelmet({type: 'end_listening'});
        }

        function activateJarvis() {
            if (!isConnected) {
                showToast('❌ Casco non connesso');
                return;
            }

            showToast('🚀 Jarvis attivato');
            stats.wakeWords++;
            updateStatistics();
            sendToHelmet({type: 'activate_jarvis'});
        }

        function testMicrophone() {
            if (!isConnected) {
                showToast('❌ Casco non connesso');
                return;
            }

            showToast('🎤 Test microfono avviato');
            sendToHelmet({type: 'test_microphone'});
        }

        function showStatistics() {
            const uptime = formatUptime(Date.now() - stats.startTime);
            const statsText = `Comandi: ${stats.commands}\\nWake Words: ${stats.wakeWords}\\nUptime: ${uptime}\\nModello: ${stats.aiModel}\\nConnessione: ${isConnected ? 'Online' : 'Offline'}`;
            alert('📊 Statistiche Dettagliate\\n\\n' + statsText);
        }

        function emergencyStop() {
            if (!isConnected) {
                showToast('❌ Casco non connesso');
                return;
            }

            if (confirm('🛑 Vuoi fermare tutti i processi del casco Jarvis?')) {
                sendToHelmet({type: 'emergency_stop'});
                showToast('🛑 Stop di emergenza inviato');
                updateSystemStatus('offline');
            }
        }

        function sendToHelmet(data) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(data));
            }
        }

        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'connection_established':
                    showToast('🎉 ' + data.message);
                    if (data.stats) updateStatsFromServer(data.stats);
                    break;
                case 'jarvis_activated':
                    showToast('🚀 ' + data.message);
                    break;
                case 'command_processed':
                    showToast('✅ Comando processato');
                    break;
                case 'wake_word_detected':
                    showToast('🎯 Wake word rilevata');
                    stats.wakeWords++;
                    updateStatistics();
                    break;
                case 'microphone_test_started':
                    showToast('🎤 ' + data.message);
                    break;
                case 'stats_update':
                    if (data.stats) updateStatsFromServer(data.stats);
                    break;
                default:
                    console.log('Messaggio ricevuto:', data);
            }
        }

        function updateStatsFromServer(serverStats) {
            stats.commands = serverStats.commands_processed || stats.commands;
            stats.wakeWords = serverStats.wake_words_detected || stats.wakeWords;
            stats.aiModel = serverStats.ai_model || stats.aiModel;
            updateStatistics();
        }

        function updateStatistics() {
            document.getElementById('commandsCount').textContent = stats.commands;
            document.getElementById('wakeWordsCount').textContent = stats.wakeWords;
            document.getElementById('uptime').textContent = formatUptime(Date.now() - stats.startTime);
            document.getElementById('aiModel').textContent = stats.aiModel.split(':')[0];
        }

        function formatUptime(ms) {
            const seconds = Math.floor(ms / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);

            if (hours > 0) {
                return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
            }
            return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');

            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Prevent context menu on touch devices
        document.addEventListener('contextmenu', e => e.preventDefault());
    </script>
</body>
</html>'''

    def get_manifest_json(self):
        """Restituisce il manifest PWA completo"""
        return '''{
  "name": "Jarvis Helmet Controller",
  "short_name": "Jarvis",
  "description": "Controller mobile per il sistema casco intelligente Jarvis",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#00d4ff",
  "orientation": "portrait",
  "scope": "/",
  "lang": "it-IT",
  "categories": ["productivity", "utilities"],
  "icons": [
    {
      "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 192 192'%3E%3Ccircle cx='96' cy='96' r='88' fill='%2300d4ff'/%3E%3Ctext x='96' y='130' text-anchor='middle' font-size='80' fill='white'%3E🤖%3C/text%3E%3C/svg%3E",
      "sizes": "192x192",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    },
    {
      "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'%3E%3Ccircle cx='256' cy='256' r='240' fill='%2300d4ff'/%3E%3Ctext x='256' y='340' text-anchor='middle' font-size='200' fill='white'%3E🤖%3C/text%3E%3C/svg%3E",
      "sizes": "512x512",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ],
  "shortcuts": [
    {
      "name": "Attiva Jarvis",
      "short_name": "Attiva",
      "description": "Attivazione rapida dell'assistente",
      "url": "/?action=activate",
      "icons": [
        {
          "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 96'%3E%3Ctext x='48' y='65' text-anchor='middle' font-size='60' fill='%2300d4ff'%3E🚀%3C/text%3E%3C/svg%3E",
          "sizes": "96x96"
        }
      ]
    }
  ]
}'''

    def get_service_worker(self):
        """Restituisce il service worker completo"""
        return '''// Service Worker per Jarvis Helmet Controller PWA
const CACHE_NAME = 'jarvis-helmet-v1.0.0';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

// Installazione
self.addEventListener('install', function(event) {
  console.log('[SW] Installazione Service Worker...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('[SW] Cache aperta:', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
      .then(function() {
        console.log('[SW] Service Worker installato');
        return self.skipWaiting();
      })
  );
});

// Attivazione
self.addEventListener('activate', function(event) {
  console.log('[SW] Attivazione Service Worker...');

  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Eliminazione cache obsoleta:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      console.log('[SW] Service Worker attivato');
      return self.clients.claim();
    })
  );
});

// Gestione richieste
self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          console.log('[SW] Risposta dalla cache:', event.request.url);
          return response;
        }

        return fetch(event.request).then(function(response) {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(function() {
          console.log('[SW] Offline - servendo dalla cache');
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/index.html');
          }
        });
      })
  );
});

console.log('[SW] Jarvis Helmet Service Worker v1.0.0 caricato');'''


def start_mobile_app_server(port=8766):
    """Funzione di utility per avviare il server mobile"""
    server = JarvisMobileServer(port)

    # Crea i file se non esistono
    server.create_mobile_files()

    # Avvia il server
    if server.start_server(open_browser=False):  # Non aprire browser automaticamente
        if DEBUG:
            print(f"✅ App mobile disponibile su:")
            print(f"   📱 Locale: http://localhost:{port}")
            print(f"   🌐 Rete: http://{server.get_local_ip()}:{port}")
            print(f"   💡 Connettiti dal tuo smartphone all'URL di rete!")
        return server
    else:
        if DEBUG:
            print("❌ Impossibile avviare server app mobile")
        return None


# Test standalone
if __name__ == "__main__":
    print("🚀 Avvio server app mobile Jarvis...")

    server = start_mobile_app_server()
    if server:
        try:
            print("📱 Server attivo. Premi Ctrl+C per fermare.")
            input()  # Aspetta input per fermare
        except KeyboardInterrupt:
            print("\n🛑 Arresto server...")
            server.stop_server()
    else:
        print("❌ Impossibile avviare il server")