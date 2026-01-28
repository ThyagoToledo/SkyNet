# SKYNET - Assistente Pessoal com IA

<div align="center">

![Skynet Logo](assets/skynet-logo.png)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat-square&logo=three.js&logoColor=white)](https://threejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

Um assistente pessoal inteligente para PC com visualização 3D interativa de partículas

[Instalação](#-instalação) •
[Funcionalidades](#funcionalidades) •
[Uso](#como-usar) •
[Comandos](#comandos-de-voz) •
[Tecnologias](#tecnologias)

</div>

---

## Sobre o Projeto

Skynet é um assistente pessoal para PC que combina:
- Reconhecimento de voz com Whisper (processamento local, privado)
- Inteligência Artificial com Google Gemini
- Síntese de voz natural com Edge TTS
- Controle do sistema (abrir apps, executar comandos, pesquisar na web)
- Visualização 3D interativa com sistema de partículas

![Demo](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=flat-square)

---

## Funcionalidades

### Reconhecimento de Voz (Speech-to-Text)
- Modelo OpenAI Whisper rodando localmente
- Aceleração AMD GPU via DirectML
- 100% offline após download do modelo
- Suporte a português brasileiro
- Ignora ruídos de fundo

### Inteligência Artificial
- Integração com Google Gemini API
- Memória de conversação
- Análise de intenção do usuário
- Respostas contextuais e naturais

### Síntese de Voz (Text-to-Speech)
- Edge TTS - Vozes neurais da Microsoft (qualidade premium)
- Fallback para pyttsx3 (offline)
- Voz em português brasileiro

### Controle do Sistema
| Comando | Ação |
|---------|------|
| Abrir aplicativos | Chrome, VS Code, Spotify, etc. |
| Fechar aplicativos | Encerra processos |
| Pesquisar na web | Abre busca no Google |
| Executar comandos | CMD/PowerShell |
| Controlar volume | Aumentar, diminuir, mudo |
| Screenshot | Captura de tela |
| Digitar texto | Automação de teclado |

### Sistema de Memória
- Curto prazo: Histórico da conversa atual
- Longo prazo: Banco SQLite com preferências
- Extração automática de informações do usuário

### Visualização 3D
Sistema de partículas interativo com múltiplos modos:
- Esfera - Partículas em formação esférica
- Átomo - Órbitas atômicas
- Fogos - Explosão de partículas
- Onda - Ondulação suave
- Hélice - Estrutura de DNA
- Galáxia - Braços espirais

As partículas respondem ao estado do assistente:
- Idle - Azul calmo
- Ouvindo - Verde pulsante
- Pensando - Laranja rápido
- Falando - Roxo expansivo

---

## Instalação

### Pré-requisitos
- Python 3.10 ou superior
- Windows 10/11
- (Opcional) GPU AMD para aceleração

### Instalação Rápida (Windows)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/skynet.git
cd skynet

# 2. Execute o instalador
install.bat
```

### Instalação Manual

```bash
# 1. Criar ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar PyAudio (Windows)
pip install pipwin
pipwin install pyaudio
```

### Configuração

1. Copie o arquivo de exemplo:
```bash
copy .env.example .env
```

2. Edite `.env` e adicione sua API Key do Gemini:
```env
GEMINI_API_KEY=sua_api_key_aqui
```

> Obtenha sua API Key gratuita em: https://makersuite.google.com/app/apikey

---

## Como Usar

### Iniciar o Assistente

```bash
# Windows
start.bat

# Ou diretamente
python main.py
```

### Acessar a Interface

Abra no navegador: **http://localhost:8000**

### Interação

1. Por voz: Clique no botão de voz ou diga "Skynet"
2. Por texto: Digite na caixa de mensagem
3. Modos visuais: Clique nos botões à direita

---

## Comandos de Voz

### Aplicativos
```
"Abrir Chrome"
"Abrir VS Code"
"Abrir Spotify"
"Fechar navegador"
```

### Pesquisa
```
"Pesquisar clima em São Paulo"
"Buscar notícias sobre tecnologia"
```

### Sistema
```
"Volume aumentar"
"Volume diminuir"
"Tirar screenshot"
"Executar comando dir"
```

### Conversa
```
"Olá, como você está?"
"Me conte uma piada"
"Qual a capital do Brasil?"
```

---

## Estrutura do Projeto

```
skynet/
├── main.py                    # Entrada principal
├── requirements.txt           # Dependências
├── .env                       # Configurações (criar)
│
├── src/
│   ├── core/
│   │   └── assistant.py          # Orquestrador
│   ├── speech/
│   │   ├── speech_to_text.py     # Whisper STT
│   │   └── text_to_speech.py     # Edge TTS
│   ├── ai/
│   │   └── gemini_client.py      # Cliente Gemini
│   ├── system/
│   │   └── system_controller.py  # Controle PC
│   ├── memory/
│   │   └── memory_manager.py     # SQLite
│   └── server/
│       └── websocket_server.py   # FastAPI
│
├── frontend/
│   ├── index.html                # Interface
│   └── js/
│       ├── particles.js          # Three.js 3D
│       ├── websocket-client.js   # WebSocket
│       └── app.js                # App frontend
│
└── data/
    └── memory.db                 # Banco de dados
```

---

## Tecnologias

### Backend
| Tecnologia | Uso |
|------------|-----|
| ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white) | Linguagem principal |
| ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | Servidor web |
| ![Whisper](https://img.shields.io/badge/-Whisper-412991?style=flat-square&logo=openai&logoColor=white) | Reconhecimento de voz |
| ![Gemini](https://img.shields.io/badge/-Gemini-4285F4?style=flat-square&logo=google&logoColor=white) | IA generativa |
| ![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) | Banco de dados |

### Frontend
| Tecnologia | Uso |
|------------|-----|
| ![Three.js](https://img.shields.io/badge/-Three.js-000000?style=flat-square&logo=three.js&logoColor=white) | Visualização 3D |
| ![JavaScript](https://img.shields.io/badge/-JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) | Lógica frontend |
| ![WebSocket](https://img.shields.io/badge/-WebSocket-010101?style=flat-square&logo=socket.io&logoColor=white) | Tempo real |

---

## Configurações

### Variáveis de Ambiente (.env)

```env
# API Key do Gemini (obrigatório para IA completa)
GEMINI_API_KEY=your_api_key_here

# Configurações do assistente
ASSISTANT_NAME=Skynet
ASSISTANT_VOICE=pt-BR-FranciscaNeural
WAKE_WORD=skynet

# Reconhecimento de voz
WHISPER_MODEL=small    # tiny, small, medium, large
LANGUAGE=pt

# Servidor
SERVER_HOST=localhost
SERVER_PORT=8000

# Memória
MAX_CONVERSATION_HISTORY=20
MEMORY_DB_PATH=./data/memory.db
```

---

## Contribuindo

Contribuições são bem-vindas! 

1. Fork o projeto
2. Crie sua branch (git checkout -b feature/NovaFeature)
3. Commit suas mudanças (git commit -m 'Add NovaFeature')
4. Push para a branch (git push origin feature/NovaFeature)
5. Abra um Pull Request

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## Agradecimentos

- OpenAI Whisper - Reconhecimento de voz
- Google Gemini - IA generativa
- Three.js - Gráficos 3D
- FastAPI - Framework web

---

<div align="center">

Feito com dedicação e café

Deixe uma estrela se este projeto ajudou!

</div>
