import pandas as pd


# =========================================================
# CONCATENA RESULTADOS PRINCIPAIS
# =========================================================

def consolidar_principal(

    resultados

):

    dfs = []

    for resultado in resultados:

        df = resultado.get(
            "principal"
        )

        if (

            df is not None

            and

            not df.empty

        ):

            dfs.append(df)

    if not dfs:

        return pd.DataFrame()

    return pd.concat(

        dfs,
        ignore_index=True

    )


# =========================================================
# CONCATENA COBERTURAS
# =========================================================

def consolidar_coberturas(

    resultados

):

    dfs = []

    for resultado in resultados:

        df = resultado.get(
            "coberturas"
        )

        if (

            df is not None

            and

            not df.empty

        ):

            dfs.append(df)

    if not dfs:

        return pd.DataFrame()

    return pd.concat(

        dfs,
        ignore_index=True

    )


# =========================================================
# TOTAL GERAL
# =========================================================

def calcular_total_geral(

    df_principal,
    df_coberturas

):

    total_principal = 0
    total_coberturas = 0

    # =====================================================
    # PRINCIPAL
    # =====================================================

    if (

        df_principal is not None

        and

        not df_principal.empty

    ):

        total_principal = (

            df_principal[
                "Prêmio Final"
            ].sum()

        )

    # =====================================================
    # COBERTURAS
    # =====================================================

    if (

        df_coberturas is not None

        and

        not df_coberturas.empty

    ):

        total_coberturas = (

            df_coberturas[
                "Prêmio Final"
            ].sum()

        )

    # =====================================================
    # TOTAL
    # =====================================================

    total_geral = (

        total_principal
        + total_coberturas

    )

    return round(
        total_geral,
        2
    )

# =========================================================
# CONCATENA MEMÓRIA DE CÁLCULO
# =========================================================

def consolidar_memoria(

    resultados

):

    dfs = []

    for df in resultados:

        if (

            df is not None

            and

            not df.empty

        ):

            dfs.append(df)

    if not dfs:

        return pd.DataFrame()

    return pd.concat(

        dfs,
        ignore_index=True

    )