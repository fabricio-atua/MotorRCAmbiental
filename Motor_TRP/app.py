from flask import Flask, render_template, request

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

app = Flask(__name__)


# ======================================================================================================================
# HOME
# ======================================================================================================================

@app.route("/", methods=["GET", "POST"])
def home():

    resultado_principal = []

    resultado_coberturas = []

    resultado_memoria = []

    total_geral = 0

    erro = None

    try:

        if request.method == "POST":

            # ==========================================================================================================
            # PRODUTOS
            # ==========================================================================================================

            produtos_selecionados = request.form.getlist(
                "produtos[]"
            )

            print(produtos_selecionados)

            print(request.form)

            # ==========================================================================================================
            # CONFIGURAÇÕES
            # ==========================================================================================================

            comissao = (

                float(
                    request.form.get(
                        "comissao",
                        20
                    )
                ) / 100

            )

            possui_gr = request.form.get(
                "possui_gr"
            )

            empresa_gr = request.form.get(
                "empresa_gr"
            )

            modal_ti = request.form.get(
                "modal_ti",
                "RODOVIARIO"
            )

            # ==========================================================================================================
            # MERCADORIAS
            # ==========================================================================================================

            lista_mercadorias = request.form.getlist(
                "mercadoria[]"
            )

            lista_mix = request.form.getlist(
                "mix[]"
            )

            mercadorias = []

            for codigo, mix in zip(

                lista_mercadorias,
                lista_mix

            ):

                if codigo != "":

                    mercadorias.append({

                        "codigo":
                            codigo,

                        "mix":
                            float(mix)

                    })

            # ==========================================================================================================
            # ROTAS
            # ==========================================================================================================

            lista_origem = request.form.getlist(
                "origem[]"
            )

            lista_destino = request.form.getlist(
                "destino[]"
            )

            rotas = []

            for origem, destino in zip(

                lista_origem,
                lista_destino

            ):

                if origem != "" and destino != "":

                    rotas.append({

                        "origem":
                            origem,

                        "destino":
                            destino

                    })

            # ==========================================================================================================
            # SINISTRO
            # ==========================================================================================================

            valor_sinistros = float(

                request.form.get(
                    "valor_sinistros",
                    0
                )

            )

            teve_sinistro = request.form.get(
                "teve_sinistro"
            )

            # ==========================================================================================================
            # FUNÇÃO SINISTRO
            # ==========================================================================================================

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

            # ==========================================================================================================
            # COBERTURAS
            # ==========================================================================================================

            coberturas_adicionais = []

            produtos_cob = [

                ("RCTR-C", "rctr"),
                ("RC-DC", "rcdc"),
                ("TN", "tn"),
                ("TI", "ti")

            ]

            for produto_nome, prefixo in produtos_cob:

                lista_cob = request.form.getlist(
                    f"cob_{prefixo}[]"
                )

                lista_lmi = request.form.getlist(
                    f"lmi_{prefixo}[]"
                )

                for codigo, lmi in zip(

                    lista_cob,
                    lista_lmi

                ):

                    if codigo != "":

                        coberturas_adicionais.append({

                            "produto":
                                produto_nome,

                            "codigo":
                                codigo,

                            "lmi":
                                float(lmi)

                        })

            # ==========================================================================================================
            # DADOS MOTOR
            # ==========================================================================================================

            dados_motor = {}

            # ==========================================================================================================
            # RCTR-C
            # ==========================================================================================================

            if "RCTR-C" in produtos_selecionados:

                viagens = request.form.get(
                    "viagens_mes_rctr"
                )

                noturno = request.form.get(
                    "faixa_noturna"
                )

                rota = request.form.get(
                    "rota_critica"
                )

                idade = request.form.get(
                    "idade_frota"
                )

                terceiros = request.form.get(
                    "pct_terceiros"
                )

                dados_motor["RCTR-C"] = {

                    "valor_mensal":

                        float(

                            request.form.get(
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

            # ==========================================================================================================
            # RC-DC
            # ==========================================================================================================
            if "RC-DC" in produtos_selecionados:

                viagens = request.form.get(
                    "viagens_mes_rcdc"
                )

                noturno = request.form.get(
                    "faixa_noturna"
                )

                rota = request.form.get(
                    "rota_critica"
                )

                idade = request.form.get(
                    "idade_frota"
                )

                terceiros = request.form.get(
                    "pct_terceiros"
                )

                dados_motor["RC-DC"] = {

                    "valor_mensal":

                        float(

                            request.form.get(
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

            # ==========================================================================================================
            # TN
            # ==========================================================================================================
            if "TN" in produtos_selecionados:

                viagens = request.form.get(
                    "viagens_mes_tn"
                )

                noturno = request.form.get(
                    "faixa_noturna"
                )

                rota = request.form.get(
                    "rota_critica"
                )

                idade = request.form.get(
                    "idade_frota"
                )

                terceiros = request.form.get(
                    "pct_terceiros"
                )

                distancia = request.form.get(
                    "distancia_tn"
                )

                if distancia == "Baixa Distância":

                    fator_distancia = 1.00

                elif distancia == "Média Distancia":

                    fator_distancia = 1.03

                elif distancia == "Alta Distância":

                    fator_distancia = 1.08

                elif distancia == "Crítica Distância":

                    fator_distancia = 1.15

                else:

                    fator_distancia = 1.00


                dados_motor["TN"] = {

                    "valor_mensal":

                        float(

                            request.form.get(
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
                        fator_distancia,

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

                        {

                            "codigo": codigo,
                            "lmi": float(lmi)

                        }

                        for codigo, lmi in zip(

                            request.form.getlist(
                                "cobertura_tn[]"
                            ),

                            request.form.getlist(
                                "lmi_tn[]"
                            )

                        )

                        if codigo != ""

                    ]

                }


            # ==========================================================================================================
            # TI
            # ==========================================================================================================

            if "TI" in produtos_selecionados:

                viagens = request.form.get(
                    "viagens_mes_ti"
                )

                noturno = request.form.get(
                    "faixa_noturna"
                )

                rota = request.form.get(
                    "rota_critica"
                )

                idade = request.form.get(
                    "idade_frota"
                )

                terceiros = request.form.get(
                    "pct_terceiros"
                )

                dados_motor["TI"] = {

                    "valor_mensal":

                        float(

                            request.form.get(
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

                    "modal":
                        modal_ti,

                    "coberturas_adicionais": [

                        {

                            "codigo": codigo,
                            "lmi": float(lmi)

                        }

                        for codigo, lmi in zip(

                            request.form.getlist(
                                "cobertura_ti[]"
                            ),

                            request.form.getlist(
                                "lmi_ti[]"
                            )

                        )

                        if codigo != ""

                    ]

                }

            # ==========================================================================================================
            # MOTOR
            # ==========================================================================================================

            resultado = calcular_motor(
                
                produtos=
                    produtos_selecionados,

                dados=
                    dados_motor,

                comissao=
                    comissao,

                iof=
                    IOF

            )

            print(resultado)

            resultado_principal = (

                resultado["principal"]
                .to_dict(
                    orient="records"
                )

            )

            resultado_coberturas = (

                resultado["coberturas"]
                .to_dict(
                    orient="records"
                )

            )

            total_geral = (
                resultado["total_geral"]
            )

            resultado_memoria = (

                resultado["memoria"]
                .to_dict(
                    orient="records"
                )

            )
    except Exception as e:

        erro = str(e)

    # ==================================================================================================================
    # RENDER
    # ==================================================================================================================

    return render_template(

        "index.html",

        resultado_principal=
            resultado_principal,

        resultado_coberturas=
            resultado_coberturas,

        total_geral=
            total_geral,

        resultado_memoria=
            resultado_memoria,

        erro=
            erro,

        form_data=
            request.form,

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


# ======================================================================================================================
# MAIN
# ======================================================================================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )