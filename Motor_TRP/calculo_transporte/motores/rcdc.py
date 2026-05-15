import pandas as pd

from calculo_transporte.taxas import (
    TAXA_BASE
)

from calculo_transporte.motores.coberturas import (
    calcular_coberturas
)

from calculo_transporte.utils.premio import (
    calcular_premio
)

from calculo_transporte.fatores.mercadoria import (
    calcular_fator_mercadoria
)

from calculo_transporte.fatores.uf import (
    calcular_fator_uf
)

# =========================================================
# MOTOR RC-DC
# =========================================================

def calcular_rcdc(

    dados,
    comissao,
    iof

):

    produto = "RC-DC"

    # =====================================================
    # TAXA BASE
    # =====================================================

    taxa_base = TAXA_BASE[
        produto
    ]

    # =====================================================
    # FATORES OPERACIONAIS
    # =====================================================

    fator_viagens = dados[
        "fator_viagens"
    ]

    fator_noturno = dados[
        "fator_noturno"
    ]

    fator_rota = dados[
        "fator_rota_critica"
    ]

    fator_distancia = dados[
        "fator_distancia"
    ]

    fator_idade = dados[
        "fator_idade"
    ]

    fator_terceiros = dados[
        "fator_terceiros"
    ]

    fator_sinistro = dados[
        "fator_sinistro"
    ]

    # =====================================================
    # FATOR MERCADORIA
    # =====================================================

    fator_mercadoria = (

        calcular_fator_mercadoria(

            mercadorias=
                dados["mercadorias"],

            produto=
                produto

        )

    )

    # =====================================================
    # FATOR UF
    # =====================================================

    fator_uf = (

        calcular_fator_uf(

            rotas=
                dados["rotas"],

            produto=
                produto

        )

    )

    # =====================================================
    # IMPORTÂNCIA SEGURADA
    # =====================================================

    importancia_segurada = (

        dados["valor_mensal"]
        * 12

    )

    # =====================================================
    # PRÊMIO BASE
    # =====================================================

    premio_base = (

        importancia_segurada
        * taxa_base

    )

    # =====================================================
    # MEMÓRIA DE CÁLCULO
    # =====================================================

    memoria = []

    premio_evolutivo = premio_base

    memoria.append({

        "Pergunta":
            "Taxa Base",

        "Resposta":
            produto,

        "Fator":
            round(
                taxa_base,
                6
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # VIAGENS
    # =====================================================

    premio_evolutivo *= fator_viagens

    memoria.append({

        "Pergunta":
            "Viagens",

        "Resposta":
            fator_viagens,

        "Fator":
            round(
                fator_viagens,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # NOTURNO
    # =====================================================

    premio_evolutivo *= fator_noturno

    memoria.append({

        "Pergunta":
            "Noturno",

        "Resposta":
            fator_noturno,

        "Fator":
            round(
                fator_noturno,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # ROTA CRÍTICA
    # =====================================================

    premio_evolutivo *= fator_rota

    memoria.append({

        "Pergunta":
            "Rota Crítica",

        "Resposta":
            fator_rota,

        "Fator":
            round(
                fator_rota,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # IDADE FROTA
    # =====================================================

    premio_evolutivo *= fator_idade

    memoria.append({

        "Pergunta":
            "Idade Frota",

        "Resposta":
            fator_idade,

        "Fator":
            round(
                fator_idade,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # TERCEIROS
    # =====================================================

    premio_evolutivo *= fator_terceiros

    memoria.append({

        "Pergunta":
            "% Terceiros",

        "Resposta":
            fator_terceiros,

        "Fator":
            round(
                fator_terceiros,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # SINISTRO
    # =====================================================

    premio_evolutivo *= fator_sinistro

    memoria.append({

        "Pergunta":
            "Sinistro",

        "Resposta":
            fator_sinistro,

        "Fator":
            round(
                fator_sinistro,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # MERCADORIA
    # =====================================================

    premio_evolutivo *= fator_mercadoria

    memoria.append({

        "Pergunta":
            "Mercadoria",

        "Resposta":
            "Mercadorias",

        "Fator":
            round(
                fator_mercadoria,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # UF
    # =====================================================

    premio_evolutivo *= fator_uf

    memoria.append({

        "Pergunta":
            "UF",

        "Resposta":
            "Rotas",

        "Fator":
            round(
                fator_uf,
                4
            ),

        "Premio":
            round(
                premio_evolutivo,
                2
            )

    })

    # =====================================================
    # TAXA FINAL
    # =====================================================

    taxa_final = (

        taxa_base

        * fator_viagens
        * fator_noturno
        * fator_rota
        * fator_distancia
        * fator_idade
        * fator_terceiros
        * fator_sinistro
        * fator_mercadoria
        * fator_uf

    )

    # =====================================================
    # PRÊMIO
    # =====================================================

    premio = calcular_premio(

        importancia_segurada=
            importancia_segurada,

        taxa=
            taxa_final,

        comissao=
            comissao,

        iof=
            iof

    )

    # =====================================================
    # COBERTURAS ADICIONAIS
    # =====================================================

    df_coberturas = calcular_coberturas(

        produto=
            produto,

        coberturas=
            dados.get(
                "coberturas_adicionais",
                []
            ),

        comissao=
            comissao,

        iof=
            iof

    )

    # =====================================================
    # COMISSÃO
    # =====================================================

    premio_comercial = (
        premio["premio_comercial"]
    )

    fator_comissao = (

        premio_comercial
        / premio_evolutivo

    )

    memoria.append({

        "Pergunta":
            "Comissão",

        "Resposta":
            f"{comissao}%",

        "Fator":
            round(
                fator_comissao,
                4
            ),

        "Premio":
            round(
                premio_comercial,
                2
            )

    })

    # =====================================================
    # IOF
    # =====================================================

    premio_final = (
        premio["premio_final"]
    )

    fator_iof = (

        premio_final
        / premio_comercial

    )

    memoria.append({

        "Pergunta":
            "IOF",

        "Resposta":
            f"{iof}%",

        "Fator":
            round(
                fator_iof,
                4
            ),

        "Premio":
            round(
                premio_final,
                2
            )

    })

    # =====================================================
    # COBERTURAS
    # =====================================================

    valor_coberturas = 0

    if not df_coberturas.empty:

        valor_coberturas = (

            df_coberturas[
                "Prêmio Final"
            ].sum()

        )

    memoria.append({

        "Pergunta":
            "Coberturas",

        "Resposta":
            "Adicionais",

        "Fator":
            "-",

        "Premio":
            round(
                valor_coberturas,
                2
            )

    })

    # =====================================================
    # TOTAL GERAL
    # =====================================================

    total_geral = (

        premio_final
        + valor_coberturas

    )

    memoria.append({

        "Pergunta":
            "TOTAL GERAL",

        "Resposta":
            produto,

        "Fator":
            "-",

        "Premio":
            round(
                total_geral,
                2
            )

    })

    # =====================================================
    # DATAFRAME PRINCIPAL
    # =====================================================

    df_principal = pd.DataFrame([{

        "Produto":
            produto,

        "Taxa Base":
            round(
                taxa_base,
                6
            ),

        "Taxa Final":
            round(
                taxa_final,
                6
            ),

        "IS Anual":
            round(
                importancia_segurada,
                2
            ),

        "Prêmio Risco":

            round(

                premio["premio_risco"],2
            ),

        "Prêmio Comercial":

            round(

                premio["premio_comercial"],2 
            ),

        "Prêmio Final":

            round(
                total_geral,
                2
            )

    }])

    # =====================================================
    # MEMÓRIA DATAFRAME
    # =====================================================

    df_memoria = pd.DataFrame(
        memoria
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
            df_memoria

    }