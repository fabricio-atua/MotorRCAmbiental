from calculo_transporte.taxas import (
    TBL_VALOR_SINISTRO
)


# =========================================================
# FATOR SINISTRO
# =========================================================

def calcular_fator_sinistro(

    valor_sinistro,
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

    for faixa, dados in (
        TBL_VALOR_SINISTRO.items()
    ):

        minimo, maximo = (
            dados["faixa"]
        )

        if (

            valor_sinistro >= minimo

            and

            valor_sinistro <= maximo

        ):

            return dados.get(
                campo_fator,
                1.00
            )

    return 1.00