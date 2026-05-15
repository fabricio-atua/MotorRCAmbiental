import pandas as pd

from calculo_transporte.taxas import (
    COBERTURAS_ADICIONAIS
)

# =========================================================
# CALCULA COBERTURAS ADICIONAIS
# =========================================================

def calcular_coberturas(

    produto,
    coberturas,
    comissao,
    iof

):

    resultado = []

    # =====================================================
    # SEM COBERTURA
    # =====================================================

    if not coberturas:

        return pd.DataFrame()

    # =====================================================
    # LOOP COBERTURAS
    # =====================================================

    for cobertura in coberturas:

        print("\n======================")
        print("COBERTURA RECEBIDA")
        print("======================")
        print(cobertura)

        # =================================================
        # CÓDIGO
        # =================================================

        codigo = str(

            cobertura.get(
                "codigo"
            )

            or

            cobertura.get(
                "cobertura"
            )

        )

        if not codigo:

            continue

        # =================================================
        # LMI
        # =================================================

        lmi = float(

            cobertura.get(
                "lmi",
                0
            )

        )

        # =================================================
        # VALIDA COBERTURA
        # =================================================

        if (

            codigo

            not in

            COBERTURAS_ADICIONAIS[
                produto
            ]

        ):

            raise Exception(

                f"""
                Cobertura {codigo}
                não encontrada
                para produto {produto}
                """

            )

        # =================================================
        # DADOS COBERTURA
        # =================================================

        dados_cobertura = (

            COBERTURAS_ADICIONAIS[
                produto
            ][codigo]

        )

        nome = dados_cobertura["nome"]

        taxa = dados_cobertura["taxa"]

        franquia = dados_cobertura.get(

            "franquia",
            0

        )

        # =================================================
        # PRÊMIO RISCO
        # =================================================

        premio_risco = (

            lmi
            * taxa
            * 12

        )

        # =================================================
        # PRÊMIO COMERCIAL
        # =================================================

        premio_comercial = (

            premio_risco
            / (1 - comissao)

        )

        # =================================================
        # PRÊMIO FINAL
        # =================================================

        premio_final = (

            premio_comercial
            * (1 + iof)

        )

        # =================================================
        # RESULTADO
        # =================================================

        resultado.append({

            "Produto":
                produto,

            "Código":
                codigo,

            "Cobertura":
                nome,

            "LMI":
                round(
                    lmi,
                    2
                ),

            "Taxa":
                round(
                    taxa,
                    6
                ),

            "Franquia":
                franquia,

            "Prêmio Risco":
                round(
                    premio_risco,
                    2
                ),

            "Prêmio Comercial":
                round(
                    premio_comercial,
                    2
                ),

            "Prêmio Final":
                round(
                    premio_final,
                    2
                )

        })

    # =====================================================
    # DATAFRAME
    # =====================================================

    return pd.DataFrame(
        resultado
    )