import mysql.connector
import json
from flask import request
import pandas as pd
import sys
from configLocal import db_user, db_password, db_name, db_host, db_port

# ============================================================
# 1) Conexão MySQL
# ============================================================
def get_mysql_connection():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        autocommit=True
    )

# ============================================================
# 2) Buscar fator
# ============================================================
def buscar_fator(tabela, campo, valores):
    """
    Busca registros em qualquer tabela e campo.
    - Se 'valores' for lista → IN
    - Se for valor único → =
    - Sempre filtra pela maior NR_TARIFA
    - NÃO filtra colunas FT_ (isso é feito no depurador)
    """

    conn = get_mysql_connection()

    # 1) Buscar NR_TARIFA mais recente
    with conn.cursor(dictionary=True, buffered=True) as cur1:
        cur1.execute(f"SELECT MAX(NR_TARIFA) AS max_tarifa FROM {tabela}")
        row = cur1.fetchone()
        if not row or not row["max_tarifa"]:
            conn.close()
            return [] if isinstance(valores, list) else {}

        max_tarifa = row["max_tarifa"]

    # 2) Buscar dados
    with conn.cursor(dictionary=True, buffered=True) as cur2:
        if isinstance(valores, list):
            if not valores:
                conn.close()
                return []
            placeholders = ", ".join(["%s"] * len(valores))
            query = f"""
                SELECT *
                FROM {tabela}
                WHERE NR_TARIFA = %s
                  AND {campo} IN ({placeholders})
            """
            cur2.execute(query, [max_tarifa] + valores)
            resultados = cur2.fetchall()
        else:
            query = f"""
                SELECT *
                FROM {tabela}
                WHERE NR_TARIFA = %s
                  AND {campo} = %s
            """
            cur2.execute(query, (max_tarifa, valores))
            resultados = cur2.fetchone() or {}

    conn.close()
    return resultados


depuradores = []

# ============================================================
# 3) BUSCA DADOS DA COTAÇÃO – DEPURADOR COBERTURAS ADICIONAIS
# ============================================================
def calcular_precificacao_cobertura_ADD(resposta_json):
    """
    DEPURADOR DE COBERTURAS ADICIONAIS
    --------------------------------
    - Suporta 0 a 5 coberturas
    - Cada cobertura é calculada isoladamente
    - NÃO altera regra do motor principal
    """
    cotacao_info = resposta_json.get("cotacao", {})

    numero_cotacao = cotacao_info.get("numero_cotacao")
    versao_cotacao = cotacao_info.get("versao")
    data_criacao_cotacao = cotacao_info.get("data_criacao")

    json_coberturas_adicionais = []

    # ============================================================
    # 1) LEITURA DAS COBERTURAS DO FORMULÁRIO
    # ============================================================
    coberturas_raw = request.form.getlist("coberturas_adicionais[]")
    coberturas_adicionais = []

    for item in coberturas_raw:
        try:
            coberturas_adicionais.append(json.loads(item))
        except Exception:
            pass

    if not coberturas_adicionais:
        return pd.DataFrame(columns=[
            "numero_cotacao", "versao_cotacao", "data_criacao_cotacao",
            "fonte", "pergunta", "resposta", "relatividade", "premio", "cobertura"
        ])

    codigos_cobertura = [c["codigo"] for c in coberturas_adicionais]

    # ============================================================
    # 2) BUSCA DESCRIÇÕES E PRÊMIO BASE
    # ============================================================
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        f"""
        SELECT CD_COBERTURA, DS_COBERTURA
        FROM CA_COBERTURA
        WHERE CD_COBERTURA IN ({",".join(["%s"] * len(codigos_cobertura))})
        """,
        codigos_cobertura
    )
    coberturas_desc = cursor.fetchall()

    cursor.close()
    conn.close()

    # Mapa: código da cobertura -> descrição da cobertura
    mapa_coberturas = {
        item["CD_COBERTURA"]: item["DS_COBERTURA"]
        for item in coberturas_desc
    }

    linha_premio = buscar_fator("PR_PREMIO", "CD_SEGMENTO", 1)

    # ============================================================
    # 3) BUSCA FATORES (UMA ÚNICA VEZ)
    # ============================================================
    canal = buscar_fator("FT_CANAL", "CD_CANAL", request.form.get("ft_canal"))
    prodperig = buscar_fator("FT_PRODPERIG", "CD_PRODPERIG", request.form.get("ft_prodperig"))

    ft_modais = buscar_fator("FT_MODAIS", "CD_MODAIS", request.form.getlist("modais_utilizado[]"))
    ft_atividade = buscar_fator("FT_ATIVIDADE", "CD_ATIVIDADE", request.form.getlist("atividade[]"))

    ft_acondic_granel = buscar_fator(
        "FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO",
        request.form.get("ft_acondicionamento_granel")
    )

    ft_acondic_fracional = buscar_fator(
        "FT_ACONDICIONAMENTO", "CD_FAIXA_ACONDICIONAMENTO",
        request.form.get("ft_acondicionamento_fracionado")
    )

    carregamentos = buscar_fator(
        "FT_CARREGAMENTO", "CD_CARREGAMENTO",
        [1,2,3,4,5,6,7,8,9,10,11,12]
    )

    # ============================================================
    # 4) FUNÇÃO INTERNA PARA ADICIONAR LINHAS
    # ============================================================
    def adicionar_linha(linhas, linhas_json, valor_corrente,
                        fonte, pergunta, resposta, relatividade, cobertura):

        if isinstance(relatividade, (int, float)):
            valor_corrente = round(valor_corrente * relatividade, 4)

        # 🔹 registro COMPLETO (para DataFrame)
        registro = {
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": fonte,
            "pergunta": pergunta,
            "resposta": resposta,
            "relatividade": relatividade,
            "premio": valor_corrente,
            "cobertura": cobertura
        }

        linhas.append(registro)

        # 🔹 registro SIMPLIFICADO (para JSON)
        linhas_json.append({
            "fonte": fonte,
            "pergunta": pergunta,
            "resposta": resposta,
            "relatividade": relatividade,
            "premio": valor_corrente
        })

        return valor_corrente


    # ============================================================
    # 5) LOOP PRINCIPAL – UMA COBERTURA POR VEZ
    # ============================================================
    
    def normalizar_lmi(valor):
        if not valor:
            return None
        return float(
            str(valor)
            .replace(".", "")
            .replace(",", ".")
        )
    
    
    depuradores = []

    for cobertura in coberturas_adicionais:

        codigo = cobertura["codigo"]          # CA1
        cobertura_id = f"FT_{codigo}"         # FT_CA1
        coluna_premio = f"PR_{codigo}"

        premio_base = linha_premio.get(coluna_premio)
        if not premio_base:
            continue

        valor_corrente = float(premio_base)
        linhas = []        # para DataFrame
        linhas_json = []   # para JSON


        # ---------------------------------------------------------
        # LINHA BASAL (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        descricao_cobertura = mapa_coberturas.get(codigo, codigo)

        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Basal",
            "pergunta": descricao_cobertura,
            "resposta": codigo,
            "relatividade": "",
            "premio": valor_corrente,
            "cobertura": codigo
        })

        # ---------------------------------------------------------
        # CERTIFICAÇÕES (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        for i, cert in enumerate(resposta_json.get("certificacoes", []), start=1):

            cd_tem_certificacao = cert.get("CD_TEMCERTIFICACAO")

            if not cd_tem_certificacao:
                continue

            resultado = buscar_fator(
                "FT_CERTIFICACAO",
                "CD_TEMCERTIFICACAO",
                cd_tem_certificacao
            )

            if not resultado:
                continue

            valor_corrente = adicionar_linha(
                linhas,
                linhas_json,
                valor_corrente,
                f"Certificação_{i}",
                cert.get("DS_CERTIFICACAO"),
                cd_tem_certificacao,
                resultado.get(cobertura_id),  # FT_CA
                codigo
            )

        # ---------------------------------------------------------
        # CANAL 
        # ---------------------------------------------------------
        if canal:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json,
                valor_corrente,
                "Canal", "Canal",
                canal.get("DS_CANAL"),
                canal.get(cobertura_id),
                codigo
            )

        # ---------------------------------------------------------
        # PRODUTO PERIGOSO (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        if prodperig:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json,
                valor_corrente,
                "Produto", "Produto Perigoso",
                prodperig.get("DS_PRODPERIG"),
                prodperig.get(cobertura_id),
                codigo
            )


        # ---------------------------------------------------------
        # QUANTIDADE DE EMBARQUE (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        ft_qtde_embarque = request.form.get("ft_qtde_embarque")

        if ft_qtde_embarque:
            try:
                ft_qtde_embarque = float(ft_qtde_embarque)

                conn = get_mysql_connection()
                cursor = conn.cursor(dictionary=True)

                coluna_fator = cobertura_id  # FT_CA1, FT_CA2...

                query = f"""
                    SELECT `{coluna_fator}`, DS_QTDEMBARQUE
                    FROM FT_QTDE_EMBARQUE
                    WHERE %s BETWEEN CD_QTDEMBARQUE_INI AND CD_QTDEMBARQUE_FIM
                    LIMIT 1
                """

                cursor.execute(query, (ft_qtde_embarque,))
                resultado = cursor.fetchone()

                if resultado:
                    valor_corrente = adicionar_linha(
                        linhas,
                        linhas_json,
                        valor_corrente,
                        "Embarque",
                        "Quantidade de Embarque",
                        resultado.get("DS_QTDEMBARQUE"),
                        resultado.get(coluna_fator),  # 👈 relatividade correta
                        codigo
                    )

                cursor.close()
                conn.close()

            except Exception as e:
                print("Erro QTDE_EMBARQUE adicional:", e)

        
        # ---------------------------------------------------------
        # EMBARQUE – LMI (FAIXA) (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        lmi_input = normalizar_lmi(cobertura.get("lmi"))

        if lmi_input is not None:

            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = f"""
                SELECT *
                FROM FT_ISAGRUPCOBETURA
                WHERE NR_TARIFA = (
                    SELECT MAX(NR_TARIFA) FROM FT_ISAGRUPCOBETURA
                )
                AND %s BETWEEN CD_LMI_INI AND CD_LMI_FIM
                LIMIT 1
            """

            cursor.execute(query, (lmi_input,))
            bloco_lmi = cursor.fetchone()

            cursor.close()
            conn.close()

            if bloco_lmi:
                valor_corrente = adicionar_linha(
                    linhas,
                    linhas_json,
                    valor_corrente,
                    "Embarque_LMI",
                    "LMI",
                    bloco_lmi.get("DS_LMI"),
                    bloco_lmi.get(cobertura_id),  # FT_CA1 / FT_CA2
                    codigo
                )


        # ---------------------------------------------------------
        # PERFIL DO MOTORISTA (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        perfil_motorista = request.form.getlist("perfil_motorista[]")

        for i, cd_perfil in enumerate(perfil_motorista, start=1):

            resultado = buscar_fator(
                "FT_PERFMOTORISTA",
                "CD_PERFMOTORISTA",
                cd_perfil
            )

            if resultado:
                valor_corrente = adicionar_linha(
                    linhas,
                    linhas_json,
                    valor_corrente,
                    f"Perfil_motorista_{i}",
                    "Perfil do Motorista",
                    resultado.get("DS_PERFMOTORISTA"),
                    resultado.get(cobertura_id),  # FT_CA1, FT_CA2...
                    codigo
                )

        
        # ---------------------------------------------------------
        # TIPO DE SEGURO (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        tipos_seguro = request.form.getlist("tipo_seguro[]")

        for i, cd_tipo in enumerate(tipos_seguro, start=1):

            resultado = buscar_fator(
                "FT_TIPSEGURO",
                "CD_TIPSEGURO",
                cd_tipo
            )

            if resultado:
                valor_corrente = adicionar_linha(
                    linhas,
                    linhas_json,
                    valor_corrente,
                    f"Tipo_Seguro_{i}",
                    "Tipo de Seguro",
                    resultado.get("DS_TIPSEGURO"),
                    resultado.get(cobertura_id),  # FT_CA1, FT_CA2...
                    codigo
                )


        # ---------------------------------------------------------
        # CLASSE DO PRODUTO (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        classes = json.loads(request.form.get("classes", "{}"))
        porcentagens = json.loads(request.form.get("porcentagens", "{}"))

        for cd_classe, percentual in porcentagens.items():

            resultado = buscar_fator(
                "FT_CLASSEPRODUTO",
                "CD_CLASSEPRODUTO",
                cd_classe
            )

            if resultado:
                valor_corrente = adicionar_linha(
                    linhas,
                    linhas_json,
                    valor_corrente,
                    f"Classe_{cd_classe}",
                    "Classe do Produto",
                    resultado.get("DS_CLASSEPRODUTO"),
                    resultado.get(cobertura_id),  # FT_CA1, FT_CA2...
                    codigo
                )


        # ---------------------------------------------------------
        # UF (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        ufs = json.loads(request.form.get("ufs", "[]"))

        for cd_uf in ufs:

            resultado = buscar_fator(
                "FT_UF",
                "CD_UF",
                cd_uf
            )

            if resultado:
                valor_corrente = adicionar_linha(
                    linhas,
                    linhas_json,
                    valor_corrente,
                    f"UF_{cd_uf}",
                    "UF",
                    resultado.get("DS_UF"),
                    resultado.get(cobertura_id),  # FT_CA1, FT_CA2...
                    codigo
                )

        # ---------------------------------------------------------
        # MODAIS (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        for modal in ft_modais or []:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json,
                valor_corrente,
                "Modal", "Modal",
                modal.get("DS_MODAIS"),
                modal.get(cobertura_id),
                codigo
            )
        
        # ---------------------------------------------------------
        # ATIVIDADE (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        for atv in ft_atividade or []:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json, 
                valor_corrente,
                "Atividade", "Atividade",
                atv.get("DS_ATIVIDADE"),
                atv.get(cobertura_id),
                codigo
            )

        # ---------------------------------------------------------
        # ACONDICIONAMENTO (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        for bloco, nome in [
            (ft_acondic_granel, "Granel"),
            (ft_acondic_fracional, "Fracionado")
        ]:
            if bloco:
                valor_corrente = adicionar_linha(
                    linhas, 
                    linhas_json,
                    valor_corrente,
                    "Acondicionamento", nome,
                    bloco.get("DS_ACONDICIONAMENTO"),
                    bloco.get(cobertura_id),
                    codigo
                )


        # ---------------------------------------------------------
        # TOTAL – PRÊMIO DE RISCO (ANTES DOS CARREGAMENTOS) (COBERTURA ADICIONAL)
        # ---------------------------------------------------------
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio de Risco",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })

        # ---------------------------------------------------------
        # BLOCO 1 – CARREGAMENTOS (1, 2, 3)
        # ---------------------------------------------------------
        carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [1, 2, 3])

        for item in carregamentos or []:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json,
                valor_corrente,
                "Carregamento",
                f"Carreg. {item['CD_CARREGAMENTO']}",
                item.get("DS_CARREGAMENTO"),
                item.get(cobertura_id),
                codigo
            )

        # Linha intermediária – Prêmio de Risco
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio de Risco",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })

        # ---------------------------------------------------------
        # BLOCO 2 – CARREGAMENTOS (4, 5, 6)
        # ---------------------------------------------------------
        carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [4, 5, 6])

        for item in carregamentos or []:
            valor_corrente = adicionar_linha(
                linhas,
                linhas_json, 
                valor_corrente,
                "Carregamento",
                f"Carreg. {item['CD_CARREGAMENTO']}",
                item.get("DS_CARREGAMENTO"),
                item.get(cobertura_id),
                codigo
            )

        # Linha intermediária – Prêmio de Risco
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio de Risco",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })


        # ---------------------------------------------------------
        # BLOCO 3 – CARREGAMENTO 7
        # ---------------------------------------------------------
        carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [7])

        for item in carregamentos or []:
            valor_corrente = adicionar_linha(
                linhas, 
                linhas_json,
                valor_corrente,
                "Carregamento",
                f"Carreg. {item['CD_CARREGAMENTO']}",
                item.get("DS_CARREGAMENTO"),
                item.get(cobertura_id),
                codigo
            )

        # Linha – Prêmio Puro
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio Puro",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })

        # ---------------------------------------------------------
        # BLOCO 4 – COMISSÃO + CARREGAMENTOS (8, 9, 10, 11)
        # ---------------------------------------------------------
        corretor = resposta_json.get("corretor", {})

        valor_corrente = adicionar_linha(
            linhas, 
            linhas_json,
            valor_corrente,
            "Corretor",
            "Comissão do Corretor",
            f"{corretor.get('corretor_comissao', '')}%",
            corretor.get("corretor_fator", 1.0),
            codigo
        )

        carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [8, 9, 10, 11])

        for item in carregamentos or []:
            valor_corrente = adicionar_linha(
                linhas, 
                linhas_json,
                valor_corrente,
                "Carregamento",
                f"Carreg. {item['CD_CARREGAMENTO']}",
                item.get("DS_CARREGAMENTO"),
                item.get(cobertura_id),
                codigo
            )

        # Linha – Prêmio Líquido
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio Líquido",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })

        # ---------------------------------------------------------
        # BLOCO 5 – CARREGAMENTO 12 (IOF)
        # ---------------------------------------------------------
        carregamentos = buscar_fator("FT_CARREGAMENTO", "CD_CARREGAMENTO", [12])

        for item in carregamentos or []:
            valor_corrente = adicionar_linha(
                linhas, 
                linhas_json,
                valor_corrente,
                "Carregamento",
                f"Carreg. {item['CD_CARREGAMENTO']}",
                item.get("DS_CARREGAMENTO"),
                item.get(cobertura_id),
                codigo
            )

        # Linha – Prêmio Total
        linhas.append({
            "numero_cotacao": numero_cotacao,
            "versao_cotacao": versao_cotacao,
            "data_criacao_cotacao": data_criacao_cotacao,
            "fonte": "Prêmio Total",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": round(valor_corrente, 4),
            "cobertura": codigo
        })


        # ---------------------------------------------------------
        # LINHA EM BRANCO – SEPARADOR ENTRE COBERTURAS
        # ---------------------------------------------------------
        linhas.append({
            "numero_cotacao": "",
            "versao_cotacao": "",
            "data_criacao_cotacao": "",
            "fonte": "",
            "pergunta": "",
            "resposta": "",
            "relatividade": "",
            "premio": "",
            "cobertura": ""
        })

        depuradores.append(pd.DataFrame(linhas))


         # ---------------------------------------------------------
        # JSON DA COBERTURA ADICIONAL (UMA POR LOOP)
        # ---------------------------------------------------------
        
        cobertura_json = {
            "codigo_cobertura": codigo,
            "descricao_cobertura": descricao_cobertura,
            "premio_base": premio_base,
            "premio_total": round(valor_corrente, 2),
            "depurador": linhas_json
        }

        json_coberturas_adicionais.append(cobertura_json)
       
    # ============================================================
    # 6) CONSOLIDAÇÃO FINAL
    # ============================================================
    if not depuradores:
        return pd.DataFrame(columns=[
            "numero_cotacao", "versao_cotacao", "data_criacao_cotacao",
            "fonte", "pergunta", "resposta", "relatividade", "premio", "cobertura"
        ])

    depurador_final = pd.concat(depuradores, ignore_index=True)
    return {
    "depurador_df": depurador_final.to_dict(orient="records"),
    "coberturas_adicionais": json_coberturas_adicionais
}


# ============================================================
# FUNÇÃO PÚBLICA CHAMADA PELO MOTOR
# ============================================================
def executar_depurador_cobertura_adicional(resposta_json):
    """
    Função chamada pelo motor (wrapper).
    """
    return calcular_precificacao_cobertura_ADD(resposta_json)