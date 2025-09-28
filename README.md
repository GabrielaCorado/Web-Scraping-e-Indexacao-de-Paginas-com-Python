Web Crawler e Sistema de Ranqueamento Personalizado

Este projeto em Python implementa um **Web Crawler** recursivo para indexar conteúdo de páginas web e um **Mecanismo de Busca** que ranqueia os resultados utilizando métricas de relevância personalizadas (Frequência, Localização e Distância).

O objetivo é demonstrar a construção de um sistema de busca completo, desde a coleta de dados (Web Scraping) até a geração de um ranking de resultados (Information Retrieval).

🚀 Estrutura do Projeto

O projeto é dividido em dois módulos principais que simulam um fluxo de trabalho em série:

1.  **`01_CrawlerAtualizado.py`**: Responsável pela coleta de dados, processamento e gravação no banco de dados.
2.  **`02_BuscaERanking.py`**: Responsável por receber a consulta, aplicar as métricas de ranqueamento e exibir o melhor resultado.

⚙️ Tecnologias e Dependências

  * **Python 3.x**
  * **MySQL** (para persistência dos dados indexados)
  * **`BeautifulSoup4`**: Para análise e *parsing* do HTML.
  * **`requests`**: Para fazer as requisições HTTP.
  * **`pymysql`**: Para conexão com o banco de dados MySQL.
  * **`nltk`**: Para processamento de linguagem natural (Stopwords e Stemming).

🗺️ Fluxo de Processo (BPMN)

Para garantir clareza na arquitetura, o fluxo de trabalho foi modelado usando a notação **BPMN (Business Process Model and Notation)**. Este diagrama representa o ciclo completo do sistema.

<img width="1083" height="440" alt="image" src="https://github.com/user-attachments/assets/1df7b19c-acd4-447c-9bba-d5a61242f60a" />

1\. Módulo de Indexação (`01_CrawlerAtualizado.py`)

Este script é responsável por visitar páginas, extrair texto e estruturar os dados para o ranqueamento.

# Explicação Detalhada das Funções

| Função | Propósito | Por que foi usada? |
| :--- | :--- | :--- |
| `abrirConexao()` | Estabelece a conexão com o banco de dados MySQL. | **Necessidade:** É a porta de entrada para a persistência dos dados. O `autocommit=True` garante que cada `INSERT` seja salvo imediatamente, ideal para o processo de indexação. |
| `limparBancoDeDados()` | Zera as tabelas de `palavras`, `urls` e `palavra_localizacao`. | **Necessidade:** Garante que cada nova execução do *crawler* comece com uma base de dados limpa, evitando duplicações e garantindo que o índice seja atualizado. O uso de `SET FOREIGN_KEY_CHECKS` permite zerar as tabelas na ordem correta, mesmo com chaves estrangeiras. |
| `paginaIndexada()`, `palavraIndexada()` | Checam a existência de uma URL ou palavra no banco de dados. | **Eficiência:** Previnem o re-processamento de páginas e garantem que as palavras só sejam inseridas uma vez, otimizando o espaço em disco. |
| `insertPagina()`, `insertPalavra()`, `insertPalavraLocalizacao()` | Inserem a URL, a palavra e a localização dela na página. | **Persistência:** São as funções CRUD (Create/Insert) que constroem o índice. O *Web Crawler* trabalha com o que é chamado de **Índice Invertido**, onde a localização da palavra (`i` em `enumerate(palavras)`) é crucial para o ranqueamento. |
| `getTexto(sopa)` | Remove elementos não-textuais (`<script>`, `<style>`) do HTML. | **Qualidade de Dados:** Essencial para limpar o texto de ruídos de código e garantir que apenas o conteúdo relevante seja processado e indexado, melhorando a precisão da busca. |
| `separaPalavras(texto)` | Tokeniza o texto, aplica *Stemming* e remove *Stopwords*. | **Processamento de Linguagem Natural (PLN):** *Stemming* (usando RSLPStemmer) reduz as palavras aos seus radicais (`programação` -\> `program`). A remoção de *Stopwords* (`e`, `o`, `de`) filtra palavras comuns e irrelevantes, tornando a busca mais eficiente e focada. |
| `indexador(conexao, url, sopa)` | Orquestra a extração e inserção de palavras no banco de dados. | **Controle:** É a função central que coordena `getTexto()`, `separaPalavras()`, e as funções de `insert` para uma única página, após verificar se a página já foi processada. |
| `crawl(conexao, paginas, profundidade)` | Implementa o algoritmo recursivo de Web Crawler. | **Core do Crawler:** A **recursão** (`crawl(..., profundidade - 1)`) permite que o *crawler* siga links em profundidade. O controle de `profundidade` garante que o processo tenha um limite e não varra a internet indefinidamente, sendo a lógica representada no *Gateway* do BPMN. |

2\. Módulo de Consulta e Ranqueamento (`02_BuscaERanking.py`)

Este script utiliza o índice criado para calcular a relevância de cada URL para a consulta do usuário.

# Explicação Detalhada das Funções de Ranqueamento

| Função | Propósito | Por que foi usada? |
| :--- | :--- | :--- |
| `getIdPalavra(conexao, palavra)` | Encontra o ID da palavra no índice, aplicando *Stemming* à palavra de busca. | **Consistência:** Garante que a palavra buscada (`programação`) seja comparada com o radical salvo no banco de dados (`program`), usando a mesma lógica de PLN do módulo de indexação. |
| `buscaMaisPalavras(conexao, consulta)` | Constrói e executa uma query SQL complexa (JOIN dinâmico). | **Eficiência na Busca:** Cria uma cláusula `JOIN` dinâmica para cada palavra da consulta. Isso garante que o sistema só retorne URLs que contenham **TODAS** as palavras de busca, otimizando o conjunto de resultados a serem ranqueados. |
| `frequenciaScore(linhas)` | Calcula o ranqueamento baseado na frequência da palavra na URL. | **Métrica de Relevância (Frequência):** Páginas onde as palavras de busca aparecem mais vezes são consideradas mais relevantes. |
| `localizacaoScore(linhas)` | Calcula o ranqueamento baseado na **soma das posições** das palavras na página. | **Métrica de Relevância (Localização):** Palavras que aparecem mais cedo no documento (menores valores de localização) são consideradas mais importantes. A soma total das localizações baixas resulta em uma pontuação melhor. |
| `distanciaScore(linhas)` | Calcula o ranqueamento baseado na distância entre as palavras-chave na página. | **Métrica de Relevância (Proximidade):** Se as palavras-chave (`Programação` e `Python`) estiverem muito próximas, o conteúdo é considerado mais focado e relevante. A menor distância entre elas resulta em um *score* maior. |
| `pesquisa(conexao, consulta, pesos)` | Orquestra as métricas e aplica os pesos definidos pelo usuário. | **Ranqueamento Final:** Combina as três pontuações (`frequencia`, `localizacao`, `distancia`), aplicando os pesos definidos. Isso permite ao usuário **personalizar a relevância** (ex: priorizar frequência com peso `2.0`, como feito no `if __name__ == '__main__':`). O resultado é uma pontuação única que define o ranking final. |

🛠️ Como Executar

1.  **Configurar o MySQL:** Crie o banco de dados `indice` e suas tabelas (`urls`, `palavras`, `palavra_localizacao`).
2.  **Instalar Dependências:**
    ```bash
    pip install beautifulsoup4 requests pymysql nltk lxml
    ```
3.  **Executar Indexação (Coleta de Dados):**
    ```bash
    python 01_CrawlerAtualizado.py
    ```
4.  **Executar Consulta (Ranqueamento):**
    ```bash
    python 02_BuscaERanking.py
    ```
