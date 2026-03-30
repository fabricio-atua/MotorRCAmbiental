# motorRcTransporte.py
import json
import sys
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import pandas as pd

# suponho que você já tenha as funções abaixo definidas em outro lugar do projeto:
# - get_mysql_connection()
# - buscar_fator(tabela, chave, valor, coluna_opcional=None)
# - gerar_nova_cotacao()
# - salvar_detalhes_depurador(numero, versao, data_criacao, detalhes)
# - salvar_cotacao_completa(resposta_unificada)
# Ajuste imports/paths conforme sua estrutura real.

app = Flask(__name__)

# ---------------------------
# Função utilitária de depurador (reutilizável por cobertura)
# ---------------------------
def adicionar_linha(fonte, pergunta, resposta, relatividade, valor_corrente_premio, linhas,
                    premio="", numero_cotacao=None, versao_cotacao=None, data_criacao_cotacao=None):
    """
    Aplica a relatividade (quando for numérica) e adiciona uma linha no depurador.
    Retorna (valor_corrente_premio_atualizado, linhas)
    """
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

# ---------------------------
# Função que calcula o depurador para UMA cobertura (básica ou adicional)
# ---------------------------
def calcular_depurador_por_cobertura(prefix_cobertura, premio_basal, contexto, numero_cotacao, versao, data_criacao):
    """
    prefix_cobertura: ex: 'FT_CAG1' para cobertura básica, 'FT_CA1' para adicional CA1
    premio_basal: valor numérico do prêmio básico (PR_CAG1 ou PR_CA1)
    contexto: dicionário com todos os blocos já buscados pelo motor (canal, certificacoes, ft_acondicionamento_granel, ...)
    Retorna: (lista_de_linhas_dep, premio_final)
    """
    linhas_local = []
    valor_corrente = float(premio_basal) if premio_basal is not None else 0.0

    # 1) linha basal
    valor_corrente, linhas_local = adicionar_linha(
        "basal", "cobertura", prefix_cobertura.replace("FT_", ""), "",
        valor_corrente, linhas_local, premio=round(valor_corrente, 4),
        numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 2) certificações
    for i, cert in enumerate(contexto.get("certificacoes", []), start=1):
        fator = cert.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            f"certificacao_{i}", cert.get("DS_CERTIFICACAO"), cert.get("DS_TEMCERTIFICACAO"),
            fator, valor_corrente, linhas_local,
            numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
        )

    # 3) acondicionamentos (granel + fracionado)
    for key in ["ft_acondicionamento_granel", "ft_acondicionamento_fracionado"]:
        bloco = contexto.get(key, {})
        if bloco:
            fator = bloco.get(prefix_cobertura)
            valor_corrente, linhas_local = adicionar_linha(
                key, bloco.get("DS_ACONDICIONAMENTO") or bloco.get("DS_ACONDICIONAMENTO"),
                bloco.get("DS_FAIXA_ACONDICIONAMENTO") or bloco.get("DS_FAIXA_ACONDICIONAMENTO"),
                fator, valor_corrente, linhas_local,
                numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
            )

    # 4) canal
    canal = contexto.get("canal", {})
    if canal:
        fator = canal.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "canal", canal.get("CANAL"), canal.get("DS_CANAL"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 5) modais
    for i, modal in enumerate(contexto.get("ft_modais", []), start=1):
        fator = modal.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            f"modal_{i}", "Tipo de modais", modal.get("DS_MODAIS"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 6) atividade
    for i, atividade in enumerate(contexto.get("ft_atividade", []), start=1):
        fator = atividade.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            f"atividade_{i}", "Tipo de Atividade", atividade.get("DS_ATIVIDADE"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 7) embarque: produto perigoso
    prodperig = contexto.get("prodperig", {})
    valor_corrente, linhas_local = adicionar_linha(
        "Embarque_1", "Produto Perigoso?", prodperig.get("CD_PRODPERIG"), prodperig.get(prefix_cobertura),
        valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 8) embarque: qtde embarque
    qtde_emb = contexto.get("qtde_embarque", {})
    valor_corrente, linhas_local = adicionar_linha(
        "Embarque_2", "Quantidade de Embarque", qtde_emb.get("DS_QTDEMBARQUE"), qtde_emb.get(prefix_cobertura),
        valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 9) embarque: LMI (IMPORTANTE: LMI pode ser diferente para cada cobertura — contexto deve ter sido populado antes)
    isagrup = contexto.get("isagrupcobertura", {})
    # isagrupcobertura for specific coverage must be in contexto like: contexto["isagrupcobertura_by_coverage"] = { "FT_CA1": {...}, ... }
    isagrup_map = contexto.get("isagrupcobertura_by_coverage", {})
    isagrup_coverage = isagrup_map.get(prefix_cobertura, {}) or isagrup
    valor_corrente, linhas_local = adicionar_linha(
        "Embarque_3", "LMI", isagrup_coverage.get("DS_LMI"), isagrup_coverage.get(prefix_cobertura),
        valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 10) perfil motorista
    for i, item in enumerate(contexto.get("perfil_motorista", {}).get("relatividades", []), start=1):
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            f"Perfil_motorista_{i}", "Perfil do Motorista", item.get("DS_PERFMOTORISTA"),
            fator, valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 11) tipo de seguro
    for i, item in enumerate(contexto.get("tipos_seguro", []), start=1):
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            f"Tipo de Seguro_{i}", "Tipo de Seguro", item.get("DS_TIPSEGURO"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 12) classe
    for chave, dados in contexto.get("ft_classe", {}).items():
        classe_info = dados.get("relatividade", {})
        fator = classe_info.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            chave, "Classe do Produto", classe_info.get("DS_CLASSEPRODUTO"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 13) UF
    for chave, uf_info in contexto.get("ft_uf", {}).items():
        fator = uf_info.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            chave, "UF", uf_info.get("DS_UF"), fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    # 14) Linha de Prêmio de Risco
    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao, versao_cotacao=versao,
        data_criacao_cotacao=data_criacao
    )

    # 15) carregamentos blocos 1-3
    carregamentos_1 = contexto.get("carregamentos_block_1", [])
    for item in carregamentos_1:
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "Carregamento", f"Carreg. {item['CD_CARREGAMENTO']}", item["DS_CARREGAMENTO"], fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao, versao_cotacao=versao,
        data_criacao_cotacao=data_criacao
    )

    # 16) carregamentos blocos 4-6
    carregamentos_2 = contexto.get("carregamentos_block_2", [])
    for item in carregamentos_2:
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "Carregamento", f"Carreg. {item['CD_CARREGAMENTO']}", item["DS_CARREGAMENTO"], fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio de Risco", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao, versao_cotacao=versao,
        data_criacao_cotacao=data_criacao
    )

    # 17) carregamento 7 (segurança)
    carregamentos_3 = contexto.get("carregamentos_block_3", [])
    for item in carregamentos_3:
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "Carregamento", f"Carreg. {item['CD_CARREGAMENTO']}", item["DS_CARREGAMENTO"], fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio Puro", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao, versao_cotacao=versao,
        data_criacao_cotacao=data_criacao
    )

    # 18) corretor (comissão)
    corretor = contexto.get("corretor", {})
    fator_corretor = corretor.get("corretor_fator", 1.0)
    valor_corrente, linhas_local = adicionar_linha(
        "Corretor", "Comissão do Corretor", f"{corretor.get('corretor_comissao', '')}%",
        fator_corretor, valor_corrente, linhas_local, numero_cotacao=numero_cotacao,
        versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 19) carregamentos 8-11 (operacionais/admin/impostos/lucro)
    carregamentos_4 = contexto.get("carregamentos_block_4", [])
    for item in carregamentos_4:
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "Carregamento", f"Carreg. {item['CD_CARREGAMENTO']}", item["DS_CARREGAMENTO"], fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio Líquido", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao,
        versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # 20) carregamento 12 (IOF)
    carregamentos_5 = contexto.get("carregamentos_block_5", [])
    for item in carregamentos_5:
        fator = item.get(prefix_cobertura)
        valor_corrente, linhas_local = adicionar_linha(
            "Carregamento", f"Carreg. {item['CD_CARREGAMENTO']}", item["DS_CARREGAMENTO"], fator,
            valor_corrente, linhas_local, numero_cotacao=numero_cotacao, versao_cotacao=versao,
            data_criacao_cotacao=data_criacao
        )

    valor_corrente, linhas_local = adicionar_linha(
        "Prêmio Total", "", "", "", valor_corrente, linhas_local,
        premio=round(valor_corrente, 4), numero_cotacao=numero_cotacao,
        versao_cotacao=versao, data_criacao_cotacao=data_criacao
    )

    # Retorna o bloco de linhas e o prêmio final desta cobertura
    return linhas_local, round(valor_corrente, 4)

# ---------------------------
# Endpoint principal (versão atualizada)
# ---------------------------
@app.route("/calcular_precificacao", methods=["POST"])
def calcular_precificacao():
    # --- captura dados do formulário (mantive seu código original) ---
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

    # COBERTURAS BÁSICAS
    cobertura_id = request.form.get("ft_cobertura")
    cobertura_id = f"FT_{cobertura_id}" if cobertura_id else ""

    coberturas_form = request.form.get("ft_cobertura")
    coberturas = [c.strip() for c in coberturas_form.split(",") if c.strip()]
    colunas_premio = [f"PR_{c}" for c in coberturas]

    linha_premio = buscar_fator("PR_PREMIO", "CD_SEGMENTO", 1)

    valores_basais = {}
    for coluna in colunas_premio:
        valor_basal = linha_premio.get(coluna)
        valores_basais[coluna] = valor_basal

    # -------------------------
    # COBERTURAS ADICIONAIS: ler JSON e buscar descrição
    # -------------------------
    cob_adicionais_json = request.form.getlist("coberturas_adicionais[]")
    coberturas_adicionais = []
    for item in cob_adicionais_json:
        try:
            coberturas_adicionais.append(json.loads(item))
        except:
            pass

    adicionais_result = []
    if coberturas_adicionais:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        codigos = [c["codigo"] for c in coberturas_adicionais]
        sql = f"""
            SELECT CD_COBERTURA, DS_COBERTURA, COBERTURA_PESO
            FROM CA_COBERTURA
            WHERE CD_COBERTURA IN ({",".join(['%s']*len(codigos))})
        """
        cursor.execute(sql, codigos)
        adicionais_result = cursor.fetchall()
        cursor.close()
        conn.close()

    # -------------------------
    # CORRETOR
    # -------------------------
    corretor_json = request.form.get("corretor")
    corretor = {}
    if corretor_json:
        dados_corretor = json.loads(corretor_json)
        comissao = dados_corretor.get("corretor_comissao")
        try:
            relatividade_comissao = 1 + float(comissao) / 100
        except (TypeError, ValueError):
            relatividade_comissao = 1.00
        corretor = {
            "corretor_codigo": dados_corretor.get("corretor_codigo"),
            "corretor_nome": dados_corretor.get("corretor_nome"),
            "corretor_comissao": comissao,
            "corretor_contato": dados_corretor.get("corretor_contato"),
            "corretor_telefone": dados_corretor.get("corretor_telefone"),
            "corretor_fator": round(relatividade_comissao, 6)
        }

    # CANAL
    ft_canal = request.form.get("ft_canal")
    canal = buscar_fator("FT_CANAL", "CD_CANAL", ft_canal, cobertura_id)

    # TOP5 / EMBARQUE / ETC.
    produtos_top5 = request.form.getlist("produto_top5[]")
    ft_prodperig = request.form.get("ft_prodperig")
    prodperig = buscar_fator("FT_PRODPERIG", "CD_PRODPERIG", ft_prodperig, cobertura_id)

    # QTDE EMBARQUE - mantive seu método
    ft_qtde_embarque = request.form.get("ft_qtde_embarque")
    qtde_embarque = None
    if ft_qtde_embarque and cobertura_id:
        try:
            ft_qtde_embarque_f = float(ft_qtde_embarque)
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            coluna_fator = cobertura_id
            query = f"""
                SELECT `{coluna_fator}`, DS_QTDEMBARQUE
                FROM FT_QTDE_EMBARQUE
                WHERE %s BETWEEN CD_QTDEMBARQUE_INI AND CD_QTDEMBARQUE_FIM
                LIMIT 1
            """
            cursor.execute(query, (ft_qtde_embarque_f,))
            resultado = cursor.fetchone()
            if resultado:
                qtde_embarque = {
                    "DS_QTDEMBARQUE": resultado["DS_QTDEMBARQUE"],
                    cobertura_id: resultado[coluna_fator]
                }
            cursor.close()
            conn.close()
        except:
            qtde_embarque = None

    # LMI da cobertura básica (por faixa)
    ft_isagrupcobertura = request.form.get("ft_isagrupcobertura")
    isagrupcobertura = {}
    if ft_isagrupcobertura and cobertura_id:
        ft_isagrupcobertura_val = ft_isagrupcobertura.replace(".", "").replace(",", ".")
        try:
            ft_isagrupcobertura_val = float(ft_isagrupcobertura_val)
        except ValueError:
            ft_isagrupcobertura_val = None

        if ft_isagrupcobertura_val is not None:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            coluna_fator = cobertura_id
            query = f"""
                SELECT `{coluna_fator}`, DS_LMI, CD_LMI_INI, CD_LMI_FIM
                FROM FT_ISAGRUPCOBETURA
                WHERE CD_LMI_INI <= %s AND CD_LMI_FIM >= %s
                LIMIT 1
            """
            cursor.execute(query, (ft_isagrupcobertura_val, ft_isagrupcobertura_val))
            resultado = cursor.fetchone()
            if resultado:
                isagrupcobertura = {
                    "DS_LMI": resultado.get("DS_LMI"),
                    cobertura_id: resultado.get(coluna_fator)
                }
            cursor.close()
            conn.close()

    # ACONDICIONAMENTO
    ft_acondic_granel = request.form.get("ft_acondicionamento_granel")
    ft_acondicionamento_granel = buscar_fator("FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO", ft_acondic_granel, cobertura_id)
    ft_acondic_fracional = request.form.get("ft_acondicionamento_fracionado")
    ft_acondicionamento_fracionado = buscar_fator("FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO", ft_acondic_fracional, cobertura_id)

    # PERFIL MOTORISTA
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

    # CERTIFICAÇÕES
    cds_cert = [request.form.get(f"cd_certificao_{i}") for i in range(1,6)]
    certificacoes = []
    for i, valor in enumerate(cds_cert, start=1):
        if valor:
            resultado = buscar_fator("FT_CERTIFICACAO", "CD_TEMCERTIFICACAO", valor, cobertura_id)
            if resultado:
                certificacoes.append({"certificacao": f"cd_certificao_{i}", **resultado})

    # TIPOS SEGURO
    tipos_seguro = request.form.getlist("tipo_seguro[]")
    tipos_seguro_detalhes = []
    for codigo in tipos_seguro:
        resultado = buscar_fator("FT_TIPSEGURO", "CD_TIPSEGURO", codigo, cobertura_id)
        if resultado:
            tipos_seguro_detalhes.append(resultado)

    # MODAIS
    modais_utilizado = request.form.getlist("modais_utilizado[]")
    ft_modais = buscar_fator("FT_MODAIS", "CD_MODAIS", modais_utilizado, cobertura_id)

    # ATIVIDADE
    atividade = request.form.getlist("atividade[]")
    ft_atividade = buscar_fator("FT_ATIVIDADE", "CD_ATIVIDADE", atividade, cobertura_id)

    # CLASSE
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

    # Carregamentos: vamos buscar em blocos para reaproveitar no depurador por cobertura
    carregamentos_all = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [1,2,3,4,5,6,7,8,9,10,11,12], cobertura_id)
    # separar por blocos conforme seu depurador original
    carregamentos_block_1 = [c for c in carregamentos_all if c['CD_CARREGAMENTO'] in (1,2,3)]
    carregamentos_block_2 = [c for c in carregamentos_all if c['CD_CARREGAMENTO'] in (4,5,6)]
    carregamentos_block_3 = [c for c in carregamentos_all if c['CD_CARREGAMENTO'] in (7,)]
    carregamentos_block_4 = [c for c in carregamentos_all if c['CD_CARREGAMENTO'] in (8,9,10,11)]
    carregamentos_block_5 = [c for c in carregamentos_all if c['CD_CARREGAMENTO'] in (12,)]

    # Monta contexto compartilhado que será passado ao calculador por cobertura
    contexto = {
        "canal": canal,
        "certificacoes": certificacoes,
        "ft_acondicionamento_granel": ft_acondicionamento_granel,
        "ft_acondicionamento_fracionado": ft_acondicionamento_fracionado,
        "ft_modais": ft_modais,
        "ft_atividade": ft_atividade,
        "prodperig": prodperig,
        "qtde_embarque": qtde_embarque or {},
        # isagrupcobertura_by_coverage: preenchido abaixo para cada adicional
        "isagrupcobertura": isagrupcobertura,
        "perfil_motorista": {"relatividades": relatividades_motorista},
        "tipos_seguro": tipos_seguro_detalhes,
        "ft_classe": ft_classe,
        "ft_uf": ft_uf,
        "corretor": corretor,
        "carregamentos_block_1": carregamentos_block_1,
        "carregamentos_block_2": carregamentos_block_2,
        "carregamentos_block_3": carregamentos_block_3,
        "carregamentos_block_4": carregamentos_block_4,
        "carregamentos_block_5": carregamentos_block_5
    }

    # -------------------------------------------------------------------------
    # Depurador da cobertura básica (fluxo original)
    # -------------------------------------------------------------------------
    linhas = []

    # Dados para depurador básico: número/versão/data
    numero_cotacao = nova_cotacao.get("numero_cotacao")
    versao = nova_cotacao.get("versao")
    data_criacao = nova_cotacao.get("data_criacao")

    # pega o prêmio basal da tabela PR_PREMIO conforme já feito
    cobertura_suffix = cobertura_id.replace("FT_", "") if cobertura_id else ""
    premio_basal_coberta = valores_basais.get(f"PR_{cobertura_suffix}", 0.0)

    # Reaproveito a função geral para calcular o depurador da cobertura básica
    linhas_basica, premio_final_basica = calcular_depurador_por_cobertura(
        prefix_cobertura=cobertura_id,
        premio_basal=premio_basal_coberta,
        contexto=contexto,
        numero_cotacao=numero_cotacao,
        versao=versao,
        data_criacao=data_criacao
    )

    # append das linhas básicas
    linhas.extend(linhas_basica)

    # -------------------------------------------------------------------------
    # Depurador das coberturas adicionais (uma passada por cobertura selecionada)
    # -------------------------------------------------------------------------
    lista_coberturas_adicionais = []
    detalhes_adicionais_all = []
    # Mapeamento para LMI por cobertura (string como veio do front)
    lmi_usuario_map = {c["codigo"]: c.get("lmi") for c in coberturas_adicionais}

    if adicionais_result:
        # Buscar PR_PREMIO linha completa (já tinha sido buscada antes no seu código original)
        pr_premio = buscar_fator("PR_PREMIO", "CD_SEGMENTO", 1)

        # Para cada cobertura adicional encontrada em CA_COBERTURA
        for cob in adicionais_result:
            cd = cob.get("CD_COBERTURA")
            ds = cob.get("DS_COBERTURA")

            # premio basal desta cobertura (PR_CA1, PR_CA2...)
            coluna_pr = f"PR_{cd}"
            premio_basal_ad = pr_premio.get(coluna_pr, 0.0)

            # Prepara contexto específico para LMI desta cobertura adicional:
            # converte LMI informado pelo usuário e busca faixa em FT_ISAGRUPCOBETURA para a coluna FT_{CD}
            lmi_raw = lmi_usuario_map.get(cd, "") or ""
            isagrup_specific = {}
            if lmi_raw:
                lmi_val = lmi_raw.replace(".", "").replace(",", ".")
                try:
                    lmi_val = float(lmi_val)
                except:
                    lmi_val = None
                if lmi_val is not None:
                    conn = get_mysql_connection()
                    cursor = conn.cursor(dictionary=True)
                    coluna_fator = f"FT_{cd}"
                    query = f"""
                        SELECT `{coluna_fator}`, DS_LMI, CD_LMI_INI, CD_LMI_FIM
                        FROM FT_ISAGRUPCOBETURA
                        WHERE CD_LMI_INI <= %s AND CD_LMI_FIM >= %s
                        LIMIT 1
                    """
                    cursor.execute(query, (lmi_val, lmi_val))
                    res = cursor.fetchone()
                    if res:
                        isagrup_specific = {
                            "DS_LMI": res.get("DS_LMI"),
                            coluna_fator: res.get(coluna_fator)
                        }
                    cursor.close()
                    conn.close()

            # adiciona esse isagrup específico no contexto
            contexto_local = contexto.copy()
            # injeta mapa de isagrup por coverage para o depurador
            contexto_local["isagrupcobertura_by_coverage"] = { f"FT_{cd}": isagrup_specific }
            # também mantenho isagrupcobertura padrão (caso necessário)
            contexto_local["isagrupcobertura"] = isagrup_specific or contexto.get("isagrupcobertura", {})

            # Para todos os fatores que dependem de coluna FT_XXXX, o buscar_fator já retornou objetos
            # contendo chaves como 'FT_CAG1' e 'FT_CA1' (ou seja, contexto contém os blocos com todas colunas).
            # A função calcular_depurador_por_cobertura irá usar prefix_cobertura='FT_CA1' para buscar os campos corretos.

            prefix_field = f"FT_{cd}"

            # gera as linhas de depurador e prêmio final para esta cobertura adicional
            linhas_adicional, premio_final_adicional = calcular_depurador_por_cobertura(
                prefix_cobertura=prefix_field,
                premio_basal=premio_basal_ad,
                contexto=contexto_local,
                numero_cotacao=numero_cotacao,
                versao=versao,
                data_criacao=data_criacao
            )

            # inclui informações resumidas desta cobertura na lista de adicionais
            lista_coberturas_adicionais.append({
                "CD_COBERTURA": cd,
                "DS_COBERTURA": ds,
                "LMI": lmi_raw,
                "PREMIO_BASAL": premio_basal_ad,
                "PREMIO_FINAL": premio_final_adicional
            })

            # adiciona as linhas deste adicional ao depurador geral (mas mantendo bloco separado por fonte)
            linhas.append({
                "numero_cotacao": numero_cotacao,
                "versao_cotacao": versao,
                "data_criacao_cotacao": data_criacao,
                "fonte": f"--- INICIO ADICIONAL {cd} ---",
                "pergunta": "",
                "resposta": "",
                "relatividade": "",
                "premio": ""
            })
            linhas.extend(linhas_adicional)
            linhas.append({
                "numero_cotacao": numero_cotacao,
                "versao_cotacao": versao,
                "data_criacao_cotacao": data_criacao,
                "fonte": f"--- FIM ADICIONAL {cd} ---",
                "pergunta": "",
                "resposta": "",
                "relatividade": "",
                "premio": premio_final_adicional
            })

            # detalhes para retorno/salvamento
            detalhes_adicionais_all.extend(linhas_adicional)

    # -------------------------------------------------------------------------
    # Monta resposta_json (mantendo sua estrutura)
    # -------------------------------------------------------------------------
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
        "canal": canal,
        "produtos_top5": produtos_top5,
        "prodperig": prodperig,
        "qtde_embarque": qtde_embarque or {},
        "isagrupcobertura": isagrupcobertura or {},
        "ft_acondicionamento_granel": ft_acondicionamento_granel,
        "ft_acondicionamento_fracionado": ft_acondicionamento_fracionado,
        "certificacoes": certificacoes,
        "tipos_seguro": tipos_seguro_detalhes,
        "ft_modais": ft_modais,
        "ft_atividade": ft_atividade,
        "ft_classe": ft_classe,
        "ft_uf": ft_uf,
        "corretor": corretor,
        "ft_carregamento": carregamentos_all,
        "perfil_motorista": {
            "quantidade_frota": {
                "transportadora": qtd_frota_transportadora,
                "agregado": qtd_frota_agregado,
                "frota_propria": qtd_frota_propria,
                "autonomo": qtd_frota_autonomo
            },
            "relatividades": relatividades_motorista
        },
        # coberturas adicionais separadas (com prêmio final por cobertura)
        "coberturas_adicionais": lista_coberturas_adicionais
    }

    # -------------------------------------------------------------------------
    # Gera DataFrame do depurador completo (básica + adicionais) e salva
    # -------------------------------------------------------------------------
    depurador_final = pd.DataFrame(linhas)
    # garante colunas na ordem
    if not depurador_final.empty:
        depurador_final = depurador_final[["numero_cotacao", "versao_cotacao", "data_criacao_cotacao", "fonte", "pergunta", "resposta", "relatividade", "premio"]]

    # imprime no stdout (como seu código fazia)
    print(depurador_final.to_string(index=False), file=sys.stdout)

    # salva detalhes no banco (mesma mecânica que você já tinha)
    dados_depurador = depurador_final.to_dict(orient='records') if not depurador_final.empty else []
    if dados_depurador:
        numero = dados_depurador[0].get("numero_cotacao")
        versao_dep = dados_depurador[0].get("versao_cotacao")
        data_cri = dados_depurador[0].get("data_criacao_cotacao")
        salvar_detalhes_depurador(numero, versao_dep, data_cri, dados_depurador)

    # monta resultado_final e salva cotação completa (igual ao seu fluxo)
    resultado_final = {
        "metadata": {"status": "sucesso", "timestamp": datetime.now().isoformat()},
        "dados_cotacao": resposta_json,
        "detalhes_calculo": dados_depurador,
        "resumo": {
            "premio_total": premio_final_basica,  # observe: aqui mantive o prêmio total da básica
            "cobertura_principal": cobertura_id
        }
    }

    resposta_unificada = {
        "dados_principais": resposta_json,
        "detalhes_depurador": dados_depurador
    }
    salvar_cotacao_completa(resposta_unificada)

    return jsonify(resultado_final)


# rotas auxiliares (mantive as suas rotas originais para depurador/consulta)
@app.route("/depurador")
def mostrar_depurador():
    return render_template("depurador.html", linhas=[], cotacao_data={})

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
        try:
            cursor.close()
            conn.close()
        except:
            pass

# Se for executado diretamente
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
