from calculo_transporte.motores.rctr import (
    calcular_rctr
)

from calculo_transporte.motores.rcdc import (
    calcular_rcdc
)

from calculo_transporte.motores.tn import (
    calcular_tn
)

from calculo_transporte.motores.ti import (
    calcular_ti
)

from calculo_transporte.utils.dataframe import (

    consolidar_principal,
    consolidar_coberturas,
    consolidar_memoria,
    calcular_total_geral

)

# =========================================================
# ENGINE PRINCIPAL
# =========================================================

def calcular_motor(

    produtos,
    dados,
    comissao,
    iof

):

    resultados = []
    resultados_memoria = []
    # =====================================================
    # RCTR
    # =====================================================

    if "RCTR-C" in produtos:

        resultado_rctr = calcular_rctr(

            dados=
                dados["RCTR-C"],

            comissao=
                comissao,

            iof=
                iof

        )

        resultados.append(
            resultado_rctr
        )

        resultados_memoria.append(
            resultado_rctr["memoria"]
        )

    # =====================================================
    # RC-DC
    # =====================================================

    if "RC-DC" in produtos:

        resultado_rcdc = calcular_rcdc(

            dados=
                dados["RC-DC"],

            comissao=
                comissao,

            iof=
                iof

        )

        resultados.append(
            resultado_rcdc
        )

        resultados_memoria.append(
            resultado_rcdc["memoria"]
        )

    # =====================================================
    # TN
    # =====================================================

    if "TN" in produtos:

        resultado_tn = calcular_tn(

            dados=
                dados["TN"],

            comissao=
                comissao,

            iof=
                iof

        )

        resultados.append(
            resultado_tn
        )

        resultados_memoria.append(
            resultado_tn["memoria"]
        )

    # =====================================================
    # TI
    # =====================================================

    if "TI" in produtos:

        resultado_ti = calcular_ti(

            dados=
                dados["TI"],

            comissao=
                comissao,

            iof=
                iof

        )

        resultados.append(
            resultado_ti
        )

        resultados_memoria.append(
            resultado_ti["memoria"]
        )

    # =====================================================
    # CONSOLIDAÇÃO
    # =====================================================

    df_principal = consolidar_principal(
        resultados
    )

    df_coberturas = consolidar_coberturas(
        resultados
    )

    df_memoria = consolidar_memoria(
        resultados_memoria
    )

    total_geral = calcular_total_geral(

        df_principal,
        df_coberturas

    )

    # =====================================================
    # RETORNO
    # =====================================================

    return {

        "principal":
            df_principal,

        "coberturas":
            df_coberturas,

        "memoria":
            df_memoria,

        "total_geral":
            total_geral

    }