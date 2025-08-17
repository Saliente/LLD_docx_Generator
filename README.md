Claro, aqui está o `README.md` pronto para ser inserido no GitHub, formatado em Markdown.

-----

# Gerador Automático de LLD para Cisco 9800

Uma ferramenta de automação em Python que transforma a saída de diagnóstico (`show tech-support`) de uma controladora Cisco 9800 em um documento de Low-Level Design (LLD) completo e formatado em `.docx`.

-----

## 📄 Visão Geral

Documentar a configuração de equipamentos de rede é uma tarefa demorada, repetitiva e suscetível a erros. Este script resolve esse problema ao automatizar completamente o processo para controladoras wireless Cisco 9800. Ele lê um arquivo `show tech`, extrai dezenas de parâmetros de configuração e os insere em um template Word pré-definido, gerando um LLD profissional em segundos.

-----

## ✨ Principais Funcionalidades

  - **Extração Abrangente de Dados**: Coleta informações sobre inventário, interfaces, WLANs, Tags (Policy, Site, RF), Perfis (Flex, RF, Policy) e muito mais.
  - **Automação via Template**: Utiliza a biblioteca `docxtpl` para preencher um template `.docx` com a sintaxe poderosa do Jinja2.
  - **Estrutura Orientada a Objetos**: O código é organizado na classe `ShowTechWireless`, tornando-o modular e fácil de estender.
  - **Economia de Tempo**: Reduz horas de trabalho manual para poucos segundos de execução de um script.
  - **Padronização**: Garante que toda a documentação LLD siga um padrão consistente e de alta qualidade.

-----

## 🚀 Como Funciona

O fluxo de trabalho do aplicativo é simples e direto:

1.  **Entrada**: Um arquivo de texto contendo a saída completa do comando `show tech-support wireless no-sanitize`.
2.  **Processamento**: O script Python analisa (`parse`) o arquivo de entrada, usando expressões regulares para encontrar e extrair os dados de configuração relevantes.
3.  **Saída**: As informações extraídas são inseridas em um template `LLD_Template.docx`, gerando um novo arquivo Word (ex: `LLD_WLC-HOSTNAME.docx`) com todos os campos preenchidos.

-----

## 🛠️ Tecnologias Utilizadas

  - **Python 3**
  - **DocxTemplate (`docxtpl`)**: Para manipulação de templates `.docx` com Jinja2.
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
    docxtpl
    ```

    Em seguida, instale-o:

    ```bash
    pip install -r requirements.txt
    ```

-----

## 🏃 Como Usar

1.  **Obtenha o `show tech`:**
    Acesse sua controladora Cisco 9800 e execute o comando abaixo para garantir que todas as informações (incluindo as sensíveis, como strings SNMP) sejam coletadas. Salve a saída em um arquivo de texto chamado `show_tech` na raiz do projeto.

    ```
    show tech-support wireless no-sanitize
    ```

2.  **Prepare o Template (`LLD_Template.docx`):**
    Crie um documento Word que servirá como seu template. Nos locais onde você deseja inserir os dados, use a sintaxe Jinja2.

    **Exemplo para uma variável simples:**
    `O hostname do equipamento é: {{ hostname }}`

    **Exemplo para uma tabela:**
    | Nome da WLAN | ID | SSID |
    |:---|:---|:---|
    |`{% for wlan in wlan_details %}`| | |
    |`{{ wlan.profile_name }}`|`{{ wlan.id }}`|`{{ wlan.ssid }}`|
    |`{% endfor %}`| | |

3.  **Execute o Script:**
    Com o arquivo `show_tech` e o `LLD_Template.docx` na mesma pasta, execute o script:

    ```bash
    python script.py
    ```

    Um novo arquivo, como `LLD_WLC-SP-01.docx`, será gerado com todas as informações preenchidas.

-----

## 🔧 Extensibilidade

Adicionar a extração de novas informações é fácil:

1.  **Crie um novo método** na classe `ShowTechWireless` (ex: `get_qos_maps`).
2.  **Implemente a lógica** de parsing com expressões regulares dentro deste método.
3.  **Chame o novo método** no bloco `if __name__ == '__main__':` e adicione seu retorno ao dicionário `context`.
4.  **Atualize seu template** `.docx` para exibir os novos dados.

-----

## 📜 Licença

Este projeto está sob a licença BSD. Veja o arquivo `LICENSE` para mais detalhes.
