# Skynet - Personal AI Assistant

## 🚀 Instalação

### 1. Criar Ambiente Virtual
```bash
cd skynet
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar API Key do Gemini
1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API Key
3. Copie o arquivo `.env.example` para `.env`:
```bash
copy .env.example .env
```
4. Edite o arquivo `.env` e adicione sua API Key:
```
GEMINI_API_KEY=sua_api_key_aqui
```

### 4. Instalar Dependências de Áudio (Windows)
Para o reconhecimento de voz, você precisa instalar o PyAudio:
```bash
pip install pipwin
pipwin install pyaudio
```

## 🎮 Executando

```bash
python main.py
```

Acesse http://localhost:8000 no navegador para a interface 3D.

## 📋 Funcionalidades

### 1. Reconhecimento de Voz (STT)
- Usa Whisper localmente com aceleração AMD GPU (DirectML)
- Funciona offline após download do modelo
- Suporte a português brasileiro

### 2. Inteligência Artificial
- Integração com Google Gemini API
- Memória de conversação
- Análise de comandos

### 3. Síntese de Voz (TTS)
- Edge TTS (vozes neurais Microsoft)
- Fallback para pyttsx3 (offline)
- Voz em português brasileiro

### 4. Controle do Sistema
- Abrir/fechar aplicativos
- Executar comandos no terminal
- Pesquisar na web
- Controlar volume
- Tirar screenshots
- Digitar texto

### 5. Memória
- Histórico de conversas
- Preferências do usuário
- Base de conhecimento

### 6. Visualização 3D
- Sistema de partículas com Three.js
- Múltiplos modos: Esfera, Átomo, Fogos, Onda, Hélice, Galáxia
- Responde ao estado do assistente

## 🎤 Comandos de Voz

- "Abrir Chrome" - Abre o navegador
- "Pesquisar [termo]" - Faz busca no Google
- "Fechar Spotify" - Fecha o aplicativo
- "Volume aumentar/diminuir" - Controla volume
- "Screenshot" - Tira captura de tela

## 🔧 Estrutura do Projeto

```
skynet/
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── .env                    # Configurações (criar a partir de .env.example)
├── src/
│   ├── core/
│   │   └── assistant.py    # Orquestrador principal
│   ├── speech/
│   │   ├── speech_to_text.py   # Reconhecimento de voz
│   │   └── text_to_speech.py   # Síntese de voz
│   ├── ai/
│   │   └── gemini_client.py    # Cliente Gemini API
│   ├── system/
│   │   └── system_controller.py # Controle do PC
│   ├── memory/
│   │   └── memory_manager.py   # Gerenciador de memória
│   └── server/
│       └── websocket_server.py # Servidor WebSocket
├── frontend/
│   ├── index.html          # Interface principal
│   └── js/
│       ├── particles.js    # Sistema de partículas 3D
│       ├── websocket-client.js # Cliente WebSocket
│       └── app.js          # Aplicação principal
└── data/
    └── memory.db          # Banco de dados de memória
```

## 🛠️ Tecnologias

- **Python 3.10+**
- **Whisper** - Reconhecimento de voz
- **Google Gemini** - IA generativa
- **Edge TTS** - Síntese de voz
- **FastAPI** - Servidor web
- **Three.js** - Visualização 3D
- **WebSocket** - Comunicação em tempo real
- **SQLite** - Banco de dados local

## 📝 Licença

MIT License
