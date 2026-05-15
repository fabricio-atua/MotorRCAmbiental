from calculo_transporte.taxas import (
    TBL_DISTANCIA
)


# =========================================================
# FATOR DISTÂNCIA
# =========================================================

def calcular_fator_distancia(

    distancia,
    produto

):

    mapa_produto = {

        "RCTR-C": "f_rctr",
        "RC-DC": "f_rcdc",
        "TN": "f_tn",
        "TI": "f_ti"

    }

    campo_fator = mapa_produto[
        produto
    ]

    dados = TBL_DISTANCIA.get(
        distancia,
        {}
    )

    return dados.get(
        campo_fator,
        1.00
    )