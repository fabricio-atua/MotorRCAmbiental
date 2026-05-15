from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from calculo_transporte.engine import (
    calcular_motor
)

from calculo_transporte.taxas import (

    IOF,
    TBL_VIAGENS_MES,
    TBL_NOTURNO,
    TBL_ROTA_CRITICA,
    TBL_IDADE_FROTA,
    TBL_PCT_TERCEIROS,
    TBL_VALOR_SINISTRO,
    FATOR_UF,
    MERCADORIAS,
    COBERTURAS_ADICIONAIS

)

from datetime import datetime

import uuid
import json
import logging
import os

# =====================================================================
# CONFIG
# =====================================================================

VERSAO_MOTOR = "1.0.0"

# =====================================================================
# LOGS
# =====================================================================

if not os.path.exists("logs"):

    os.makedirs("logs")

logging.basicConfig(

    filename="logs/api.log",

    level=logging.INFO,

    format="""
    %(asctime)s
    %(levelname)s
    %(message)s
    """

)

# =====================================================================
# APP
# =====================================================================

app = Flask(__name__)

# =====================================================================
# PASTA COTAÇÕES
# =====================================================================

PASTA_COTACOES = "cotacoes"

if not os.path.exists(PASTA_COTACOES):

    os.makedirs(PASTA_COTACOES)

# =====================================================================
# HOME
# =====================================================================

@app.route("/")
def home():

    return render_template(

        "index.html",

        viagens=
            TBL_VIAGENS_MES.keys(),

        rotas=
            TBL_ROTA_CRITICA.keys(),

        noturnos=
            TBL_NOTURNO.keys(),

        idades=
            TBL_IDADE_FROTA["RODOVIARIO"].keys(),

        terceiros=
            TBL_PCT_TERCEIROS["RODOVIARIO"].keys(),

        ufs=
            FATOR_UF.keys(),

        mercadorias={

            codigo: dados["descricao"]

            for codigo, dados
            in MERCADORIAS.items()

        },

        coberturas_adicionais=
            COBERTURAS_ADICIONAIS,

        coberturas_tn=
            COBERTURAS_ADICIONAIS["TN"],

        coberturas_ti=
            COBERTURAS_ADICIONAIS["TI"]

    )

# =====================================================================
# HEALTH
# =====================================================================

@app.route(
    "/health",
    methods=["GET"]
)

def health():

    return jsonify({

        "status":
            "online",

        "motor":
            "transporte",

        "versao":
            VERSAO_MOTOR

    })

# =====================================================================
# SALVAR JSON
# =====================================================================

def salvar_cotacao_json(
    cotacao
):

    caminho = os.path.join(

        PASTA_COTACOES,

        f"{cotacao['id_cotacao']}.json"

    )

    with open(

        caminho,

        "w",

        encoding="utf-8"

    ) as arquivo:

        json.dump(

            cotacao,

            arquivo,

            ensure_ascii=False,

            indent=4

        )

# =====================================================================
# BUSCAR JSON
# =====================================================================

def buscar_cotacao_json(
    id_cotacao
):

    caminho = os.path.join(

        PASTA_COTACOES,

        f"{id_cotacao}.json"

    )

    if not os.path.exists(caminho):

        return None

    with open(

        caminho,

        "r",

        encoding="utf-8"

    ) as arquivo:

        return json.load(
            arquivo
        )

# =====================================================================
# FUNÇÃO SINISTRO
# =====================================================================

def calcular_fator_sinistro(
    valor,
    produto
):

    mapa = {

        "RCTR-C":
            "f_rctr",

        "RC-DC":
            "f_rcdc",

        "TN":
            "f_tn",

        "TI":
            "f_ti"

    }

    campo = mapa[
        produto
    ]

    for _, dados in (
        TBL_VALOR_SINISTRO.items()
    ):

        min_val, max_val = (
            dados["faixa"]
        )

        if (

            min_val <= valor <= max_val

        ):

            return dados.get(
                campo,
                1.00
            )

    return 1.00

# =====================================================================
# API COTAÇÃO
# =====================================================================

@app.route(
    "/cotacao/transporte",
    methods=["GET", "POST"]
)

def cotacao_transporte():

    # ================================================================
    # STATUS API
    # ================================================================

    if request.method == "GET":

        return jsonify({

            "status":
                "online",

            "rota":
                "/cotacao/transporte",

            "metodo":
                "POST",

            "mensagem":
                "API de cotação transporte online"

        })

    try:

        # ============================================================
        # PAYLOAD
        # ============================================================

        dados = request.get_json()

        if not dados:

            return jsonify({

                "status":
                    "erro",

                "mensagem":
                    "Payload JSON inválido"

            }), 400

        # ============================================================
        # INPUTS
        # ============================================================

        produtos = dados.get(
            "produtos",
            []
        )

        usuario = dados.get(
            "usuario",
            {}
        )

        comissao = float(

            dados.get(
                "comissao",
                0.20
            )

        )

        possui_gr = dados.get(
            "possui_gr"
        )

        empresa_gr = dados.get(
            "empresa_gr"
        )

        modal_ti = dados.get(
            "modal_ti",
            "RODOVIARIO"
        )

        valor_sinistros = float(

            dados.get(
                "valor_sinistros",
                0
            )

        )

        # ============================================================
        # MERCADORIAS
        # ============================================================

        mercadorias = dados.get(
            "mercadorias",
            []
        )

        # ============================================================
        # ROTAS
        # ============================================================

        rotas = dados.get(
            "rotas",
            []
        )

        # ============================================================
        # COBERTURAS
        # ============================================================

        coberturas_adicionais = dados.get(
            "coberturas_adicionais",
            []
        )

        # ============================================================
        # DADOS MOTOR
        # ============================================================

        dados_motor = {}

        # ============================================================
        # RCTR-C
        # ============================================================

        if "RCTR-C" in produtos:

            viagens = dados.get(
                "viagens_mes_rctr"
            )

            noturno = dados.get(
                "faixa_noturna"
            )

            rota = dados.get(
                "rota_critica"
            )

            idade = dados.get(
                "idade_frota"
            )

            terceiros = dados.get(
                "pct_terceiros"
            )

            dados_motor["RCTR-C"] = {

                "valor_mensal":

                    float(

                        dados.get(
                            "valor_mensal_rctr",
                            0
                        )

                    ),

                "fator_viagens":

                    TBL_VIAGENS_MES[
                        viagens
                    ]["f_rctr"],

                "fator_noturno":

                    TBL_NOTURNO[
                        noturno
                    ]["f_rctr"],

                "fator_rota_critica":

                    TBL_ROTA_CRITICA[
                        rota
                    ]["f_rctr"],

                "fator_distancia":
                    1.00,

                "fator_idade":

                    TBL_IDADE_FROTA[
                        "RODOVIARIO"
                    ][idade]["f_rctr"],

                "fator_terceiros":

                    TBL_PCT_TERCEIROS[
                        "RODOVIARIO"
                    ][terceiros]["f_rctr"],

                "fator_sinistro":

                    calcular_fator_sinistro(
                        valor_sinistros,
                        "RCTR-C"
                    ),

                "mercadorias":
                    mercadorias,

                "rotas":
                    rotas,

                "coberturas_adicionais": [

                    c for c in coberturas_adicionais

                    if c["produto"] == "RCTR-C"

                ]

            }

        # ============================================================
        # RC-DC
        # ============================================================

        if "RC-DC" in produtos:

            viagens = dados.get(
                "viagens_mes_rcdc"
            )

            noturno = dados.get(
                "faixa_noturna"
            )

            rota = dados.get(
                "rota_critica"
            )

            idade = dados.get(
                "idade_frota"
            )

            terceiros = dados.get(
                "pct_terceiros"
            )

            dados_motor["RC-DC"] = {

                "valor_mensal":

                    float(

                        dados.get(
                            "valor_mensal_rcdc",
                            0
                        )

                    ),

                "fator_viagens":

                    TBL_VIAGENS_MES[
                        viagens
                    ]["f_rcdc"],

                "fator_noturno":

                    TBL_NOTURNO[
                        noturno
                    ]["f_rcdc"],

                "fator_rota_critica":

                    TBL_ROTA_CRITICA[
                        rota
                    ]["f_rcdc"],

                "fator_distancia":
                    1.00,

                "fator_idade":

                    TBL_IDADE_FROTA[
                        "RODOVIARIO"
                    ][idade]["f_rcdc"],

                "fator_terceiros":

                    TBL_PCT_TERCEIROS[
                        "RODOVIARIO"
                    ][terceiros]["f_rcdc"],

                "fator_sinistro":

                    calcular_fator_sinistro(
                        valor_sinistros,
                        "RC-DC"
                    ),

                "mercadorias":
                    mercadorias,

                "rotas":
                    rotas,

                "coberturas_adicionais": [

                    c for c in coberturas_adicionais

                    if c["produto"] == "RC-DC"

                ]

            }

        # ============================================================
        # TN
        # ============================================================

        if "TN" in produtos:

            viagens = dados.get(
                "viagens_mes_tn"
            )

            noturno = dados.get(
                "faixa_noturna"
            )

            rota = dados.get(
                "rota_critica"
            )

            idade = dados.get(
                "idade_frota"
            )

            terceiros = dados.get(
                "pct_terceiros"
            )

            print("\n======================")
            print("DEBUG TN")
            print("======================")
            print("viagens:", viagens)
            print("noturno:", noturno)
            print("rota:", rota)
            print("idade:", idade)
            print("terceiros:", terceiros)

            if viagens not in TBL_VIAGENS_MES:

                raise Exception(
                    f"Faixa viagens TN inválida: {viagens}"
                )

            if noturno not in TBL_NOTURNO:

                raise Exception(
                    f"Faixa noturno inválida: {noturno}"
                )

            if rota not in TBL_ROTA_CRITICA:

                raise Exception(
                    f"Rota crítica inválida: {rota}"
                )

            if idade not in TBL_IDADE_FROTA["RODOVIARIO"]:

                raise Exception(
                    f"Idade frota inválida: {idade}"
                )

            if terceiros not in TBL_PCT_TERCEIROS["RODOVIARIO"]:

                raise Exception(
                    f"Pct terceiros inválido: {terceiros}"
                )

            dados_motor["TN"] = {

                "valor_mensal":

                    float(

                        dados.get(
                            "valor_mensal_tn",
                            0
                        )

                    ),

                "fator_viagens":

                    TBL_VIAGENS_MES[
                        viagens
                    ]["f_tn"],

                "fator_noturno":

                    TBL_NOTURNO[
                        noturno
                    ]["f_tn"],

                "fator_rota_critica":

                    TBL_ROTA_CRITICA[
                        rota
                    ]["f_tn"],

                "fator_distancia":
                    1.00,

                "fator_idade":

                    TBL_IDADE_FROTA[
                        "RODOVIARIO"
                    ][idade]["f_tn"],

                "fator_terceiros":

                    TBL_PCT_TERCEIROS[
                        "RODOVIARIO"
                    ][terceiros]["f_tn"],

                "fator_sinistro":

                    calcular_fator_sinistro(
                        valor_sinistros,
                        "TN"
                    ),

                "mercadorias":
                    mercadorias,

                "rotas":
                    rotas,

                "coberturas_adicionais": [

                    c for c in coberturas_adicionais

                    if c["produto"] == "TN"

                ]

            }

            print("\n======================")
            print("DADOS MOTOR TN")
            print("======================")
            print(dados_motor["TN"])

        # ============================================================
        # TI
        # ============================================================

        if "TI" in produtos:

            viagens = dados.get(
                "viagens_mes_ti"
            )

            noturno = dados.get(
                "faixa_noturna"
            )

            rota = dados.get(
                "rota_critica"
            )

            idade = dados.get(
                "idade_frota"
            )

            terceiros = dados.get(
                "pct_terceiros"
            )

            print("\n======================")
            print("DEBUG TI")
            print("======================")
            print("modal:", modal_ti)
            print("viagens:", viagens)
            print("noturno:", noturno)
            print("rota:", rota)
            print("idade:", idade)
            print("terceiros:", terceiros)

            if viagens not in TBL_VIAGENS_MES:

                raise Exception(
                    f"Faixa viagens TI inválida: {viagens}"
                )

            if noturno not in TBL_NOTURNO:

                raise Exception(
                    f"Faixa noturno inválida: {noturno}"
                )

            if rota not in TBL_ROTA_CRITICA:

                raise Exception(
                    f"Rota crítica inválida: {rota}"
                )

            if idade not in TBL_IDADE_FROTA[modal_ti]:

                raise Exception(
                    f"Idade frota inválida: {idade}"
                )

            if terceiros not in TBL_PCT_TERCEIROS[modal_ti]:

                raise Exception(
                    f"Pct terceiros inválido: {terceiros}"
                )

            dados_motor["TI"] = {

                "valor_mensal":

                    float(

                        dados.get(
                            "valor_mensal_ti",
                            0
                        )

                    ),

                "fator_viagens":

                    TBL_VIAGENS_MES[
                        viagens
                    ]["f_ti"],

                "fator_noturno":

                    TBL_NOTURNO[
                        noturno
                    ]["f_ti"],

                "fator_rota_critica":

                    TBL_ROTA_CRITICA[
                        rota
                    ]["f_ti"],

                "fator_distancia":
                    1.00,

                "fator_idade":

                    TBL_IDADE_FROTA[
                        modal_ti
                    ][idade]["f_ti"],

                "fator_terceiros":

                    TBL_PCT_TERCEIROS[
                        modal_ti
                    ][terceiros]["f_ti"],

                "fator_sinistro":

                    calcular_fator_sinistro(
                        valor_sinistros,
                        "TI"
                    ),

                "mercadorias":
                    mercadorias,

                "rotas":
                    rotas,

                "coberturas_adicionais": [

                    c for c in coberturas_adicionais

                    if c["produto"] == "TI"

                ]

            }

            print("\n======================")
            print("DADOS MOTOR TI")
            print("======================")
            print(dados_motor["TI"])





        # ============================================================
        # MOTOR
        # ============================================================

        resultado = calcular_motor(

            produtos=
                produtos,

            dados=
                dados_motor,

            comissao=
                comissao,

            iof=
                IOF

        )

        # ============================================================
        # RESULTADOS
        # ============================================================

        principal = (

            resultado[
                "principal"
            ].to_dict(
                orient="records"
            )

        )

        coberturas = (

            resultado[
                "coberturas"
            ].to_dict(
                orient="records"
            )

        )

        memoria = (

            resultado[
                "memoria"
            ].to_dict(
                orient="records"
            )

        )

        total_geral = (

            resultado[
                "total_geral"
            ]

        )

        # ============================================================
        # UUID
        # ============================================================

        id_cotacao = str(
            uuid.uuid4()
        )

        # ============================================================
        # JSON FINAL
        # ============================================================

        cotacao_final = {

            "id_cotacao":
                id_cotacao,

            "data_cotacao":
                datetime.utcnow().isoformat(),

            "status":
                "sucesso",

            "versao_motor":
                VERSAO_MOTOR,

            "usuario":
                usuario,

            "payload_entrada":
                dados,

            "dados_motor":
                dados_motor,

            "resultado": {

                "principal":
                    principal,

                "coberturas":
                    coberturas,

                "memoria_calculo":
                    memoria,

                "total_geral":
                    total_geral

            }

        }

        # ============================================================
        # SALVAR JSON
        # ============================================================

        salvar_cotacao_json(
            cotacao_final
        )

        # ============================================================
        # LOG
        # ============================================================

        logging.info(

            f"""
            COTAÇÃO FINALIZADA
            ID: {id_cotacao}
            TOTAL: {total_geral}
            """
        )

        # ============================================================
        # RETORNO
        # ============================================================

        return jsonify(
            cotacao_final
        )

    except Exception as e:

        logging.error(

            f"""
            ERRO COTAÇÃO
            {str(e)}
            """
        )

        return jsonify({

            "status":
                "erro",

            "mensagem":
                str(e)

        }), 500

# =====================================================================
# CONSULTAR COTAÇÃO
# =====================================================================

@app.route(
    "/cotacao/<id_cotacao>",
    methods=["GET"]
)

def consultar_cotacao(
    id_cotacao
):

    try:

        cotacao = buscar_cotacao_json(
            id_cotacao
        )

        if not cotacao:

            return jsonify({

                "status":
                    "erro",

                "mensagem":
                    "Cotação não encontrada"

            }), 404

        return jsonify(
            cotacao
        )

    except Exception as e:

        return jsonify({

            "status":
                "erro",

            "mensagem":
                str(e)

        }), 500

# =====================================================================
# LISTAR COTAÇÕES
# =====================================================================

@app.route(
    "/cotacoes",
    methods=["GET"]
)

def listar_cotacoes():

    try:

        lista = []

        arquivos = os.listdir(
            PASTA_COTACOES
        )

        for arquivo in arquivos:

            caminho = os.path.join(

                PASTA_COTACOES,

                arquivo

            )

            with open(

                caminho,

                "r",

                encoding="utf-8"

            ) as f:

                cotacao = json.load(f)

                lista.append({

                    "id_cotacao":

                        cotacao.get(
                            "id_cotacao"
                        ),

                    "data_cotacao":

                        cotacao.get(
                            "data_cotacao"
                        ),

                    "total_geral":

                        cotacao[
                            "resultado"
                        ].get(
                            "total_geral"
                        ),

                    "usuario":

                        cotacao.get(
                            "usuario"
                        )

                })

        return jsonify({

            "status":
                "sucesso",

            "quantidade":
                len(lista),

            "cotacoes":
                lista

        })

    except Exception as e:

        return jsonify({

            "status":
                "erro",

            "mensagem":
                str(e)

        }), 500

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":

    print("\n====================================")
    print("API MOTOR TRANSPORTE ONLINE")
    print("====================================")

    print("Navegador:")
    print("http://127.0.0.1:5000/")

    #print("\nHEALTH:")
    #print("http://127.0.0.1:5000/health")

    print("\nAPI COTAÇÃO:")
    print("http://127.0.0.1:5000/cotacao/transporte")

    #print("\nLISTAR COTAÇÕES:")
   # print("http://127.0.0.1:5000/cotacoes")

    #print("====================================\n")

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True,

        use_reloader=False

    )