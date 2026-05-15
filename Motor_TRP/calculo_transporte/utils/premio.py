# =========================================================
# CÁLCULO DE PRÊMIO
# =========================================================

def calcular_premio(

    importancia_segurada,
    taxa,
    comissao,
    iof

):

    # =====================================================
    # PRÊMIO RISCO
    # =====================================================

    premio_risco = (

        importancia_segurada
        * taxa

    )

    # =====================================================
    # PRÊMIO COMERCIAL
    # =====================================================

    # Comissão como carregamento

    if comissao >= 1:

        comissao = 0.99

    premio_comercial = (

        premio_risco
        / (1 - comissao)

    )

    # =====================================================
    # IOF
    # =====================================================

    premio_final = (

        premio_comercial
        * (1 + iof)

    )

    # =====================================================
    # RETORNO
    # =====================================================

    return {

        "premio_risco":
            round(
                premio_risco,
                2
            ),

        "premio_comercial":
            round(
                premio_comercial,
                2
            ),

        "premio_final":
            round(
                premio_final,
                2
            )

    }