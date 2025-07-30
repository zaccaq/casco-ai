import requests
import json
import asyncio
from config.settings import OLLAMA_HOST, OLLAMA_MODEL, DEBUG


class OllamaAssistant:
    def __init__(self):
        """Inizializza il client Ollama per AI locale gratuita"""
        self.host = OLLAMA_HOST
        self.model = OLLAMA_MODEL
        self.conversation_history = []

        # Sistema prompt per il casco Jarvis
        self.system_prompt = """
        Sei Jarvis, l'assistente personale integrato in un casco smart. 
        Caratteristiche della tua personalità:
        - Sei professionale ma amichevole, come l'assistente di Iron Man
        - Dai risposte concise e utili (massimo 2-3 frasi)
        - Puoi aiutare con informazioni generali, calcoli, conversazioni
        - Rispondi sempre in italiano
        - Mantieni un tono futuristico ma accessibile
        - Se non sai qualcosa, ammettilo onestamente

        Ricorda: stai comunicando tramite audio, quindi evita formattazioni complesse.
        Usa un linguaggio naturale e colloquiale.
        """

        self._check_ollama_connection()

    def _check_ollama_connection(self):
        """Verifica la connessione a Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if DEBUG:
                    print(f"[OLLAMA] Connesso a {self.host}")
                    print(f"[OLLAMA] Modelli disponibili: {model_names}")

                # Controlla se il modello richiesto è disponibile
                if not any(self.model in name for name in model_names):
                    if DEBUG:
                        print(f"[OLLAMA] Modello {self.model} non trovato, scaricando...")
                    self._download_model()
                else:
                    if DEBUG:
                        print(f"[OLLAMA] Modello {self.model} pronto")
            else:
                raise Exception(f"Ollama non risponde (status: {response.status_code})")

        except requests.exceptions.ConnectionError:
            raise Exception(
                "Ollama non è in esecuzione! Installalo e avvialo:\n"
                "1. Scarica da: https://ollama.ai/\n"
                "2. Installa Ollama\n"
                "3. Esegui: ollama serve"
            )
        except Exception as e:
            raise Exception(f"Errore connessione Ollama: {e}")

    def _download_model(self):
        """Scarica il modello se non presente"""
        try:
            if DEBUG:
                print(f"[OLLAMA] Scaricando modello {self.model}...")

            # Comando pull per scaricare il modello
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": self.model},
                timeout=300  # 5 minuti timeout per download
            )

            if response.status_code == 200:
                if DEBUG:
                    print(f"[OLLAMA] Modello {self.model} scaricato con successo")
            else:
                raise Exception(f"Errore download modello: {response.text}")

        except Exception as e:
            if DEBUG:
                print(f"[OLLAMA] Errore download: {e}")
            raise

    async def process_command(self, user_input: str) -> str:
        """
        Processa un comando vocale dell'utente e restituisce la risposta

        Args:
            user_input (str): Il testo del comando vocale

        Returns:
            str: La risposta di Ollama
        """
        try:
            if DEBUG:
                print(f"[OLLAMA] Processando: {user_input}")

            # Prepara il prompt completo
            full_prompt = f"{self.system_prompt}\n\nUtente: {user_input}\nJarvis:"

            # Invia la richiesta a Ollama
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 200,  # Risposte brevi per audio
                        "stop": ["\nUtente:", "\n\n"]
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get('response', '').strip()

                # Pulisci la risposta
                assistant_response = self._clean_response(assistant_response)

                if DEBUG:
                    print(f"[OLLAMA] Risposta: {assistant_response}")

                return assistant_response
            else:
                error_msg = f"Errore Ollama: {response.status_code}"
                if DEBUG:
                    print(f"[OLLAMA] {error_msg}")
                return "Mi dispiace, ho riscontrato un problema tecnico."

        except requests.exceptions.Timeout:
            error_msg = "Timeout nella risposta"
            if DEBUG:
                print(f"[OLLAMA] {error_msg}")
            return "Mi dispiace, sto impiegando troppo tempo a rispondere."

        except Exception as e:
            error_msg = f"Errore nell'elaborazione: {str(e)}"
            if DEBUG:
                print(f"[OLLAMA] Errore: {error_msg}")
            return "Mi dispiace, ho riscontrato un problema tecnico."

    def _clean_response(self, response: str) -> str:
        """Pulisce la risposta da artefatti del modello"""
        # Rimuovi prefissi comuni
        prefixes_to_remove = [
            "Jarvis:", "jarvis:", "Assistente:", "assistente:",
            "AI:", "ai:", "Bot:", "bot:"
        ]

        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()

        # Rimuovi righe vuote multiple
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        response = '\n'.join(lines)

        # Limita lunghezza per audio
        if len(response) > 300:
            sentences = response.split('.')
            response = '. '.join(sentences[:2]) + '.'

        return response

    def reset_conversation(self):
        """Resetta la cronologia della conversazione"""
        self.conversation_history = []
        if DEBUG:
            print("[OLLAMA] Cronologia conversazione resettata")

    async def get_system_status(self) -> str:
        """Restituisce lo stato del sistema"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                return f"Jarvis attivo con modello {self.model}. Sistema operativo."
            else:
                return "Sistema Jarvis attivo ma Ollama non risponde."
        except:
            return "Sistema Jarvis attivo in modalità ridotta."

    def list_available_models(self) -> list:
        """Lista i modelli disponibili in Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except:
            return []

    def switch_model(self, model_name: str) -> bool:
        """Cambia il modello AI"""
        try:
            available_models = self.list_available_models()
            if any(model_name in name for name in available_models):
                self.model = model_name
                if DEBUG:
                    print(f"[OLLAMA] Modello cambiato a: {model_name}")
                return True
            else:
                if DEBUG:
                    print(f"[OLLAMA] Modello {model_name} non disponibile")
                return False
        except:
            return False