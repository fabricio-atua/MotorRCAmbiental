// =========================================================
// EMPRESA GR
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const possuiGR =
        document.getElementById("possui_gr");

    const empresaGRDiv =
        document.getElementById("empresa_gr_div");

    const blocoCobTN =
         document.getElementById("bloco_cob_tn");

    const blocoCobTI =
        document.getElementById("bloco_cob_ti");

    function toggleEmpresaGR() {

        if (possuiGR.value === "Sim") {

            empresaGRDiv.style.display = "block";

        }

        else {

            empresaGRDiv.style.display = "none";

        }

    }

    toggleEmpresaGR();

    possuiGR.addEventListener(
        "change",
        toggleEmpresaGR
    );

});


// =========================================================
// CONTROLE PRODUTOS
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const produtoRCTR =
        document.getElementById("produto_rctr");

    const produtoRCDC =
        document.getElementById("produto_rcdc");

    const produtoTN =
        document.getElementById("produto_tn");

    const produtoTI =
        document.getElementById("produto_ti");

    const blocoRCTR =
        document.getElementById("bloco_rctr");

    const blocoRCDC =
        document.getElementById("bloco_rcdc");

    const blocoCobRCTR =
        document.getElementById("bloco_cob_rctr");

    const blocoCobRCDC =
        document.getElementById("bloco_cob_rcdc");

    const blocoModal =
        document.getElementById("bloco_modal");


const blocoTN =
    document.getElementById("bloco_tn");

const blocoTI =
    document.getElementById("bloco_ti");

const blocoCobTN =
    document.getElementById("bloco_cob_tn");

const blocoCobTI =
    document.getElementById("bloco_cob_ti");      


function controlarProdutos() {

    const rctr =
        produtoRCTR.checked;

    const rcdc =
        produtoRCDC.checked;

    const tn =
        produtoTN.checked;

    const ti =
        produtoTI.checked;

    // =============================================
    // RESETA TODOS
    // =============================================

    produtoRCTR.disabled = false;
    produtoRCDC.disabled = false;
    produtoTN.disabled = false;
    produtoTI.disabled = false;

    // =============================================
    // TN = EXCLUSIVO
    // =============================================

    if (tn) {

        produtoRCTR.disabled = true;
        produtoRCDC.disabled = true;
        produtoTI.disabled = true;

    }

    // =============================================
    // TI = EXCLUSIVO
    // =============================================

    if (ti) {

        produtoRCTR.disabled = true;
        produtoRCDC.disabled = true;
        produtoTN.disabled = true;

    }

    // =============================================
    // RCTR/RC-DC PODEM COMBINAR
    // MAS BLOQUEIAM TN E TI
    // =============================================

    if (rctr || rcdc) {

        produtoTN.disabled = true;
        produtoTI.disabled = true;

    }
    // =============================================
    // EXIBIÇÃO BLOCOS
    // =============================================

    // =============================================
    // RCTR
    // =============================================

    blocoRCTR.style.display =
        rctr
        ? "block"
        : "none";

    blocoCobRCTR.style.display =
        rctr
        ? "block"
        : "none";

    // =============================================
    // RC-DC
    // =============================================

    blocoRCDC.style.display =
        rcdc
        ? "block"
        : "none";

    blocoCobRCDC.style.display =
        rcdc
        ? "block"
        : "none";

    // =============================================
    // TN
    // =============================================

    blocoTN.style.display =
        tn
        ? "block"
        : "none";

    blocoCobTN.style.display =
        tn
        ? "block"
        : "none";

    // =============================================
    // TI
    // =============================================

    blocoTI.style.display =
        ti
        ? "block"
        : "none";

    blocoCobTI.style.display =
        ti
        ? "block"
        : "none";

     // =============================================
    // MODAL TI
    // =============================================

    blocoModal.style.display =
        ti
        ? "block"
        : "none";

}

// =====================================================
// EVENTOS
// =====================================================

document
.querySelectorAll(".produto-check")
.forEach(item => {

    item.addEventListener(
        "change",
        controlarProdutos
    );

});

controlarProdutos();

});


// =========================================================
// REMOVER LINHA
// =========================================================

function removerLinha(btn) {

    const row = btn.closest("tr");

    const tbody = row.parentNode;

    if (tbody.rows.length > 1) {

        row.remove();

        atualizarOpcoesCobertura();

        atualizarOpcoesMercadoria();

        calcularMixTotal();

        calcularRotasTotal();

    }

}

// =========================================================
// ADICIONAR MERCADORIA
// =========================================================

function adicionarMercadoria() {

    const tabela =
        document.querySelector(
            "#tabelaMercadorias tbody"
        );

    const primeiraLinha =
        tabela.rows[0];

    const novaLinha =
        primeiraLinha.cloneNode(true);

    novaLinha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = 0;

    });

    novaLinha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

        select.value = "";

    });

    tabela.appendChild(novaLinha);

    atualizarOpcoesMercadoria();

}

// =========================================================
// ADICIONAR ROTA
// =========================================================

function adicionarRota() {

    const tabela =
        document.querySelector(
            "#tabelaRotas tbody"
        );

    const primeiraLinha =
        tabela.rows[0];

    const novaLinha =
        primeiraLinha.cloneNode(true);

    novaLinha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = 0;

    });

    novaLinha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

    });

    tabela.appendChild(novaLinha);

}

// =========================================================
// COBERTURA RCTR
// =========================================================

function adicionarCobRCTR() {

    const tabela =
        document.querySelector(
            "#tabelaCobRCTR tbody"
        );

    if (tabela.rows.length >= 5) {

        alert("Máximo 5 coberturas RCTR");

        return;

    }

    const linha =
        tabela.rows[0].cloneNode(true);

    linha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = 0;

    });

    linha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

        select.value = "";

    });

    tabela.appendChild(linha);

    atualizarOpcoesCobertura();

}


// =========================================================
// COBERTURA RCDC
// =========================================================

function adicionarCobRCDC() {

    const tabela =
        document.querySelector(
            "#tabelaCobRCDC tbody"
        );

    if (tabela.rows.length >= 4) {

        alert("Máximo 4 coberturas RC-DC");

        return;

    }

    const linha =
        tabela.rows[0].cloneNode(true);

    linha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = 0;

    });

    linha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

        select.value = "";

    });

    tabela.appendChild(linha);

    atualizarOpcoesCobertura();

}


// =========================================================
// MIX MERCADORIAS
// =========================================================

function calcularMixTotal() {

    const mixes =
        document.querySelectorAll(
            'input[name="mix[]"]'
        );

    let total = 0;

    mixes.forEach(input => {

        total += parseFloat(
            input.value || 0
        );

    });

    const span =
        document.getElementById(
            "mixTotal"
        );

    if (span) {

        span.innerHTML =
            total.toFixed(2) + "%";

        if (total > 100) {

            span.className =
                "badge bg-danger";

        }

        else if (total < 100) {

            span.className =
                "badge bg-warning text-dark";

        }

        else {

            span.className =
                "badge bg-success";

        }

    }

}


// =========================================================
// TOTAL ROTAS
// =========================================================

function calcularRotasTotal() {

    const percentuais =
        document.querySelectorAll(
            'input[name="percentual[]"]'
        );

    let total = 0;

    percentuais.forEach(input => {

        total += parseFloat(
            input.value || 0
        );

    });

    const span =
        document.getElementById(
            "rotasTotal"
        );

    if (span) {

        span.innerHTML =
            total.toFixed(2) + "%";

        if (total > 100) {

            span.className =
                "badge bg-danger";

        }

        else if (total < 100) {

            span.className =
                "badge bg-warning text-dark";

        }

        else {

            span.className =
                "badge bg-success";

        }

    }

}


// =========================================================
// COBERTURAS DUPLICADAS
// =========================================================

function atualizarOpcoesCobertura() {

    // =====================================================
    // RCTR
    // =====================================================

    const selectsRCTR =
        document.querySelectorAll(
            'select[name="cob_rctr[]"]'
        );

    const selecionadosRCTR = [];

    selectsRCTR.forEach(select => {

        if (select.value !== "") {

            selecionadosRCTR.push(
                select.value
            );

        }

    });

    selectsRCTR.forEach(select => {

        const valorAtual = select.value;

        Array.from(select.options)
        .forEach(option => {

            if (

                option.value !== ""

                &&

                option.value !== valorAtual

                &&

                selecionadosRCTR.includes(
                    option.value
                )

            ) {

                option.hidden = true;

            }

            else {

                option.hidden = false;

            }

        });

    });

    // =====================================================
    // RCDC
    // =====================================================

    const selectsRCDC =
        document.querySelectorAll(
            'select[name="cob_rcdc[]"]'
        );

    const selecionadosRCDC = [];

    selectsRCDC.forEach(select => {

        if (select.value !== "") {

            selecionadosRCDC.push(
                select.value
            );

        }

    });

    selectsRCDC.forEach(select => {

        const valorAtual = select.value;

        Array.from(select.options)
        .forEach(option => {

            if (

                option.value !== ""

                &&

                option.value !== valorAtual

                &&

                selecionadosRCDC.includes(
                    option.value
                )

            ) {

                option.hidden = true;

            }

            else {

                option.hidden = false;

            }

        });

    });

    // =====================================================
    // TN
    // =====================================================

    const selectsTN =
        document.querySelectorAll(
            'select[name="cobertura_tn[]"]'
        );

    const selecionadosTN = [];

    selectsTN.forEach(select => {

        if (select.value !== "") {

            selecionadosTN.push(
                select.value
            );

        }

    });

    selectsTN.forEach(select => {

        const valorAtual = select.value;

        Array.from(select.options)
        .forEach(option => {

            if (

                option.value !== ""

                &&

                option.value !== valorAtual

                &&

                selecionadosTN.includes(
                    option.value
                )

            ) {

                option.hidden = true;

            }

            else {

                option.hidden = false;

            }

        });

    });

    // =====================================================
    // TI
    // =====================================================

    const selectsTI =
        document.querySelectorAll(
            'select[name="cobertura_ti[]"]'
        );

    const selecionadosTI = [];

    selectsTI.forEach(select => {

        if (select.value !== "") {

            selecionadosTI.push(
                select.value
            );

        }

    });

    selectsTI.forEach(select => {

        const valorAtual = select.value;

        Array.from(select.options)
        .forEach(option => {

            if (

                option.value !== ""

                &&

                option.value !== valorAtual

                &&

                selecionadosTI.includes(
                    option.value
                )

            ) {

                option.hidden = true;

            }

            else {

                option.hidden = false;

            }

        });

    });

}




// =========================================================
// MERCADORIAS DUPLICADAS
// =========================================================

function atualizarOpcoesMercadoria() {

    const selects =
        document.querySelectorAll(
            'select[name="mercadoria[]"]'
        );

    const selecionados = [];

    selects.forEach(select => {

        if (select.value !== "") {

            selecionados.push(
                select.value
            );

        }

    });

    selects.forEach(select => {

        const valorAtual =
            select.value;

        Array.from(select.options)
        .forEach(option => {

            if (option.value === "") {

                option.hidden = false;

                return;

            }

            if (

                option.value !== valorAtual

                &&

                selecionados.includes(
                    option.value
                )

            ) {

                option.hidden = true;

            }

            else {

                option.hidden = false;

            }

        });

    });

}


// =========================================================
// EVENTOS GLOBAIS
// =========================================================

document.addEventListener(
    "change",
    function (e) {

        if (

            e.target.name === "cob_rctr[]"

            ||

            e.target.name === "cob_rcdc[]"

            ||

            e.target.name === "cobertura_tn[]"

            ||

            e.target.name === "cobertura_ti[]"

        ) {

            atualizarOpcoesCobertura();

        }

        if (

            e.target.name === "mercadoria[]"

        ) {

            atualizarOpcoesMercadoria();

        }

    }
);

document.addEventListener(
    "input",
    function (e) {

        if (e.target.name === "mix[]") {

            calcularMixTotal();

        }

        if (e.target.name === "percentual[]") {

            calcularRotasTotal();

        }

    }
);


// =========================================================
// LOADING
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.querySelector("form");

        const botao =
            document.querySelector(
                'button[type="submit"]'
            );

        form.addEventListener(
            "submit",
            function () {

                botao.disabled = true;

                botao.innerHTML = `
                    <span class="spinner-border spinner-border-sm"></span>
                    Calculando...
                `;

            }
        );

    }
);


// =========================================================
// INIT
// =========================================================

window.onload = function () {

    calcularMixTotal();

    calcularRotasTotal();

    atualizarOpcoesCobertura();

    atualizarOpcoesMercadoria();

};
// =====================================================
// COBERTURAS TN
// =====================================================

function adicionarCoberturaTN() {

    let tabela =
        document.querySelector(
            "#tbody_cob_tn"
        );

    let linha =
        tabela.rows[0].cloneNode(true);

    linha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = "";

    });

    linha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

        select.value = "";

    });

    tabela.appendChild(linha);

    atualizarOpcoesCobertura();

}

// =====================================================
// COBERTURAS TI
// =====================================================

function adicionarCoberturaTI() {

    let tabela =
        document.querySelector(
            "#tbody_cob_ti"
        );

    let linha =
        tabela.rows[0].cloneNode(true);

    linha
    .querySelectorAll("input")
    .forEach(input => {

        input.value = "";

    });

    linha
    .querySelectorAll("select")
    .forEach(select => {

        select.selectedIndex = 0;

        select.value = "";

    });

    tabela.appendChild(linha);

    atualizarOpcoesCobertura();

}

// =====================================================
// ENVIAR COTAÇÃO API
// =====================================================

async function enviarCotacao() {

    try {

        console.clear()

        console.log("================================")
        console.log("NOVA COTAÇÃO")
        console.log("================================")

        // =================================================
        // FUNÇÃO AUXILIAR
        // =================================================

        function getFloat(selector) {

            const el = document.querySelector(selector)

            if (!el) return 0

            const valor = parseFloat(el.value)

            return isNaN(valor)
                ? 0
                : valor

        }

        function getValue(selector) {

            const el = document.querySelector(selector)

            if (!el) return ""

            return el.value

        }

        // =================================================
        // PRODUTOS
        // =================================================

        const produtos = []

        document
            .querySelectorAll(".produto-check:checked")
            .forEach(item => {

                produtos.push(item.value)

            })

        console.log("PRODUTOS:", produtos)

        // =================================================
        // PAYLOAD BASE
        // =================================================

        const payload = {

            usuario: {

                nome: "Fabricio Lopes"

            },

            produtos: produtos,

            comissao:
                getFloat('[name="comissao"]'),

            possui_gr:
                getValue('[name="possui_gr"]'),

            empresa_gr:
                getValue('[name="empresa_gr"]'),

            faixa_noturna:
                getValue('[name="faixa_noturna"]'),

            rota_critica:
                getValue('[name="rota_critica"]'),

            idade_frota:
                getValue('[name="idade_frota"]'),

            pct_terceiros:
                getValue('[name="pct_terceiros"]'),

            valor_sinistros:
                getFloat('[name="valor_sinistros"]'),

            mercadorias: [],

            rotas: [],

            coberturas_adicionais: []

        }

        // =================================================
        // RCTR-C
        // =================================================

        if (produtos.includes("RCTR-C")) {

            payload.viagens_mes_rctr =
                getValue('[name="viagens_mes_rctr"]')

            payload.valor_mensal_rctr =
                getFloat('[name="valor_mensal_rctr"]')

        }

        // =================================================
        // RC-DC
        // =================================================

        if (produtos.includes("RC-DC")) {

            payload.viagens_mes_rcdc =
                getValue('[name="viagens_mes_rcdc"]')

            payload.valor_mensal_rcdc =
                getFloat('[name="valor_mensal_rcdc"]')

        }

        // =================================================
        // TN
        // =================================================

        if (produtos.includes("TN")) {

            payload.viagens_mes_tn =
                getValue('[name="viagens_mes_tn"]')

            payload.valor_mensal_tn =
                getFloat('[name="valor_mensal_tn"]')

            payload.distancia_tn =
                getValue('[name="distancia_tn"]')

        }

        // =================================================
        // TI
        // =================================================

        if (produtos.includes("TI")) {

            payload.viagens_mes_ti =
                getValue('[name="viagens_mes_ti"]')

            payload.valor_mensal_ti =
                getFloat('[name="valor_mensal_ti"]')

            payload.modal_ti =
                getValue('[name="modal_ti"]')

        }

        // =================================================
        // MERCADORIAS
        // =================================================

        document
            .querySelectorAll(
                '#tabelaMercadorias tbody tr'
            )
            .forEach(row => {

                const mercadoria = row.querySelector(
                    '[name="mercadoria[]"]'
                )?.value

                const mix = parseFloat(

                    row.querySelector(
                        '[name="mix[]"]'
                    )?.value || 0

                )

                if (mercadoria) {

                    payload.mercadorias.push({

                        codigo: mercadoria,

                        mix: mix

                    })

                }

            })

        // =================================================
        // ROTAS
        // =================================================

        document
            .querySelectorAll(
                '#tabelaRotas tbody tr'
            )
            .forEach(row => {

                const origem = row.querySelector(
                    '[name="origem[]"]'
                )?.value

                const destino = row.querySelector(
                    '[name="destino[]"]'
                )?.value

                if (origem && destino) {

                    payload.rotas.push({

                        origem: origem,

                        destino: destino

                    })

                }

            })

        // =================================================
        // COBERTURAS TN
        // =================================================

        document
            .querySelectorAll('#tbody_cob_tn tr')
            .forEach(row => {

                const cobertura = row.querySelector(
                    '[name="cobertura_tn[]"]'
                )?.value

                const lmi = parseFloat(

                    row.querySelector(
                        '[name="lmi_tn[]"]'
                    )?.value || 0

                )

                if (cobertura && lmi > 0) {

                    payload.coberturas_adicionais.push({

                        produto: "TN",

                        cobertura: cobertura,

                        lmi: lmi

                    })

                }

            })

        // =================================================
        // COBERTURAS TI
        // =================================================

        document
            .querySelectorAll('#tbody_cob_ti tr')
            .forEach(row => {

                const cobertura = row.querySelector(
                    '[name="cobertura_ti[]"]'
                )?.value

                const lmi = parseFloat(

                    row.querySelector(
                        '[name="lmi_ti[]"]'
                    )?.value || 0

                )

                if (cobertura && lmi > 0) {

                    payload.coberturas_adicionais.push({

                        produto: "TI",

                        cobertura: cobertura,

                        lmi: lmi

                    })

                }

            })

        // =================================================
        // COBERTURAS RCTR
        // =================================================

        document
            .querySelectorAll('#tabelaCobRCTR tbody tr')
            .forEach(row => {

                const cobertura = row.querySelector(
                    '[name="cob_rctr[]"]'
                )?.value

                const lmi = parseFloat(

                    row.querySelector(
                        '[name="lmi_rctr[]"]'
                    )?.value || 0

                )

                if (cobertura && lmi > 0) {

                    payload.coberturas_adicionais.push({

                        produto: "RCTR-C",

                        cobertura: cobertura,

                        lmi: lmi

                    })

                }

            })

        // =================================================
        // COBERTURAS RC-DC
        // =================================================

        document
            .querySelectorAll('#tabelaCobRCDC tbody tr')
            .forEach(row => {

                const cobertura = row.querySelector(
                    '[name="cob_rcdc[]"]'
                )?.value

                const lmi = parseFloat(

                    row.querySelector(
                        '[name="lmi_rcdc[]"]'
                    )?.value || 0

                )

                if (cobertura && lmi > 0) {

                    payload.coberturas_adicionais.push({

                        produto: "RC-DC",

                        cobertura: cobertura,

                        lmi: lmi

                    })

                }

            })

        // =================================================
        // DEBUG PAYLOAD
        // =================================================

        console.log("PAYLOAD FINAL:")
        console.log(payload)

        console.log(
            JSON.stringify(
                payload,
                null,
                4
            )
        )

        // =================================================
        // FETCH API
        // =================================================

        const response = await fetch(

            "/cotacao/transporte",

            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body: JSON.stringify(
                    payload
                )

            }

        )

        const resultado = await response.json()

        console.log("RESULTADO API:")
        console.log(resultado)

      
        // =================================================
        // HTML RESULTADO
        // =================================================

        let html = ''

        // =====================================================
        // RESULTADO PRINCIPAL
        // =====================================================

        if (

            resultado.resultado.principal &&
            resultado.resultado.principal.length > 0

        ) {

            html += `

            <div class="card mb-5 shadow">

                <div class="card-header bg-success text-white">

                    Resultado da Cotação

                </div>

                <div class="card-body">

                    <h5 class="mb-3">

                        Coberturas Básicas

                    </h5>

                    <div class="table-responsive">

                        <table class="table table-bordered table-striped table-hover">

                            <thead>

                                <tr>

            `

            Object.keys(

                resultado.resultado.principal[0]

            ).forEach(coluna => {

                html += `

                    <th>${coluna}</th>

                `

            })

            html += `

                                </tr>

                            </thead>

                            <tbody>

            `

            resultado.resultado.principal.forEach(linha => {

                html += `<tr>`

                Object.values(linha).forEach(valor => {

                    html += `

                        <td>${valor}</td>

                    `

                })

                html += `</tr>`

            })

            html += `

                            </tbody>

                        </table>

                    </div>

                </div>

            </div>

            `
        }

        // =====================================================
        // COBERTURAS ADICIONAIS
        // =====================================================

        if (

            resultado.resultado.coberturas &&
            resultado.resultado.coberturas.length > 0

        ) {

            html += `

            <div class="card mb-5 shadow">

                <div class="card-header bg-primary text-white">

                    Coberturas Adicionais

                </div>

                <div class="card-body">

                    <div class="table-responsive">

                        <table class="table table-bordered table-striped table-hover">

                            <thead>

                                <tr>

            `

            Object.keys(

                resultado.resultado.coberturas[0]

            ).forEach(coluna => {

                html += `

                    <th>${coluna}</th>

                `

            })

            html += `

                                </tr>

                            </thead>

                            <tbody>

            `

            resultado.resultado.coberturas.forEach(linha => {

                html += `<tr>`

                Object.values(linha).forEach(valor => {

                    html += `

                        <td>${valor}</td>

                    `

                })

                html += `</tr>`

            })

            html += `

                            </tbody>

                        </table>

                    </div>

                </div>

            </div>

            `
        }

        // =====================================================
        // TOTAL GERAL
        // =====================================================

        html += `

        <div class="alert alert-success mb-5 shadow">

            <h4 class="mb-0">

                TOTAL GERAL:

                <strong>

                    R$ ${resultado.resultado.total_geral}

                </strong>

            </h4>

        </div>

        `

        // =====================================================
        // MEMÓRIA DE CÁLCULO
        // =====================================================

        if (

            resultado.resultado.memoria_calculo &&
            resultado.resultado.memoria_calculo.length > 0

        ) {

            html += `

            <div class="card mb-5 mt-4 shadow">

                <div class="card-header bg-dark text-white">

                    <h5 class="mb-0">

                        Memória de Cálculo

                    </h5>

                </div>

                <div class="card-body">

                    <div class="table-responsive">

                        <table class="table table-bordered table-striped table-hover">

                            <thead class="table-success">

                                <tr>

                                    <th>Pergunta</th>

                                    <th>Resposta</th>

                                    <th>Fator</th>

                                    <th>Prêmio Evolutivo</th>

                                </tr>

                            </thead>

                            <tbody>

            `

            resultado.resultado.memoria_calculo.forEach(linha => {

                html += `

                <tr>

                    <td>${linha.Pergunta}</td>

                    <td>${linha.Resposta}</td>

                    <td>${linha.Fator}</td>

                    <td>

                        R$ ${linha.Premio}

                    </td>

                </tr>

                `

            })

            html += `

                            </tbody>

                        </table>

                    </div>

                </div>

            </div>

            `
        }

        // =====================================================
        // JSON FINAL API
        // =====================================================

        html += `

        <div class="card mb-5 shadow">

            <div class="card-header bg-secondary text-white">

                JSON FINAL API

            </div>

            <div class="card-body">

                <pre style="
                    font-size:12px;
                    max-height:700px;
                    overflow:auto;
                ">

        ${JSON.stringify(resultado, null, 4)}

                </pre>

            </div>

        </div>

        `

        // =====================================================
        // RENDER FINAL
        // =====================================================

        document.getElementById(
            "resultadoCotacao"
        ).innerHTML = html

    }
   
    catch (erro) {

        console.error(erro)

        alert("Erro ao calcular cotação")

    }

}