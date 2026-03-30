import pandas as pd
import mysql.connector
import requests
import json
import sys
import secrets
import os
from werkzeug.security import check_password_hash
from datetime import datetime, date
from gerar_numero_cotacao import gerar_nova_cotacao
from depurador_cob_adicional import executar_depurador_cobertura_adicional



from functools import wraps
from flask import Flask, session, request, redirect, render_template, jsonify, url_for, flash  

from configLocal import db_user, db_password, db_name, db_host, db_port

# Função de conexão com o MySQL
def get_mysql_connection():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        autocommit=True
    )

def buscar_fator(tabela, campo, valores, cobertura_id=None):
    """
    Busca registros em qualquer tabela e campo.
    Se 'valores' for uma lista, usa IN; se for um valor único, usa =.
    Filtra também pela maior NR_TARIFA da tabela.
    """
    conn = get_mysql_connection()

    # Cursor 1: buscar NR_TARIFA mais atual
    with conn.cursor(dictionary=True, buffered=True) as cur1:
        cur1.execute(f"SELECT MAX(NR_TARIFA) AS max_tarifa FROM {tabela}")
        max_tarifa_result = cur1.fetchone()
        if not max_tarifa_result or not max_tarifa_result["max_tarifa"]:
            conn.close()
            return []

        max_tarifa = max_tarifa_result["max_tarifa"]

    # Cursor 2: buscar os dados da tabela
    with conn.cursor(dictionary=True, buffered=True) as cur2:
        if isinstance(valores, list):
            if not valores:
                conn.close()
                return []
            placeholders = ', '.join(['%s'] * len(valores))
            query = f"SELECT * FROM {tabela} WHERE NR_TARIFA = %s AND {campo} IN ({placeholders})"
            params = [max_tarifa] + valores
            cur2.execute(query, params)
            resultados = cur2.fetchall()
        else:
            query = f"SELECT * FROM {tabela} WHERE NR_TARIFA = %s AND {campo} = %s"
            cur2.execute(query, (max_tarifa, valores))
            resultados = cur2.fetchone()

    conn.close()

    if cobertura_id and resultados:
        if isinstance(resultados, list):
            return [{
                k: v for k, v in item.items()
                if not k.startswith('FT_') or k == cobertura_id
            } for item in resultados]
        else:
            return {
                k: v for k, v in resultados.items()
                if not k.startswith('FT_') or k == cobertura_id
            }

    return resultados


# Importando Blueprints
from importTabelaFator import import_tabelas_bp
from versionTabelaFator import version_bp

app = Flask("motorRcTransporte", static_folder='static')
app.secret_key = secrets.token_urlsafe(24)  # Mesma chave usada no consulta_cotacao.py

# Registro dos blueprints
app.register_blueprint(import_tabelas_bp)
app.register_blueprint(version_bp)

###########################################################################################
# === DECORATOR DE AUTENTICAÇÃO ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/consulta/login')
        return f(*args, **kwargs)
    return decorated_function


###########################################################################################
# === ROTAS DE AUTENTICAÇÃO (consulta) ===
@app.route('/consulta/login', methods=['GET', 'POST'])
def consulta_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT username, password_hash, perfil FROM usuarios_consulta WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['logged_in'] = True
                session['perfil'] = user['perfil']  # Armazena o perfil na sessão
                #return redirect('/consulta/cotacoes')
                return redirect('/painel') 
            else:
                return render_template('login_cotacoes.html', error="Credenciais inválidas")
        
        except Exception as e:
            print(f"Erro: {str(e)}")
            return render_template('login_cotacoes.html', error="Erro no servidor")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login_cotacoes.html')
    

@app.route("/painel")
@login_required
def painel_controle():
    perfil = session.get("perfil", "consulta") 
    return render_template("painel_controle.html", perfil=perfil)


@app.route('/consulta/cotacoes')
@login_required
def view_cotacoes():
    return render_template('consulta_cotacoes.html')

@app.route('/consulta/logout')
def consulta_logout():
    session.pop('logged_in', None)
    return redirect('/consulta/login')


###########################################################################################
# === ROTA PARA EXCLUIR VERSIONAMENTO DA TABELA RELATIVIDADE NO BD  ===
@app.route('/excluir_versao', methods=['POST'])
def excluir_versao():
    nome_tabela = request.form['nome_tabela']
    nr_tarifa = request.form['nr_tarifa']

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        query = f"DELETE FROM {nome_tabela} WHERE NR_TARIFA = %s"
        cursor.execute(query, (nr_tarifa,))
        conn.commit()

        flash(f"Versão NR_TARIFA {nr_tarifa} da tabela {nome_tabela} excluída com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('version.versao_tabelas'))


###########################################################################################
# === ROTAS DE CONSULTA ===
@app.route('/consulta/api/cotacoes', methods=['POST'])
@login_required
def api_get_cotacoes():
    num_cotacao = request.form.get('numero_cotacao')
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                numero_cotacao,
                versao_cotacao,
                premio_total,
                data_criacao,
                dados_json
            FROM cotacoes_armazenadas
            WHERE numero_cotacao = %s
            ORDER BY versao_cotacao DESC
        """, (num_cotacao,))
        
        results = cursor.fetchall()
        return jsonify({"success": True, "data": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

###########################################################################################
# Rota para criar uma nova cotação
@app.route('/criar_cotacao', methods=['POST'])
def criar_cotacao():
    numero_nova_cotacao = gerar_nova_cotacao()
    #print("JSON retornado:", numero_nova_cotacao)
    return jsonify(numero_nova_cotacao)

###########################################################################################
# Rota para consultar cotação existente
@app.route('/consultar')
def redirect_consulta():
    """Redireciona para o sistema de consulta (agora na mesma porta)"""
    return redirect('/consulta/login', code=302)


###########################################################################################
# Página Principal
@app.route("/", methods=["GET", "POST"])
def index():
    cnpj = ""
    erro_cnpj = ""
    dados = {}

    if request.method == "POST":
        cnpj = request.form.get("cnpj")
        if not cnpj:
            erro_cnpj = "CNPJ não informado"
        else:
            dados = consulta_cnpj(cnpj)
            if dados.get("status") == "ERRO":
                erro_cnpj = dados.get("mensagem", "Erro na consulta")
                dados = {}

    return render_template("index.html",
                           cnpj=cnpj,
                           erro_cnpj=erro_cnpj,
                           nome=dados.get("nome", ""),
                           situacao=dados.get("situacao", ""),
                           porte=dados.get("porte", ""),
                           logradouro=dados.get("logradouro", ""),
                           numero=dados.get("numero", ""),
                           municipio=dados.get("municipio", ""),
                           bairro=dados.get("bairro", ""),
                           uf=dados.get("uf", ""),
                           cep=dados.get("cep", ""),
                           email=dados.get("email", ""),
                           telefone=dados.get("telefone", ""),
                           status=dados.get("status", ""))

# API externa da ReceitaWS para buscar dados do CNPJ
@app.route("/api/cnpj/<cnpj>")
def api_cnpj(cnpj):
    return jsonify(consulta_cnpj(cnpj))

def consulta_cnpj(cnpj):
    cnpj = ''.join(filter(str.isdigit, cnpj))
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    response = requests.get(url)

    if response.status_code == 200:
        try:
            dados = response.json()
            if "nome" in dados:
                return dados
            else:
                return {"status": "ERRO", "mensagem": "CNPJ não encontrado ou inválido"}
        except ValueError:
            return {"status": "ERRO", "mensagem": "Erro ao processar a resposta"}
    else:
        return {"status": "ERRO", "mensagem": "Erro na consulta ao CNPJ"}

# Página de upload das tabelas de fatores
@app.route("/tabelas")
def page_tabelas():
    return render_template("upload_tabelas.html")

# Retorna descrições de coberturas conforme grupo
@app.route("/api/cobertura_exibir/<codigo>")
def get_cobertura_exibir(codigo):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    # CAG1 → coberturas básicas
    if codigo == "CAG1":
        cursor.execute("""
            SELECT * FROM CA_COBERTURA 
            WHERE CD_GRUPO_COBERTURA = 1 
            AND CD_COBERTURA <> 'CAG1'
        """)

    # CA1, CA2, CA3... → adicionais
    elif codigo in ("CA1","CA2","CA3","CA4","CA5"):
        cursor.execute("""
            SELECT * FROM CA_COBERTURA 
            WHERE CD_GRUPO_COBERTURA = 2
        """)

    else:
        cursor.close()
        conn.close()
        return jsonify([])

    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(resultado)



################################################################################################################################################################################
################################################################################################################################################################################
# ROTA PARA BUSCAR AS RELATIVIDADES NO MYSQL
# Processa o formulário de Precificação TODAS AS RESPOSTA TEM ESTAS NA FUNÇÃO ABAIXO
@app.route("/calcular_precificacao", methods=["POST"])
def calcular_precificacao():

    # Dados do Segurado Principal
    cnpj = request.form.get("cnpj")
    nome = request.form.get("nome")
    situacao = request.form.get("situacao")
    porte = request.form.get("porte")
    logradouro = request.form.get("logradouro")
    numero = request.form.get("numero")
    municipio = request.form.get("municipio")
    bairro = request.form.get("bairro")
    uf = request.form.get("uf")
    cep = request.form.get("cep")
    email = request.form.get("email")
    telefone = request.form.get("telefone")
    status = request.form.get("status")

    # ============================================================
    # EMPRESAS DO GRUPO - # Demais Empresas do Grupo — manter exatamente estes nomes
    # ============================================================
    grupo_emp_cnpjs = request.form.getlist("grupo_emp_cnpj[]")
    grupo_emp_nomes = request.form.getlist("grupo_emp_nome[]")
    grupo_emp_participacoes = request.form.getlist("grupo_emp_participacao[]")

    empresas_grupo = []
    for cnpj_grupo, nome_grupo, participacao in zip(grupo_emp_cnpjs, grupo_emp_nomes, grupo_emp_participacoes):
        if cnpj_grupo or nome_grupo or participacao:
            empresas_grupo.append({
                "cnpj": cnpj_grupo,
                "nome": nome_grupo,
                "participacao": participacao
            })

    # ============================================================
    # COBERTURAS BÁSICAS
    # ============================================================
    cobertura_id = request.form.get("ft_cobertura")
    cobertura_id = f"FT_{cobertura_id}" if cobertura_id else ""

    # VALOR BASAL - a FT_COBERTURA pode conter 1 ou mais coberturas ex: "CAG1, C1, C2....."
    # FT_COBERTURA pode conter 1 ou mais coberturas ex: "CAG1, C1, C2..."
    coberturas_form = request.form.get("ft_cobertura")
    coberturas = [c.strip() for c in coberturas_form.split(",") if c.strip()]
    colunas_premio = [f"PR_{c}" for c in coberturas]  # ["PR_CAG1", "PR_C1", "PR_C2"]

    linha_premio = buscar_fator("PR_PREMIO", "CD_SEGMENTO", 1) #Buscar a linha de prêmios base (APENAS DO CD_SEGMENTO = 1)

    # Busca valores de cada cobertura
    valores_basais = {}
    for coluna in colunas_premio:
        valor_basal = linha_premio.get(coluna)
        valores_basais[coluna] = valor_basal


    # ============================================================
    # COBERTURAS ADICIONAIS (NOVO BLOCO)
    # ============================================================
    cob_adicionais_json = request.form.getlist("coberturas_adicionais[]")
    coberturas_adicionais = []

    # 1) Converte cada item JSON vindo do front
    for item in cob_adicionais_json:
        try:
            coberturas_adicionais.append(json.loads(item))
        except:
            pass

    adicionais_result = []
    
    if coberturas_adicionais:

        # 2) CONSULTA MY SQL – busca descrições
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        codigos = [c["codigo"] for c in coberturas_adicionais]

        sql = f"""
            SELECT CD_COBERTURA, DS_COBERTURA
            FROM CA_COBERTURA
            WHERE CD_COBERTURA IN ({",".join(['%s']*len(codigos))})
        """
        cursor.execute(sql, codigos)
        adicionais_result = cursor.fetchall()

        cursor.close()
        conn.close()

        # 3) BUSCA LINHA DE PRÊMIO DA TABELA PR_PREMIO
        linha_premio = buscar_fator("PR_PREMIO", "CD_SEGMENTO", 1)

        # 4) INCLUI PREMIO E LMI EM CADA ITEM
        for linha in adicionais_result:
            codigo = linha["CD_COBERTURA"]                 # CA1
            coluna_premio = f"PR_{codigo}"                 # PR_CA1

            premio = linha_premio.get(coluna_premio, None)
            linha["PREMIO"] = premio

            # adiciona LMI informado no front
            for ad in coberturas_adicionais:
                if ad["codigo"] == codigo:
                    linha["LMI"] = ad.get("lmi")
                    break

    # ============================================================
    # CORRETOR
    # ============================================================
    # Recupera o campo 'corretor' como string e faz o parsing para dict
    corretor_json = request.form.get("corretor")

    # Transforma a string JSON em dicionário
    if corretor_json:
        dados_corretor = json.loads(corretor_json)
        comissao = dados_corretor.get("corretor_comissao")

        try:
            # Converte para float, divide por 100, soma 1 → 20 → 1.20
            relatividade_comissao = 1 + float(comissao) / 100
        except (TypeError, ValueError):
            # Se vier vazio, nulo ou não numérico → assume 1.00
            relatividade_comissao = 1.00

        corretor = {
            "corretor_codigo": dados_corretor.get("corretor_codigo"),
            "corretor_nome": dados_corretor.get("corretor_nome"),
            "corretor_comissao": comissao,
            "corretor_contato": dados_corretor.get("corretor_contato"),
            "corretor_telefone": dados_corretor.get("corretor_telefone"),
            "corretor_fator": round(relatividade_comissao, 6)
        } #OBS A RELATIVIADE DE COMISSÃO ESTÁ AQUI PEGANDO DIRETO DA COMISSÃO DIGITADA NÃO ESTÁ CONSULTANDO TABELA

    #CANAL
    ft_canal = request.form.get("ft_canal")
    canal = buscar_fator("FT_CANAL", "CD_CANAL", ft_canal, cobertura_id)

    #TOP 5 PRODUTOS
    produtos_top5 = request.form.getlist("produto_top5[]")

    #EMBARQUE
    ft_prodperig = request.form.get("ft_prodperig")
    prodperig = buscar_fator("FT_PRODPERIG", "CD_PRODPERIG", ft_prodperig, cobertura_id)
    

    # ============================================================
    # QTDE EMBARQUE - buscando fator diretamente via BETWEEN incluso dia 21/11/25
    # ============================================================
    ft_qtde_embarque = request.form.get("ft_qtde_embarque")
    qtde_embarque = None
    if ft_qtde_embarque and cobertura_id:
        ft_qtde_embarque = float(ft_qtde_embarque)
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Monta a coluna dinamicamente, ex: FT_CAG1
        coluna_fator = cobertura_id  # cobertura_id já está no formato FT_CAG1

        # NOVA QUERY trazendo DS_QTDEMBARQUE
        query = f"""
            SELECT `{coluna_fator}`, DS_QTDEMBARQUE
            FROM FT_QTDE_EMBARQUE
            WHERE %s BETWEEN CD_QTDEMBARQUE_INI AND CD_QTDEMBARQUE_FIM
            LIMIT 1
        """
        cursor.execute(query, (ft_qtde_embarque,))
        resultado = cursor.fetchone()
        if resultado:
            qtde_embarque = {
                "DS_QTDEMBARQUE": resultado["DS_QTDEMBARQUE"],
                cobertura_id: resultado[coluna_fator]
            }

        cursor.close()
        conn.close()

    # ============================================================
    # LMI - buscando fator diretamente via faixa incluso dia 21/11/25
    # ============================================================
    ft_isagrupcobertura = request.form.get("ft_isagrupcobertura")
    isagrupcobertura = {}

    if ft_isagrupcobertura and cobertura_id:

        # Converte "1.234,56" → 1234.56
        ft_isagrupcobertura = ft_isagrupcobertura.replace(".", "").replace(",", ".")

        try:
            ft_isagrupcobertura = float(ft_isagrupcobertura)
        except ValueError:
            ft_isagrupcobertura = None

        if ft_isagrupcobertura is not None:

            # Conecta ao MySQL
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            coluna_fator = cobertura_id  # Ex: FT_CAG1

            # Query usando BETWEEN correto para faixas float
            query = f"""
                SELECT `{coluna_fator}`, DS_LMI, CD_LMI_INI, CD_LMI_FIM
                FROM FT_ISAGRUPCOBETURA
                WHERE CD_LMI_INI <= %s AND CD_LMI_FIM >= %s
                LIMIT 1
            """

            print("VALOR LMI PARA BUSCA:", ft_isagrupcobertura)

            cursor.execute(query, (ft_isagrupcobertura, ft_isagrupcobertura))
            resultado = cursor.fetchone()
            
            if resultado:
                isagrupcobertura = {
                    "DS_LMI": resultado.get("DS_LMI"),
                    cobertura_id: resultado.get(coluna_fator)
                }

            cursor.close()
            conn.close()

    #ACONDICIONAMENTO
    ft_acondic_granel = request.form.get("ft_acondicionamento_granel")
    ft_acondicionamento_granel = buscar_fator("FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO", ft_acondic_granel, cobertura_id)

    ft_acondic_fracional = request.form.get("ft_acondicionamento_fracionado")
    ft_acondicionamento_fracionado = buscar_fator("FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO", ft_acondic_fracional, cobertura_id)
    
    #PERFIL DO MOTORISTA
    qtd_frota_transportadora = request.form.get("qtd_frota_transportadora")
    qtd_frota_agregado = request.form.get("qtd_frota_agregado")
    qtd_frota_propria = request.form.get("qtd_frota_propria")
    qtd_frota_autonomo = request.form.get("qtd_frota_autonomo")
    perfil_motorista = request.form.getlist("perfil_motorista[]")
    
    relatividades_motorista = []
    for codigo in perfil_motorista:
        resultado = buscar_fator("FT_PERFMOTORISTA", "CD_PERFMOTORISTA", codigo, cobertura_id)
        if resultado:
            relatividades_motorista.append(resultado)

    #CERTIFICAÇÕES 
    cd_certificao_1 = request.form.get("cd_certificao_1")
    cd_certificao_2 = request.form.get("cd_certificao_2")
    cd_certificao_3 = request.form.get("cd_certificao_3")
    cd_certificao_4 = request.form.get("cd_certificao_4")
    cd_certificao_5 = request.form.get("cd_certificao_5")

    certificacoes = []
    for i, valor in enumerate([
        cd_certificao_1,
        cd_certificao_2,
        cd_certificao_3,
        cd_certificao_4,
        cd_certificao_5
    ], start=1):
        if valor:
            resultado = buscar_fator("FT_CERTIFICACAO", "CD_TEMCERTIFICACAO", valor, cobertura_id)
            if resultado:
                certificacoes.append({"certificacao": f"cd_certificao_{i}", **resultado})

    #TIPO DE SEGURO 
    tipos_seguro = request.form.getlist("tipo_seguro[]")
    tipos_seguro_detalhes = []
    for codigo in tipos_seguro:
        resultado = buscar_fator("FT_TIPSEGURO", "CD_TIPSEGURO", codigo, cobertura_id)
        if resultado:
            tipos_seguro_detalhes.append(resultado)

    #MODAIS UTILIZADO 
    modais_utilizado = request.form.getlist("modais_utilizado[]")
    ft_modais = buscar_fator("FT_MODAIS", "CD_MODAIS", modais_utilizado, cobertura_id)

    #ATIVIDADE
    atividade = request.form.getlist("atividade[]")
    ft_atividade = buscar_fator("FT_ATIVIDADE", "CD_ATIVIDADE", atividade, cobertura_id)

    # CLASSIFICAÇÃO DOS PRODUTOS - CLASSE
    classes = json.loads(request.form.get("classes", "{}"))
    porcentagens = json.loads(request.form.get("porcentagens", "{}"))

    ft_classe = {}
    for codigo in classes:
        porcentagem = porcentagens.get(codigo, "0")
        info = buscar_fator("FT_CLASSEPRODUTO", "CD_CLASSEPRODUTO", codigo, cobertura_id)
        ft_classe[f"classe_{codigo}"] = {
        "relatividade": info,
        f"porcentagem_classe_{codigo}": porcentagem
    }
   
   # UF 
    ufs = json.loads(request.form.get("ufs", "[]"))
    ft_uf = {}

    for codigo in ufs:
        info = buscar_fator("FT_UF", "CD_UF", codigo, cobertura_id)
        ft_uf[f"uf_{codigo}"] = info

    nova_cotacao = gerar_nova_cotacao()

    # Busca fatores de carregamento
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], cobertura_id)


   ################################################################################################################
   # CRIA JSON COM AS RELATIVIDADES
    resposta_json = {
        "cotacao": nova_cotacao,
        "valores_basal_cobertura": valores_basais,
           
        "dados_segurado": {
            "cnpj": cnpj,
            "nome": nome,
            "situacao": situacao,
            "porte": porte,
            "endereco": f"{logradouro}, {numero} - {bairro}, {municipio} - {uf}, {cep}",
            "email": email,
            "telefone": telefone,
            "status": status
        },
        "empresas_grupo": empresas_grupo,
        "cobertura_id": cobertura_id,
        
        #"coberturas_adicionais" : adicionais_result,

        "canal": canal,
        "produtos_top5": produtos_top5,
        "prodperig": prodperig,

        "qtde_embarque": qtde_embarque or {},          # garante dicionário
       "isagrupcobertura": isagrupcobertura or {},    # garante dicionário

        "ft_acondicionamento_granel": ft_acondicionamento_granel,
        "ft_acondicionamento_fracionado": ft_acondicionamento_fracionado,
        "certificacoes": certificacoes,
        "tipos_seguro": tipos_seguro_detalhes,
        "ft_modais": ft_modais,
        "ft_atividade": ft_atividade,
        "ft_classe": ft_classe,
        "ft_uf": ft_uf,
        "corretor": corretor,
        "ft_carregamento": carregamentos, 
        
        "perfil_motorista": {
            "quantidade_frota": {
                "transportadora": qtd_frota_transportadora,
                "agregado": qtd_frota_agregado,
                "frota_propria": qtd_frota_propria,
                "autonomo": qtd_frota_autonomo
            },
            
            "relatividades": relatividades_motorista  # lista de dicionários
        }
    }

    ################################################################################################################
    # DEPURADOR COBERTURA BASICA
    def adicionar_linha(fonte, pergunta, resposta, relatividade, valor_corrente_premio, linhas, premio="", numero_cotacao=None, versao_cotacao=None, data_criacao_cotacao=None):
        if isinstance(relatividade, (float, int)):
            valor_corrente_premio *= relatividade
            premio = round(valor_corrente_premio, 4)

        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": fonte,
            "pergunta": pergunta,
            "resposta": resposta,
            "relatividade": f"{relatividade:.5f}" if isinstance(relatividade, (float, int)) else relatividade,
            "premio": premio
        })
        return valor_corrente_premio, linhas

    cotacao_info = resposta_json.get("cotacao", {})
    numero_cotacao = cotacao_info.get("numero_cotacao")
    versao = cotacao_info.get("versao")
    data_criacao = cotacao_info.get("data_criacao")

    # Inicializa a lista de linhas antes de qualquer uso
    linhas = []

    # COBERTURA SELECIONADA
    cobertura_id = resposta_json.get("cobertura_id")
    cobertura_suffix = cobertura_id.replace("FT_", "") if cobertura_id else ""
    valor_premio = resposta_json.get("valores_basal_cobertura", {}).get(f"PR_{cobertura_suffix}", "")
    valor_corrente_premio = float(valor_premio)

    valor_corrente_premio, linhas = adicionar_linha("basal", "cobertura", cobertura_id, "", valor_corrente_premio, linhas,
        premio=round(valor_premio, 4), numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR CERTIFICAÇÕES
    for i, cert in enumerate(resposta_json.get("certificacoes", []), start=1):
        valor_corrente_premio, linhas = adicionar_linha(
            f"certificacao_{i}", cert.get("DS_CERTIFICACAO"), cert.get("DS_TEMCERTIFICACAO"), cert.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR ACONDICIONAMENTO
    for key in ["ft_acondicionamento_granel", "ft_acondicionamento_fracionado"]:
        bloco = resposta_json.get(key, {})
        if bloco:
            valor_corrente_premio, linhas = adicionar_linha(
                key, bloco.get("DS_ACONDICIONAMENTO"), bloco.get("DS_FAIXA_ACONDICIONAMENTO"), bloco.get(cobertura_id),
                valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR CANAL
    bloco = resposta_json.get("canal", {})
    if bloco:
        valor_corrente_premio, linhas = adicionar_linha("canal", bloco.get("CANAL"), bloco.get("DS_CANAL"), bloco.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR MODAIS
    for i, modal in enumerate(resposta_json.get("ft_modais", []), start=1):
        valor_corrente_premio, linhas = adicionar_linha(
            f"modal_{i}", "Tipo de modais", modal.get("DS_MODAIS"), modal.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR ATIVIDADE
    for i, atividade in enumerate(resposta_json.get("ft_atividade", []), start=1):
        valor_corrente_premio, linhas = adicionar_linha(
            f"atividade_{i}", "Tipo de Atividade", atividade.get("DS_ATIVIDADE"), atividade.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # EMBARQUE: PRODUTO PERIGOSO?
    bloco = resposta_json.get("prodperig", {})
    valor_corrente_premio, linhas = adicionar_linha(
        "Embarque_1", "Produto Perigoso?", bloco.get("CD_PRODPERIG"), bloco.get(cobertura_id),
        valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)
            
    # EMBARQUE: QUANTIDADE DE EMBARQUE
    bloco = resposta_json.get("qtde_embarque", {})
    valor_corrente_premio, linhas = adicionar_linha(
        "Embarque_2", "Quantidade de Embarque", bloco.get("DS_QTDEMBARQUE"), bloco.get(cobertura_id),
        valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # EMBARQUE: LMI
    bloco = resposta_json.get("isagrupcobertura", {})
    valor_corrente_premio, linhas = adicionar_linha(
        "Embarque_3", "LMI", bloco.get("DS_LMI"), bloco.get(cobertura_id),
        valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)


    # FATOR PERFIL DO MOTORISTA
    for i, item in enumerate(resposta_json.get("perfil_motorista", {}).get("relatividades", []), start=1):
        valor_corrente_premio, linhas = adicionar_linha(
            f"Perfil_motorista_{i}", "Perfil do Motorista", item.get("DS_PERFMOTORISTA"), item.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR TIPO DE SEGURO
    for i, item in enumerate(resposta_json.get("tipos_seguro", []), start=1):
        valor_corrente_premio, linhas = adicionar_linha(
            f"Tipo de Seguro_{i}", "Tipo de Seguro", item.get("DS_TIPSEGURO"), item.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR CLASSE
    for chave, dados in resposta_json.get("ft_classe", {}).items():
        classe_info = dados.get("relatividade", {})
        valor_corrente_premio, linhas = adicionar_linha(
            chave, "Classe do Produto", classe_info.get("DS_CLASSEPRODUTO"), classe_info.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # FATOR UF
    for chave, uf_info in resposta_json.get("ft_uf", {}).items():
        valor_corrente_premio, linhas = adicionar_linha(
            chave, "UF", uf_info.get("DS_UF"), uf_info.get(cobertura_id),
            valor_corrente_premio, linhas, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao)

    # Linha de Prêmio de Risco até UF
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    #####################################################################################################################
    #BLOCO 1 CARREGAMENTO: 1-Inflação de Sinistro, 2-Tendências Estatística e 3-IBNR
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [1, 2, 3])
    for item in carregamentos:
        valor_corrente_premio, linhas = adicionar_linha(
            "Carregamento",
            f"Carreg. {item['CD_CARREGAMENTO']}",  # Pergunta simplificada
            item["DS_CARREGAMENTO"],  # Resposta completa (ex: "Inflação de Sinistro")
            item.get(cobertura_id),
            valor_corrente_premio,
            linhas,
            numero_cotacao=numero_cotacao,
            versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )
    # Linha de Prêmio de Risco até FATOR CARREGAMENTO | códigos 1-Inflação de Sinistro, 2-Tendências Estatística e 3-IBNR
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    #####################################################################################################################
    #BLOCO 2 CARREGAMENTO: 4-Salvados, 5-Ressarcimento e 6-Sinistro Judicial
    # ATENÇÃO OS CODIGOS 4-SALVADO e 5-RESSARCIMENTO ENTRAM COMO DESCONTO, por ser um valor recuperação.
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [4, 5, 6])
    for item in carregamentos:
        valor_corrente_premio, linhas = adicionar_linha(
            "Carregamento",
            f"Carreg. {item['CD_CARREGAMENTO']}",  # Pergunta simplificada
            item["DS_CARREGAMENTO"],  # Resposta completa (ex: "Inflação de Sinistro")
            item.get(cobertura_id),
            valor_corrente_premio,
            linhas,
            numero_cotacao=numero_cotacao,
            versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )
    # Linha de Prêmio de Risco até FATOR CARREGAMENTO | códigos 4-Salvados, 5-Ressarcimento e 6-Sinistro Judicial
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    #####################################################################################################################
    #BLOCO 3 CARREGAMENTO: 7-Carregamento de Segurança
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [7])
    for item in carregamentos:
        valor_corrente_premio, linhas = adicionar_linha(
            "Carregamento",
            f"Carreg. {item['CD_CARREGAMENTO']}",  # Pergunta simplificada
            item["DS_CARREGAMENTO"],  # Resposta completa (ex: "Inflação de Sinistro")
            item.get(cobertura_id),
            valor_corrente_premio,
            linhas,
            numero_cotacao=numero_cotacao,
            versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )
    # Linha de Prêmio Puro com o FATOR CARREGAMENTO | códigos 7-Carregamento de Segurança
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio Puro", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    #####################################################################################################################
    #BLOCO 4 CARREGAMENTO: COMISSÃO CORRETOR + 8-Despesas Operacionais, 9-Despesas Administrativas, 10-Impostos, 11-Lucro
    corretor = resposta_json.get("corretor", {})
    valor_corrente_premio, linhas = adicionar_linha(
        "Corretor",
        "Comissão do Corretor",
        f"{corretor.get('corretor_comissao', '')}%",  # Ex: "20%"
        corretor.get("corretor_fator", 1.0),  # Fator (ex: 1.2)
        valor_corrente_premio,
        linhas,
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao
    )
    #8-Despesas Operacionais, 9-Despesas Administrativas, 10-Impostos, 11-Lucro
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [8, 9, 10, 11])
    for item in carregamentos:
        valor_corrente_premio, linhas = adicionar_linha(
            "Carregamento",
            f"Carreg. {item['CD_CARREGAMENTO']}",  # Pergunta simplificada
            item["DS_CARREGAMENTO"],  # Resposta completa (ex: "Inflação de Sinistro")
            item.get(cobertura_id),
            valor_corrente_premio,
            linhas,
            numero_cotacao=numero_cotacao,
            versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )
    # Linha de Prêmio de Risco até FATOR CARREGAMENTO | códigos 8-Despesas Operacionais, 9-Despesas Administrativas, 10-Impostos, 11-Lucro
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio Líquido", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    #####################################################################################################################
    # BLOCO 5 - ABERTURA DO PRÊMIO LIQUIDO POR PESO DE COBERTURA
    # 1. Buscar dados das coberturas C1-80%, C2-20%  na tabela CA_COBERTURA via buscar_fator
    coberturas_desejadas = ['C1', 'C2', 'C3']
    dados_coberturas = buscar_fator("CA_COBERTURA", "CD_COBERTURA", coberturas_desejadas)

    # 2. Iterar pelas coberturas e calcular o prêmio proporcional
    if dados_coberturas:
        for item in dados_coberturas:
            codigo = item.get('CD_COBERTURA')
            descricao = item.get('DS_COBERTURA', '')
            peso = item.get('COBERTURA_PESO', 0)

            if isinstance(peso, (float, int)) and peso > 0:
                premio_proporcional = round(valor_corrente_premio * peso, 4)

                # 3. Adicionar linha com a cobertura proporcional
                _, linhas = adicionar_linha(
                fonte="Prêmio Líquido",
                pergunta="Cobertura",
                resposta=descricao,
                relatividade=peso,
                valor_corrente_premio=valor_corrente_premio,
                linhas=linhas,
                premio=premio_proporcional,
                numero_cotacao=numero_cotacao,
                versao_cotacao=versao,
                data_criacao_cotacao=data_criacao
            )

    #####################################################################################################################
    # BLOCO 6 CARREGAMENTO: 12-IOF
    carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [12])
    for item in carregamentos:
        valor_corrente_premio, linhas = adicionar_linha(
            "Carregamento",
            f"Carreg. {item['CD_CARREGAMENTO']}",  # Pergunta simplificada
            item["DS_CARREGAMENTO"],  # Resposta completa (ex: "Inflação de Sinistro")
            item.get(cobertura_id),
            valor_corrente_premio,
            linhas,
            numero_cotacao=numero_cotacao,
            versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )
    # Linha de Prêmio de Risco até FATOR CARREGAMENTO | 12-IOF
    valor_corrente_premio, linhas = adicionar_linha(
        "Prêmio Total", "", "", "", valor_corrente_premio, linhas,
        premio=round(valor_corrente_premio, 4), 
        numero_cotacao=numero_cotacao,
        versao_cotacao=versao,
        data_criacao_cotacao=data_criacao)

    # DADOS DA COTAÇÃO
    depurador_final = pd.DataFrame(linhas)
    depurador_final = depurador_final[["numero_cotacao", "versao_cotacao", "data_criacao_cotacao","fonte", "pergunta", "resposta", "relatividade", "premio"]]

    #with open("static/depurador_linhas.json", "w", encoding="utf-8") as f:
    #    json.dump(depurador_final.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    print(depurador_final.to_string(index=False), file=sys.stdout)

    
    # ============================================================
    # DEPURADOR - COBERTURAS ADICIONAIS (ISOLADO)
    # ============================================================
    depurador_cob_add_result = executar_depurador_cobertura_adicional(resposta_json)

    # Extrai o DataFrame de dentro do dict
    depurador_cob_add_df = pd.DataFrame(depurador_cob_add_result.get("depurador_df", []))

    # JSON das coberturas adicionais
    coberturas_adicionais_json = depurador_cob_add_result.get("coberturas_adicionais", [])

    # Mostrar depurador
    if not depurador_cob_add_df.empty:
        print("\n" + "="*120)
        print("DEPURADOR - COBERTURAS ADICIONAIS")
        print("="*120)
        print(depurador_cob_add_df.to_string(index=False), file=sys.stdout)
    else:
        print("\nDEPURADOR - COBERTURAS ADICIONAIS: sem dados", file=sys.stdout)


    # ---------------------------------------------------------------
    # NOVO CÓDIGO ADICIONADO (sem quebrar o fluxo existente)
    # ---------------------------------------------------------------
    dados_depurador = depurador_final.to_dict(orient='records')
    
    # Salva os detalhes do depurador no MySQL (Para Gravar Informações do Depurador para gravar o Historico e ter)
    numero = dados_depurador[0]["numero_cotacao"]
    versao = dados_depurador[0]["versao_cotacao"]
    data_criacao = dados_depurador[0]["data_criacao_cotacao"]
    salvar_detalhes_depurador(numero, versao, data_criacao, dados_depurador)

    # Unificar os JSONs
    resultado_final = {
        "metadata": {
            "status": "sucesso",
            "timestamp": datetime.now().isoformat()
        },
        "dados_cotacao": resposta_json,      # cobertura básica
        "detalhes_calculo": dados_depurador, # depurador básico
        "coberturas_adicionais": coberturas_adicionais_json,  # NOVO Coberturas Adicionais
        "resumo": {
            "premio_total": valor_corrente_premio,
            "cobertura_principal": cobertura_id
        }
    }

    # Unificar os JSONs
    resposta_unificada = {
        "dados_principais": resposta_json,
        "detalhes_depurador": depurador_final.to_dict(orient="records"),
        "coberturas_adicionais": coberturas_adicionais_json  # 👈 NOVO
    }
    # Salvar no banco de dados
    salvar_cotacao_completa(resposta_unificada)

    return jsonify(resultado_final)

# ===============================================
# Rota para exibir o depurador no navegador
@app.route("/depurador")
def mostrar_depurador():
    return render_template("depurador.html", linhas=[], cotacao_data={})

# ===============================================
# Rota para buscar as informações no mysql
@app.route("/consulta/api/depurador", methods=["POST"])
def consultar_depurador_por_numero():
    numero = request.form.get("numero_cotacao")
    if not numero:
        return jsonify({"error": "Número da cotação não informado"}), 400

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT detalhes_depurador FROM depurador
        WHERE numero_cotacao = %s
        ORDER BY data_registro DESC
        LIMIT 1
        """
        cursor.execute(query, (numero,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": f"Cotação {numero} não encontrada"}), 404

        detalhes = json.loads(row["detalhes_depurador"])
        return jsonify({"linhas": detalhes})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ===============================================
# Salva as Informações apenas do depurador para consultar Historico na Tela
def salvar_detalhes_depurador(numero, versao, data_criacao, detalhes_depurador):
    conn = None
    cursor = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()

        # Calcular o prêmio total: último valor do JSON
        premio_total = None
        if detalhes_depurador:
            ultimo = detalhes_depurador[-1]
            premio_total = float(ultimo.get('premio', 0))

        insert_query = """
            INSERT INTO depurador (
                numero_cotacao, versao_cotacao, data_criacao,
                detalhes_depurador, premio_total
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            numero,
            versao,
            data_criacao,
            json.dumps(detalhes_depurador, ensure_ascii=False),
            premio_total
        ))

        conn.commit()
        print(f"✅ Cotação {numero}-{versao} salva em depurador.")
        return True

    except Exception as e:
        print(f"❌ Erro ao salvar cotação JSON: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ===============================================
# Função para gravar cotação no banco de dados
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
    
def salvar_cotacao_completa(resposta_unificada):
    conn = None
    cursor = None
    
    try:
        # Extrair informações básicas da cotação
        cotacao_info = resposta_unificada['dados_principais']['cotacao']
        numero_cotacao = cotacao_info['numero_cotacao']
        versao_cotacao = (
                    cotacao_info.get('versao_cotacao')
                    or cotacao_info.get('versao')
                )
        
        data_criacao = cotacao_info['data_criacao']
        
        # Converter para formato JSON string
        json_str = json.dumps(resposta_unificada,
                              ensure_ascii=False,
                              indent=2,
                              cls=DateTimeEncoder)
        
        # Calcular prêmio total (busca o último valor do depurador)
        premio_total = None
        if resposta_unificada.get('detalhes_depurador'):
            ultimo_item = resposta_unificada['detalhes_depurador'][-1]
            premio_total = float(ultimo_item.get('premio', 0))
        
        
        # Obter conexão
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Query de inserção
        insert_query = """
        INSERT INTO cotacoes_armazenadas 
        (numero_cotacao, versao_cotacao, data_criacao, dados_json, premio_total)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        # Executar a inserção
        cursor.execute(insert_query, (
            numero_cotacao,
            versao_cotacao,
            data_criacao,
            json_str,
            premio_total
        ))
        
        conn.commit()
        print(f"Cotação {numero_cotacao}-{versao_cotacao} salva com sucesso no banco de dados.")
        return True
        
    except Exception as e:
        print(f"Erro ao salvar cotação no banco de dados: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


##################################################################################################
# Rota para obter a última cotação armazenada e mostrar os valor na tela principal
@app.route('/api/ultima_cotacao', methods=['GET'])
def ultima_cotacao():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    # Substitua "tabela_cotacoes" pelo nome real da sua tabela
    cursor.execute("""
        SELECT * FROM cotacoes_armazenadas
        ORDER BY numero_cotacao DESC, versao_cotacao DESC
        LIMIT 1
    """)
    cotacao = cursor.fetchone()

    cursor.close()
    conn.close()

    if cotacao:
        return jsonify(cotacao)
    else:
        return jsonify({}), 200


##################################################################################################
# Função para duplicar cotação, alterar a versão e o prêmio
@app.route('/consulta/duplicar_cotacao', methods=['POST'])
def duplicar_cotacao():
    data = request.get_json()

    resposta_unificada = data.get('dados_json')
    ajustes_recebidos = data.get('ajustes_recebidos')

    if not resposta_unificada or not ajustes_recebidos:
        return jsonify({
            'success': False,
            'message': 'Dados incompletos'
        }), 400

    resultado = duplicar_cotacao_com_agravo(
        resposta_unificada,
        ajustes_recebidos
    )

    if resultado:
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'message': 'Erro ao duplicar cotação'
        }), 500



##################################################################################################
#fiz alterações aqui nesta parte 27/12/25
def duplicar_cotacao_com_agravo(resposta_unificada, ajustes_recebidos):
    conn = None
    cursor = None

    try:
        if isinstance(resposta_unificada, str):
            resposta_unificada = json.loads(resposta_unificada)

        # 🔹 Cópia profunda segura
        nova_cotacao = json.loads(json.dumps(resposta_unificada))

        numero_cotacao = nova_cotacao['dados_principais']['cotacao']['numero_cotacao']

        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT MAX(versao_cotacao) AS ultima_versao
            FROM cotacoes_armazenadas
            WHERE numero_cotacao = %s
        """, (numero_cotacao,))

        resultado = cursor.fetchone()
        ultima_versao = resultado['ultima_versao'] or '00'
        nova_versao = str(int(ultima_versao) + 1).zfill(2)

        # 🔹 Atualiza dados principais (CORRIGIDO)
        cotacao_info = nova_cotacao['dados_principais']['cotacao']
        cotacao_info['versao'] = nova_versao          # 👈 FRONT / JSON
        cotacao_info['versao_cotacao'] = nova_versao
        cotacao_info['data_criacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # --------------------------------------------------
        # 🔹 Normalização dos ajustes
        # --------------------------------------------------
        ajustes = {}

        if isinstance(ajustes_recebidos, (int, float)):
            for item in nova_cotacao['detalhes_depurador']:
                if item.get('fonte') == 'Prêmio Líquido' and item.get('pergunta') == 'Cobertura':
                    ajustes[item['resposta']] = float(ajustes_recebidos)

        elif isinstance(ajustes_recebidos, list):
            ajustes = {
                a['cobertura']: float(a['agravo_percentual'])
                for a in ajustes_recebidos
                if isinstance(a, dict)
                and 'cobertura' in a
                and 'agravo_percentual' in a
            }
        else:
            raise ValueError('Formato inválido de ajustes_recebidos')

        if not ajustes:
            raise ValueError('Nenhum ajuste válido recebido')

        # --------------------------------------------------
        # 🔹 Normalização dos ajustes - Coberturas Adicionais
        # --------------------------------------------------
        ajustes_adicionais = {}

        if isinstance(ajustes_recebidos, list):
            for a in ajustes_recebidos:
                if (
                    isinstance(a, dict)
                    and a.get('tipo') == 'adicional'
                    and 'codigo_cobertura' in a
                    and 'agravo_percentual' in a
                ):
                    ajustes_adicionais[a['codigo_cobertura']] = float(a['agravo_percentual'])


        # --------------------------------------------------
        # 🔹 Histórico
        # --------------------------------------------------
        nova_cotacao.setdefault('historico_alteracoes', [])

        # --------------------------------------------------
        # 🔹 Atualização do prêmio por cobertura BÁSICA
        # --------------------------------------------------
        for item in nova_cotacao['detalhes_depurador']:

            if item.get('fonte') != 'Prêmio Líquido' or item.get('pergunta') != 'Cobertura':
                continue

            nome = item.get('resposta')

            if nome not in ajustes:
                continue

            premio_base = float(item.get('premio', 0))
            agravo = ajustes[nome]

            premio_novo = round(premio_base * (1 + agravo / 100), 2)

            item['premio'] = premio_novo

            nova_cotacao['historico_alteracoes'].append({
                'data': datetime.now().isoformat(),
                'cobertura': nome,
                'tipo': 'agravo' if agravo >= 0 else 'desconto',
                'percentual': agravo,
                'premio_anterior': premio_base,
                'premio_novo': premio_novo,
                'versao_origem': ultima_versao
            })

        # --------------------------------------------------
        # 🔹 Atualização do prêmio por cobertura ADICIONAIS
        # --------------------------------------------------
        for adicional in nova_cotacao.get('coberturas_adicionais', []):

            codigo = adicional.get('codigo_cobertura')

            if codigo not in ajustes_adicionais:
                continue

            premio_base = float(adicional.get('premio_total', 0))
            agravo = ajustes_adicionais[codigo]

            premio_novo = round(premio_base * (1 + agravo / 100), 2)

            adicional['premio_total'] = premio_novo

            nova_cotacao['historico_alteracoes'].append({
                'data': datetime.now().isoformat(),
                'tipo': 'agravo' if agravo >= 0 else 'desconto',
                'cobertura': codigo,
                'descricao': adicional.get('descricao_cobertura'),
                'percentual': agravo,
                'premio_anterior': premio_base,
                'premio_novo': premio_novo,
                'versao_origem': ultima_versao
            })


        # --------------------------------------------------
        # 🔹 RECOMPOSIÇÃO DO PRÊMIO TOTAL (OBRIGATÓRIA)
        # --------------------------------------------------
        total_basicas = sum(
            float(item['premio'])
            for item in nova_cotacao['detalhes_depurador']
            if item.get('fonte') == 'Prêmio Líquido'
            and item.get('pergunta') == 'Cobertura'
        )

        total_adicionais = sum(
            float(adicional.get('premio_total', 0))
            for adicional in nova_cotacao.get('coberturas_adicionais', [])
        )

        total_coberturas = round(total_basicas + total_adicionais, 2)

        premio_total_encontrado = False

        for item in nova_cotacao['detalhes_depurador']:
            if item.get('fonte') == 'Prêmio Total':
                item['premio'] = round(total_coberturas, 2)
                premio_total_encontrado = True

        if not premio_total_encontrado:
            nova_cotacao['detalhes_depurador'].append({
                'fonte': 'Prêmio Total',
                'pergunta': 'Prêmio Total',
                'resposta': 'Total',
                'premio': round(total_coberturas, 2)
            })

        # --------------------------------------------------
        # ✅ Salva no MySQL
        # --------------------------------------------------
        return salvar_cotacao_completa(nova_cotacao)

    except Exception as e:
        print(f"Erro ao duplicar cotação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



##############################################################################
# CONFIGURAÇÃO DO SERVIDOR
##############################################################################
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )