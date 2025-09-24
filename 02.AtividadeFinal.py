# Aluna: Gabriela Aparecida Tavares Corado Loreno.

import nltk
import pymysql

def abrirConexao():
    return pymysql.connect(host='localhost', user='root', passwd='ceub123456', db='indice', use_unicode=True, charset="utf8mb4")

def getIdPalavra(conexao, palavra):
    try:
        stemmer = nltk.stem.RSLPStemmer()
    except LookupError:
        nltk.download('rslp')
        stemmer = nltk.stem.RSLPStemmer()
    palavra_processada = stemmer.stem(palavra.lower())

    with conexao.cursor() as cursor:
        cursor.execute('select idpalavra from palavras where palavra = %s', palavra_processada)
        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
    return -1

def buscaMaisPalavras(conexao, consulta):
    with conexao.cursor() as cursor:
        listacampos = 'p1.idurl'
        listatabelas = ''
        listaclausulas = ''
        palavrasid = []
        
        palavras = consulta.split(' ')
        numerotabela = 1
        for palavra in palavras:
            idpalavra = getIdPalavra(conexao, palavra)
            if idpalavra > 0:
                palavrasid.append(idpalavra)
                if numerotabela > 1:
                    listatabelas += ', '
                    listaclausulas += ' and '
                    listaclausulas += 'p%d.idurl = p%d.idurl and ' % (numerotabela - 1, numerotabela)
                listacampos += ', p%d.localizacao' % numerotabela
                listatabelas += ' palavra_localizacao p%d' % numerotabela
                listaclausulas += 'p%d.idpalavra = %d' % (numerotabela, idpalavra)
                numerotabela += 1
        
        if not palavrasid:
            return [], []

        consultacompleta = 'SELECT %s FROM %s WHERE %s' % (listacampos, listatabelas, listaclausulas)
        cursor.execute(consultacompleta)
        linhas = [linha for linha in cursor]
        return linhas, palavrasid

def getUrl(conexao, idurl):
    with conexao.cursor() as cursor:
        cursor.execute('select url from urls where idurl = %s', idurl)
        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
    return ''

def frequenciaScore(linhas):
    contagem = dict([(linha[0], 0) for linha in linhas])
    for linha in linhas:
        contagem[linha[0]] += 1
    return contagem

def localizacaoScore(linhas):
    localizacoes = dict([linha[0], 1000000] for linha in linhas)
    for linha in linhas:
        soma = sum(linha[1:])
        if soma < localizacoes[linha[0]]:
            localizacoes[linha[0]] = soma
    return localizacoes

def distanciaScore(linhas):
    if len(linhas[0]) <= 2:
        return dict([(linha[0], 1.0) for linha in linhas]) 
    distancias = dict([(linha[0], 1000000) for linha in linhas])
    for linha in linhas:
        dist = sum([abs(linha[i] - linha[i - 1]) for i in range(2, len(linha))]) 
        if dist < distancias[linha[0]]: 
            distancias[linha[0]] = dist
    return distancias

def pesquisa(conexao, consulta, pesos):
    linhas, palavrasid = buscaMaisPalavras(conexao, consulta)
    
    if not linhas:
        print("Nenhuma das palavras foi encontrada nas páginas indexadas.")
        return

    PESO_FREQUENCIA = pesos.get('frequencia', 2.0)
    PESO_LOCALIZACAO = pesos.get('localizacao', 1.0)
    PESO_DISTANCIA = pesos.get('distancia', 0.5)

    scores_frequencia = frequenciaScore(linhas)
    scores_localizacao = localizacaoScore(linhas)
    scores_distancia = distanciaScore(linhas)

    pontuacao_final = dict()
    for idurl in scores_frequencia.keys():
        score_f = scores_frequencia.get(idurl, 0)
        score_l = 1.0 / (scores_localizacao.get(idurl, 100000) + 0.1)
        score_d = 1.0 / (scores_distancia.get(idurl, 100000) + 0.1)
        
        pontuacao = (score_f * PESO_FREQUENCIA) + (score_l * PESO_LOCALIZACAO) + (score_d * PESO_DISTANCIA)
        pontuacao_final[idurl] = pontuacao
        
    scores_ordenado = sorted(pontuacao_final.items(), key=lambda item: item[1], reverse=True)
    
    print("\n--- MELHOR RESULTADO ENCONTRADO ---")
    if scores_ordenado:
        id_vencedor, score_vencedor = scores_ordenado[0]
        print(f'Pontuação: {score_vencedor:.2f}\tURL: {getUrl(conexao, id_vencedor)}')
    else:
        print("Não foi possível calcular um ranking.")

if __name__ == '__main__':
    conexao_principal = abrirConexao()
    
    print('\n--- INICIANDO FASE DE CONSULTA ---')
    print('O banco de dados atual foi populado com a última URL que você pesquisou.')
    print('E as palavras que você gostaria de consultar foram Programação e Python.')

    consulta = f"{'Programacao'} {'Python'}"

    print("Pesos definidos por você: \n" 
          'Peso para frequência: 2.0 \n' 
          'Peso para Localização: 1.0 \n'
          'Peso para Distância: 0.5')
    peso_f = 2.0 #Coloquei um valor mais alto porque quero priorizar as páginas que mais repetem as palavras que coloquei.
    peso_l = 1.0 #Deixei esse como um valor mais abaixo, mas ainda é muito importante para a relevância.
    peso_d = 0.5 #A distância deixei mais baixo porque quero que a pesquisa me mostre o mais relevante conforme a frequência das palavras e a localização.
    
    pesos = {
        'frequencia': peso_f,
        'localizacao': peso_l,
        'distancia': peso_d
    }
    pesquisa(conexao_principal, consulta, pesos)
    
    conexao_principal.close()
    
    print('\nPrograma finalizado!!')