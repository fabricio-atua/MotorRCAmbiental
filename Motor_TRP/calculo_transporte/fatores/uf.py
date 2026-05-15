from calculo_transporte.taxas import (
    FATOR_UF
)


# =========================================================
# FATOR UF
# MÉDIA PONDERADA DAS ROTAS
# =========================================================

def calcular_fator_uf(

    rotas,
    produto

):

    if not rotas:

        return 1.00

    mapa_produto = {

        "RCTR-C": "fator_RCTR",
        "RC-DC": "fator_RCDC",
        "TN": "fator_TN",
        "TI": "fator_TI"

    }

    campo_fator = mapa_produto[
        produto
    ]

    soma_fatores = 0
    qtd_rotas = 0

    for rota in rotas:

        uf_origem = rota["origem"]
        uf_destino = rota["destino"]

        fator_origem = FATOR_UF.get(
            uf_origem,
            {}
        ).get(
            campo_fator,
            1.00
        )

        fator_destino = FATOR_UF.get(
            uf_destino,
            {}
        ).get(
            campo_fator,
            1.00
        )

        fator_rota = (
            fator_origem
            + fator_destino
        ) / 2

        soma_fatores += fator_rota

        qtd_rotas += 1

    if qtd_rotas == 0:

        return 1.00

    # =====================================================
    # MÉDIA PONDERADA DAS ROTAS
    # EVITA INFLAR O PREÇO
    # =====================================================

    return (
        soma_fatores / qtd_rotas
    )