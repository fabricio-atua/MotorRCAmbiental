document.addEventListener('DOMContentLoaded', function () {

    const tabela = document.getElementById('tabela-cotacoes');
    const tbody = tabela.querySelector('tbody');
    const btnCalcular = document.getElementById('btnCalcular');
    const btnAtualizar = document.getElementById('btnAtualizarCotacao');
    const processando = document.getElementById('processando');
    const mensagem = document.getElementById('mensagemCotacao');

    // ------------------------------------------------------------
    // Botão GRAVAR COTAÇÃO (versão 01)
    // ------------------------------------------------------------
    btnCalcular.addEventListener('click', function () {

        processando.style.display = 'inline-flex';
        mensagem.style.display = 'none';
        tabela.style.display = 'none';

        setTimeout(() => {
            carregarUltimaCotacao();
        }, 3000);
    });

    // ------------------------------------------------------------
    // Botão ATUALIZAR COTAÇÃO (gera versão 02)
    // ------------------------------------------------------------
    if (btnAtualizar) {
        btnAtualizar.addEventListener('click', function () {
            duplicarCotacaoComAgravo();
        });
    }

    // ------------------------------------------------------------
    // Busca última cotação
    // ------------------------------------------------------------
    function carregarUltimaCotacao() {

        fetch('/api/ultima_cotacao')
            .then(resp => {
                if (!resp.ok) throw new Error('Erro ao buscar última cotação');
                return resp.json();
            })
            .then(data => {

                processando.style.display = 'none';

                if (!data || !data.dados_json) {
                    mensagem.innerText = 'Nenhuma cotação encontrada.';
                    mensagem.style.display = 'block';
                    return;
                }

                tabela.style.display = 'table';

                window.dadosCotacoes = [{
                    ...data,
                    dados_json: typeof data.dados_json === 'string'
                        ? JSON.parse(data.dados_json)
                        : data.dados_json
                }];

                renderTabela();

                if (btnAtualizar) {
                    btnAtualizar.style.display = 'inline-block';
                }
            })
            .catch(err => {
                processando.style.display = 'none';
                console.error(err);
                mensagem.innerText = 'Erro ao carregar cotação.';
                mensagem.style.display = 'block';
            });
    }

    // ------------------------------------------------------------
    // Renderização da tabela
    // ------------------------------------------------------------
    function renderTabela() {

        tbody.innerHTML = '';

        window.dadosCotacoes.forEach((item, indexCotacao) => {

            const detalhes = item.dados_json.detalhes_depurador || [];

            function ultimaCobertura(detalhes, nome) {
                return [...detalhes]
                    .reverse()
                    .find(d => d.pergunta === 'Cobertura' && d.resposta === nome);
            }

            const coberturasBasicas = [];

            const limpeza = ultimaCobertura(detalhes, 'Custo de Limpeza: Remediações, Remoções e Descarte');
            if (limpeza) coberturasBasicas.push(limpeza);

            const danos = ultimaCobertura(detalhes, 'Danos Materiais');
            if (danos) coberturasBasicas.push(danos);


            coberturasBasicas.forEach((cob, idx) => {

                let premioBase = Number(cob.premio) || 0;

                const premioOriginal = premioBase;
                const premioFormatado = premioOriginal.toLocaleString('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                });

                const linhaId = `${indexCotacao}-${idx}`;

                tbody.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td>${item.numero_cotacao}</td>
                        <td>${item.versao_cotacao}</td>
                        <td>Básica</td>
                        <td>${cob.resposta}</td>
                        <td>${premioFormatado}</td>
                        <td>
                            <input type="number"
                                   class="agravo-input"
                                   data-cobertura="${cob.resposta}"
                                   data-premio="${premioOriginal}"
                                   placeholder="%"
                                   step="0.01"
                                   style="width:80px">
                        </td>
                        <td class="premio-final">${premioFormatado}</td>
                    </tr>
                `);
            });

            // --------------------------------------------------
            // COBERTURAS ADICIONAIS (DINÂMICAS)
            // --------------------------------------------------
            const adicionais = item.dados_json.coberturas_adicionais || [];

            adicionais.forEach((adc, idx) => {

                const premioBase = Number(adc.premio_total) || 0;

                const premioFormatado = premioBase.toLocaleString('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                });

                tbody.insertAdjacentHTML('beforeend', `
                    <tr>
                        <td>${item.numero_cotacao}</td>
                        <td>${item.versao_cotacao}</td>
                        <td>Adicional</td>
                        <td>${adc.descricao_cobertura}</td>
                        <td>${premioFormatado}</td>
                        <td>
                            <input type="number"
                                class="agravo-input"
                                data-tipo="adicional"
                                data-codigo="${adc.codigo_cobertura}"
                                data-premio="${premioBase}"
                                placeholder="%"
                                step="0.01"
                                style="width:80px">
                        </td>
                        <td class="premio-final">${premioFormatado}</td>
                    </tr>
                `);
            });

        });

        mensagem.innerText = 'Última cotação carregada com sucesso.';
        mensagem.style.display = 'block';
    }

    // ------------------------------------------------------------
    // Duplica cotação e gera nova versão no MySQL
    // ------------------------------------------------------------
    function duplicarCotacaoComAgravo() {

        const cotacao = window.dadosCotacoes[0];

        const ajustes = [];

        document.querySelectorAll('.agravo-input').forEach(input => {
            const agravo = parseFloat(input.value);
            if (isNaN(agravo)) return;

            
            if (input.dataset.tipo === 'adicional') {
                ajustes.push({
                    tipo: 'adicional',
                    codigo_cobertura: input.dataset.codigo,
                    agravo_percentual: agravo
                });
            } else {
                ajustes.push({
                    tipo: 'basica',
                    cobertura: input.dataset.cobertura,
                    agravo_percentual: agravo
                });
            }


        });

        if (!ajustes.length) {
            alert('Informe ao menos um desconto ou agravo.');
            return;
        }

        processando.style.display = 'inline-flex';

        fetch('/consulta/duplicar_cotacao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                numero_cotacao: cotacao.numero_cotacao,
                ajustes_recebidos: ajustes,   // NOME CORRETO
                dados_json: cotacao.dados_json
            })
        })
        .then(resp => resp.json())
        .then(result => {
            if (!result.success) {
                throw new Error(result.message);
            }
            carregarUltimaCotacao();
        })
        .catch(err => {
            console.error(err);
            alert('Erro ao atualizar cotação');
        });
    }


    // ------------------------------------------------------------
    // Atualiza prêmio final automaticamente ao digitar agravo/desconto
    // ------------------------------------------------------------
    document.addEventListener('input', function (event) {

        if (!event.target.classList.contains('agravo-input')) return;

        const input = event.target;
        const agravo = parseFloat(input.value) || 0;
        const premioOriginal = parseFloat(input.dataset.premio);

        const premioFinal = premioOriginal * (1 + agravo / 100);

        const tdPremioFinal = input
            .closest('tr')
            .querySelector('.premio-final');

        if (tdPremioFinal) {
            tdPremioFinal.innerText = premioFinal.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
        }
    });

});