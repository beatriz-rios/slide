# EPI Guard - Sistema de Monitoramento de EPI em Tempo Real

Este repositório contém o **EPI Guard**, um sistema inteligente de monitoramento de segurança que utiliza Inteligência Artificial para detectar o uso de Equipamentos de Proteção Individual (EPIs) em tempo real através de câmeras de vídeo.

## 🚀 Sobre o Projeto

O objetivo principal é aumentar a segurança no ambiente de trabalho automatizando a fiscalização do uso de EPIs. Atualmente, o sistema está configurado para detectar de forma robusta o uso de **óculos de proteção**.

### 🛠️ Tecnologias Utilizadas

- **Inteligência Artificial:** [YOLOv8](https://github.com/ultralytics/ultralytics) para detecção de objetos de alta performance.
- **Processamento de Imagem:** OpenCV para manipulação de streams de vídeo.
- **Interface Web:** Dashboard construído em PHP, HTML5 e CSS3 Vanilla para visualização de ocorrências.
- **Armazenamento:** Persistência leve baseada em JSON para histórico e capturas locais.

## 📁 Estrutura do Repositório

- `detector.py`: Script principal em Python que executa o modelo de detecção na webcam.
- `index.php`: Dashboard web para visualização em tempo real das detecções e histórico.
- `captures/`: Pasta onde são salvas as imagens das infrações detectadas (com timestamp).
- `history.json`: Banco de dados simplificado (JSON) contendo o log de todas as detecções.
- `best-bia.pt`: Pesos do modelo YOLOv8 treinado especificamente para este projeto.
- `style.css`: Estilização moderna e responsiva do dashboard (suporta Dark Mode).

## ⚙️ Como Funciona

1. O script `detector.py` acessa a webcam e processa cada quadro usando o modelo YOLOv8.
2. Identifica se o colaborador está **"COM EPI"** ou **"SEM EPI"**.
3. Em caso de detecção, os dados (horário, classe, confiança) são salvos no `history.json`.
4. Uma foto da ocorrência é capturada e salva na pasta `captures/`.
5. O dashboard (`index.php`) lê o arquivo JSON e atualiza a interface automaticamente, permitindo que gestores acompanhem o status da equipe.

## 🛠️ Instalação e Uso

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o detector:
   ```bash
   python detector.py
   ```
3. Acesse o dashboard (via servidor local como XAMPP ou PHP Built-in server):
   ```bash
   # Exemplo com PHP
   php -S localhost:8000
   ```

---
Desenvolvido para apresentações de IA e soluções de segurança industrial.
