from bs4 import BeautifulSoup
import requests
import re
import nltk
import pymysql

def abrirConexao():
    return pymysql.connect(host='localhost', user='root', passwd='*', db='indice', autocommit = True, use_unicode=True, charset="utf8mb4")

def limparBancoDeDados(conexao):
    print("--- Limpando o banco de dados para a nova indexação ---")
    with conexao.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE palavra_localizacao;")
        cursor.execute("TRUNCATE TABLE palavras;")
        cursor.execute("TRUNCATE TABLE urls;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Banco de dados limpo com sucesso!")

def paginaIndexada(conexao, url):
    with conexao.cursor() as cursor:
        cursor.execute('SELECT idurl FROM urls WHERE url = %s', url)
        if cursor.rowcount > 0:
            return cursor.fetchone()[0] 
    return -1 

def insertPagina(conexao, url):
    with conexao.cursor() as cursor:
        cursor.execute("INSERT INTO urls (url) VALUES (%s)", url)
        return cursor.lastrowid

def palavraIndexada(conexao, palavra):
    with conexao.cursor() as cursor:
        cursor.execute('select idpalavra from palavras where palavra = %s', palavra)
        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
    return -1

def insertPalavra(conexao, palavra):
    with conexao.cursor() as cursor:
        cursor.execute("INSERT INTO palavras (palavra) VALUES (%s)", palavra)
        return cursor.lastrowid

def insertPalavraLocalizacao(conexao, idurl, idpalavra, localizacao):
    with conexao.cursor() as cursor:
        cursor.execute("INSERT INTO palavra_localizacao (idurl, idpalavra, localizacao) VALUES (%s, %s, %s)", (idurl, idpalavra, localizacao))

def getTexto(sopa):
    for tags in sopa(['script', 'style']):
        tags.decompose()
    return ' '.join(sopa.stripped_strings)

def separaPalavras(texto):
    try:
        stop = nltk.corpus.stopwords.words('portuguese')
        stemmer = nltk.stem.RSLPStemmer()
    except LookupError:
        print("Recursos do NLTK não encontrados. Baixando agora...")
        nltk.download('stopwords')
        nltk.download('rslp')
        stop = nltk.corpus.stopwords.words('portuguese')
        stemmer = nltk.stem.RSLPStemmer()

    splitter = re.compile('\\W+')
    lista_palavras = []
    lista = [p for p in splitter.split(texto) if p != '']
    for p in lista:
        palavra_processada = stemmer.stem(p.lower())
        if palavra_processada not in stop and len(p) > 1:
            lista_palavras.append(palavra_processada)
    return lista_palavras

def indexador(conexao, url, sopa):
    idpagina = paginaIndexada(conexao, url)
    if idpagina != -1:
        print("URL já indexada, pulando: " + url)
        return
    
    idpagina = insertPagina(conexao, url)
    print('Indexando o conteúdo de: ' + url)
    texto = getTexto(sopa)
    palavras = separaPalavras(texto)
    for i, palavra in enumerate(palavras):
        idpalavra = palavraIndexada(conexao, palavra)
        if idpalavra == -1:
            idpalavra = insertPalavra(conexao, palavra)
        insertPalavraLocalizacao(conexao, idpagina, idpalavra, i)

def crawl(conexao, paginas, profundidade):
    if profundidade < 0:
        return

    print(f'\n--- INICIANDO CRAWL NA PROFUNDIDADE {profundidade} PARA {len(paginas)} PÁGINAS ---')
    novas_paginas = set()
    for pagina in paginas:
        try:
            dados_pagina = requests.get(pagina, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        except Exception as e:
            print(f'Erro ao abrir a página {pagina}: {e}')
            continue
        
        if dados_pagina.status_code != 200:
            print(f'Página {pagina} retornou status {dados_pagina.status_code}. Pulando.')
            continue

        sopa = BeautifulSoup(dados_pagina.text, "lxml")
        indexador(conexao, pagina, sopa)

        links = sopa.find_all('a')
        for link in links:
            if 'href' in link.attrs:
                url = link.get('href')
                if url is None or url.strip() == "" or url.startswith('#') or url.startswith('mailto:'):
                    continue

                from urllib.parse import urljoin
                url_completa = urljoin(pagina, url)
                if url_completa.startswith('http'):
                    novas_paginas.add(url_completa)
    
    if profundidade > 0 and novas_paginas:
        crawl(conexao, list(novas_paginas), profundidade - 1)

if __name__ == '__main__':
    conexao_principal = abrirConexao()
    limparBancoDeDados(conexao_principal)
    listapaginas = ['https://www.alura.com.br/']
    crawl(conexao_principal, listapaginas, 1)
    conexao_principal.close()
    print('\n--- FASE DE INDEXAÇÃO FINALIZADA! ---')
