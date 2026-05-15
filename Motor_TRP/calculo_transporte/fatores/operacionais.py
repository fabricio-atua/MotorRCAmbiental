from calculo_transporte.taxas import (

    TBL_VIAGENS_MES,
    TBL_NOTURNO,
    TBL_ROTA_CRITICA,
    TBL_IDADE_FROTA,
    TBL_PCT_TERCEIROS

)


# =========================================================
# MAPA PRODUTO
# =========================================================

MAPA_PRODUTO = {

    "RCTR-C": "f_rctr",
    "RC-DC": "f_rcdc",
    "TN": "f_tn",
    "TI": "f_ti"

}


# =========================================================
# FATOR VIAGENS
# =========================================================

def calcular_fator_viagens(

    viagens,
    produto

):

    campo = MAPA_PRODUTO[
        produto
    ]

    return TBL_VIAGENS_MES.get(
        viagens,
        {}
    ).get(
        campo,
        1.00
    )


# =========================================================
# FATOR NOTURNO
# =========================================================

def calcular_fator_noturno(

    noturno,
    produto

):

    campo = MAPA_PRODUTO[
        produto
    ]

    return TBL_NOTURNO.get(
        noturno,
        {}
    ).get(
        campo,
        1.00
    )


# =========================================================
# FATOR ROTA CRÍTICA
# =========================================================

def calcular_fator_rota(

    rota,
    produto

):

    campo = MAPA_PRODUTO[
        produto
    ]

    return TBL_ROTA_CRITICA.get(
        rota,
        {}
    ).get(
        campo,
        1.00
    )


# =========================================================
# FATOR IDADE FROTA
# =========================================================

def calcular_fator_idade(

    idade,
    produto,
    modal="RODOVIARIO"

):

    campo = MAPA_PRODUTO[
        produto
    ]

    return TBL_IDADE_FROTA.get(
        modal,
        {}
    ).get(
        idade,
        {}
    ).get(
        campo,
        1.00
    )


# =========================================================
# FATOR TERCEIROS
# =========================================================

def calcular_fator_terceiros(

    terceiros,
    produto,
    modal="RODOVIARIO"

):

    campo = MAPA_PRODUTO[
        produto
    ]

    return TBL_PCT_TERCEIROS.get(
        modal,
        {}
    ).get(
        terceiros,
        {}
    ).get(
        campo,
        1.00
    )