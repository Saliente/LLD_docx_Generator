# Gerador Automático de LLD para Redes Cisco

Uma ferramenta de automação com interface gráfica (GUI) que transforma a saída de diagnóstico (`show tech-support`) de uma controladora Cisco 9800 em um documento de Low-Level Design (LLD) completo e formatado em `.docx`.

-----

## 📄 Visão Geral

Documentar a configuração de equipamentos de rede é uma tarefa demorada, repetitiva e suscetível a erros. Este aplicativo resolve esse problema ao automatizar completamente o processo para controladoras wireless Cisco 9800, com uma interface gráfica intuitiva que guia o usuário. Ele lê um arquivo `show tech`, extrai dezenas de parâmetros de configuração e os insere em um template Word pré-definido, gerando um LLD profissional em segundos.

-----

## ✨ Principais Funcionalidades

  - **Interface Gráfica Amigável**: Construído com `CustomTkinter` para uma experiência de usuário moderna e simples.
  - **Campos Dinâmicos**: A interface se adapta com base no tipo de equipamento selecionado, mostrando apenas as opções relevantes.
  - **Extração Abrangente de Dados**: Coleta informações sobre inventário, interfaces, WLANs, Tags (Policy, Site, RF), Perfis (Flex, RF, Policy) e muito mais.
  - **Automação via Template**: Utiliza a biblioteca `docxtpl` para preencher um template `.docx` com a sintaxe poderosa do Jinja2.
  - **Código Modular**: O projeto é segmentado em módulos para a interface (`gui.py`), lógica de geração (`script.py`) e parsing de dados (`show_tech.py`), facilitando a manutenção e expansão.

-----

## 🏗️ Estrutura do Projeto

O código foi segmentado em três arquivos principais para melhor organização e escalabilidade:

  - **`gui.py`**: O ponto de entrada do aplicativo. Responsável por construir e gerenciar toda a interface gráfica com a qual o usuário interage.
  - **`script.py`**: Contém a lógica principal para a geração de documentos. Ele é chamado pela GUI, orquestra a coleta de dados e renderiza o template do Word.
  - **`show_tech.py`**: O "motor" de parsing. Contém a classe `ShowTechWireless`, com todos os métodos e expressões regulares responsáveis por extrair as informações do arquivo de `show tech`.

-----

## 🛠️ Tecnologias Utilizadas

  - **Python 3**
  - **CustomTkinter**: Para a criação da interface gráfica.
  - **DocxTemplate (`docxtpl`)**: Para manipulação de templates `.docx`.
  - **Expressões Regulares (`re`)**: Para a extração precisa dos dados.

-----

## ⚙️ Instalação e Configuração

Siga os passos abaixo para configurar o ambiente e rodar o projeto.

### Pré-requisitos

  - Python 3.7 ou superior
  - Pip (gerenciador de pacotes do Python)

### Passos

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/seu-repositorio.git
    cd seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    Crie um arquivo chamado `requirements.txt` com o seguinte conteúdo:

    ```
    customtkinter
    docxtpl
    ```

    Em seguida, instale-o:

    ```bash
    pip install -r requirements.txt
    ```

-----

## 🏃 Como Usar

1.  **Execute a Interface Gráfica:**
    Inicie o aplicativo executando o arquivo `gui.py`:

    ```bash
    python gui.py
    ```

2.  **Selecione o Tipo de Equipamento:**
    Na janela que se abre, escolha "WLC9800" no menu suspenso. Os campos relevantes aparecerão.

3.  **Forneça os Arquivos:**

      - **Arquivo Show Tech**: Clique em "Selecionar..." e navegue até o arquivo de texto com a saída do comando `show tech-support wireless no-sanitize`.
      - **Arquivo de Template**: Clique em "Selecionar..." e escolha o seu arquivo `LLD_Template.docx` com as tags Jinja2.

4.  **Gere o Documento:**
    Clique no botão **"Gerar"**. O script irá processar os arquivos e um novo documento, como `AsBuilt_LLD.docx`, será salvo na mesma pasta do projeto.

-----

## 🔧 Extensibilidade

Para adicionar a extração de novas informações de um `show tech` de WLC9800:

1.  **Abra `show_tech.py`**: Crie um novo método na classe `ShowTechWireless` (ex: `get_qos_maps`). Implemente a lógica de parsing com expressões regulares dentro deste método.
2.  **Abra `script.py`**: Na função `cisco_built_generator`, chame o novo método que você criou e adicione o resultado ao dicionário `context`.
3.  **Atualize seu Template**: Edite o arquivo `.docx` para exibir os novos dados usando a chave que você adicionou ao `context`.

-----

## 📜 Licença

Este projeto está sob a licença BSD. Veja o arquivo `LICENSE` para mais detalhes.
