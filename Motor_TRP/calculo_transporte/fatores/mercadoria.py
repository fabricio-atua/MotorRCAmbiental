from calculo_transporte.taxas import (
    MERCADORIAS
)


# =========================================================
# FATOR MERCADORIA
# MÉDIA PONDERADA PELO MIX
# =========================================================

def calcular_fator_mercadoria(

    mercadorias,
    produto

):

    if not mercadorias:

        return 1.00

    soma_fatores = 0
    soma_mix = 0

    mapa_produto = {

        "RCTR-C": "f_rctr",
        "RC-DC": "f_rcdc",
        "TN": "f_tn",
        "TI": "f_ti"

    }

    campo_fator = mapa_produto[
        produto
    ]

    for item in mercadorias:

        codigo = item["codigo"]

        mix = float(
            item.get("mix", 0)
        )

        if mix <= 0:

            continue

        fator = MERCADORIAS[
            codigo
        ].get(
            campo_fator,
            1.00
        )

        soma_fatores += (
            fator * mix
        )

        soma_mix += mix

    if soma_mix == 0:

        return 1.00

    return (
        soma_fatores / soma_mix
    )