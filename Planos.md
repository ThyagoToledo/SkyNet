Create a real-time interactive 3D particle system using Three.js.
The system should use real-time AI-generated conversation/text and dynamically control particle behavior — including expansion, color changes, and switching between particle models such as sphere, fireworks, atom, and more.

Skynet (Assistente pessoal pc)

1- Fazer ele escutar pelo microfone e escrever em texto o que a pessoa fala para poder decidir o que fazer de acordo com o que ela falar.

2- Usar a api de alguma ia gratuita como o gemini, para o assistente poder fazer pesquisa na web e usar o poder de uma ia

3- Sistema de voz gratuito com Api, para dar voz ao assistente. 

4- Conseguir interagir no pc, abrir apps, mexer no cmd, e fazer o que o usuário pedir, mexer no app e etc.

5- conseguir entender o que está fazendo e ter uma memória base.









O objetivo é construir um assistente pessoal para PC com as seguintes funcionalidades e as melhores opções para implementação:
Reconhecimento de Fala (Speech-to-Text - STT)
Objetivo: Capturar áudio do microfone e transcrever para texto com alta precisão e baixa latência, permitindo ao assistente processar a solicitação sem depender de serviços em nuvem pagos.
Solução Implementada (AMD GPU Acceleration): Utilização do modelo OpenAI Whisper rodando localmente, otimizado via ONNX Runtime com o backend DirectML.
Tecnologia: Hugging Face Optimum + onnxruntime-directml.
Modelo: openai/whisper-small (equilíbrio ideal) ou whisper-tiny (velocidade máxima).
Vantagens:
Custo Zero: Elimina a necessidade de APIs pagas (como Google Cloud).
Privacidade Total: O áudio é processado 100% no seu hardware, nada é enviado para a nuvem.
Performance AMD: Utiliza a aceleração de hardware da sua GPU AMD (via DirectML), garantindo transcrições rápidas sem sobrecarregar a CPU.
Robustez: O modelo Whisper entende pontuação, sotaques e ignora ruídos de fundo melhor que as bibliotecas antigas (como CMU Sphinx).


Inteligência Artificial e Pesquisa Web
Objetivo: Utilizar uma API de IA para processamento de linguagem natural (PLN), pesquisa web e execução de tarefas complexas.
Melhores Opções:
Gemini API: Ótima escolha (conforme você mencionou) por ser gratuita para uso em prototipagem e oferecer recursos avançados de geração e raciocínio. Ideal para lógica de conversação e acesso a informações.
OpenAI API: Alternativa popular, com um modelo gratuito ou de baixo custo, conhecida pela sua robustez e vasta documentação.
Sistema de Voz (Text-to-Speech - TTS)
Objetivo: Dar voz ao assistente para fornecer respostas de forma natural.
Melhores Opções:
Google Cloud Text-to-Speech API / Microsoft Azure TTS: Ambas oferecem vozes de alta qualidade (neurais) e possuem camadas gratuitas. Oferecem a experiência mais natural e profissional.
pyttsx3 (Python) com Vozes Nativas do Sistema: Uma solução gratuita e offline. Utiliza as vozes instaladas no Windows (SAPI5) ou Linux (eSpeak), sendo mais simples de implementar para uso pessoal.
Interação com o PC (Controle de Sistema)
Objetivo: Abrir aplicativos, interagir com o Prompt de Comando (CMD) e realizar ações na interface do usuário (UI).
Melhores Opções:
Módulos subprocess e os (Python): Essenciais para interagir diretamente com o sistema operacional, executar comandos (CMD) e abrir programas.
pyautogui (Python): Permite a automação da interface gráfica (movimento do mouse, cliques e digitação), essencial para interagir com aplicativos que não possuem API.
Entendimento e Memória de Base (Contexto)
Objetivo: Permitir que o assistente entenda o contexto da conversa e lembre-se de informações passadas.
Melhores Opções:
Memória de Curto Prazo (Contexto Conversacional): Implementar uma lista de histórico de conversas ou um cache temporário para enviar as últimas N interações à API de IA (Gemini/OpenAI), mantendo o fluxo da conversa.
Memória de Longo Prazo (Base de Conhecimento): Utilizar um banco de dados simples (como SQLite ou arquivos JSON/YAML) para armazenar preferências do usuário, notas e informações críticas. Para pesquisa eficiente, considerar o uso de Embeddings/Vector Databases em conjunto com a API de IA.
