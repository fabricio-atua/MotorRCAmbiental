document.addEventListener('DOMContentLoaded', function () {

    function buscarCotacao() {
        const numero = document.getElementById('inputNumero').value.trim();
        if (!numero) {
            alert('Por favor, digite um número de cotação válido');
            return;
        }

        const tbody = document.getElementById('tabelaCorpo');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="no-results">Buscando cotações...</td>
            </tr>
        `;

        fetch('/consulta/api/cotacoes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `numero_cotacao=${encodeURIComponent(numero)}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na resposta do servidor');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="no-results" style="color: #dc3545;">${data.error}</td>
                    </tr>
                `;
                return;
            }

            if (data.data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="no-results">Nenhuma cotação encontrada</td>
                    </tr>
                `;
                return;
            }

            // Ordena por número de cotação 
            data.data.sort((a, b) => {
                if (a.numero_cotacao < b.numero_cotacao) return -1;
                if (a.numero_cotacao > b.numero_cotacao) return 1;
                
                // Se for a mesma cotação, ordena por versão (crescente)
                return a.versao_cotacao.localeCompare(b.versao_cotacao);
            });

            window.dadosCotacoes = data.data.map(item => {
                return {
                    ...item,
                    dados_json: JSON.parse(item.dados_json)
                };
            });

            tbody.innerHTML = data.data.map((item, index) => {
                const premio = parseFloat(item.premio_total);
                const premioFormatado = isNaN(premio) ? '—' : 
                    premio.toLocaleString('pt-BR', { 
                        style: 'currency', 
                        currency: 'BRL' 
                    });
    
                    const nomeSegurado = (() => {
                        try {
                            // Verifica múltiplos caminhos possíveis
                            const dados = window.dadosCotacoes[index].dados_json;
                            return dados?.dados_principais?.dados_segurado?.nome || 
                                   dados?.dados_segurado?.nome ||
                                   dados?.segurado?.nome ||
                                   '—';
                        } catch {
                            return '—';
                        }
                    })();
                
                return `
                    <tr id="linha-${index}">
                        <td>${item.numero_cotacao}</td>
                        <td>${item.versao_cotacao}</td>

                        <td>${
                            (() => {
                                try {
                                    let dataRaw = window.dadosCotacoes[index].dados_json?.dados_principais?.cotacao?.data_criacao;
                                    if (!dataRaw) return '—';

                                    // Converte "2025-05-06 10:24:35" → "2025-05-06T10:24:35"
                                    dataRaw = dataRaw.replace(' ', 'T');

                                    const data = new Date(dataRaw);
                                    return data.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
                                } catch {
                                    return '—';
                                }
                            })()
                        }</td>



                        <td>${nomeSegurado}</td>
                        <td>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span id="premio-${index}">${premioFormatado}</span>
                                <div style="display: flex; gap: 10px;">
                                    <button onclick="mostrarAlterar(${index})" 
                                        class="btn-alterar">Alterar</button>
                                    <div id="alterar-${index}" style="display: none; gap: 8px;">
                                        <input type="number" id="agravo-${index}" 
                                            placeholder="%" step="0.01"
                                            style="width: 80px; padding: 4px;">
                                        <button onclick="aplicarAgravo(${index}, ${premio}, '${item.numero_cotacao}')"
                                            class="btn-confirmar">Aplicar</button>
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        })
        .catch(error => {
            console.error('Erro:', error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="no-results" style="color: #dc3545;">
                        Erro ao buscar cotações: ${error.message}
                    </td>
                </tr>
            `;
        });
    }

    function mostrarAlterar(index, premioOriginal) {
        const alterarDiv = document.getElementById(`alterar-${index}`);
        if (alterarDiv.style.display === 'none' || alterarDiv.style.display === '') {
            alterarDiv.style.display = 'flex';
        } else {
            alterarDiv.style.display = 'none';
        }
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // APLICA DESCONTO/AGRAVO NO JSON COMPLETO E MOSTRA VALOR NA TELA  
    function aplicarAgravo(index, premioOriginal, numeroCotacao) {
        const input = document.getElementById(`agravo-${index}`);
        const agravo = parseFloat(input.value);

        if (isNaN(agravo)) {
            alert('Informe um valor numérico para o agravo/desconto');
            return;
        }

        const jsonData = window.dadosCotacoes[index];
        if (!jsonData || !jsonData.dados_json) {
            alert('Dados da cotação não encontrados.');
            return;
        }

        const detalhesDepurador = jsonData.dados_json.detalhes_depurador;
        if (!detalhesDepurador || !Array.isArray(detalhesDepurador)) {
            alert('Detalhes depurador não encontrados.');
            return;
        }

        // Cálculo do novo prêmio
        const iofItem = detalhesDepurador.find(item => item.resposta === 'IOF');
        const premioTotalItem = detalhesDepurador.find(item => item.fonte === 'Prêmio Total');
        
        if (!iofItem || !premioTotalItem) {
            alert('Dados necessários não encontrados na cotação.');
            return;
        }

        const iofFator = parseFloat(iofItem.relatividade);
        const premioTotal = parseFloat(premioTotalItem.premio);
        
        if (isNaN(iofFator) || isNaN(premioTotal)) {
            alert('Valores numéricos inválidos na cotação.');
            return;
        }

        const premioLiquido = premioTotal / iofFator;
        const premioLiquidoCorrigido = premioLiquido * (1 + agravo / 100);
        const novoPremioTotal = premioLiquidoCorrigido * iofFator;

        // Atualiza o front-end primeiro
        const premioFormatado = novoPremioTotal.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        document.getElementById(`premio-${index}`).innerText = premioFormatado;

        // Mostra o alerta de sucesso
        alert(`Cotação ${numeroCotacao} salva com sucesso!`);

        // Prepara os dados para enviar ao backend
        const dadosParaEnviar = {
            numero_cotacao: numeroCotacao,
            agravo_percentual: agravo,
            dados_json: jsonData.dados_json
        };

        // Envia para o backend
        fetch('/consulta/duplicar_cotacao', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dadosParaEnviar)
        })
        .then(response => {
            if (!response.ok) throw new Error('Erro na resposta do servidor');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    html: `Cotação atualizada:<br>
                        <strong>Novo prêmio:</strong> R$ ${premioFormatado}<br>
                        <strong>Variação:</strong> ${agravo > 0 ? '+' : ''}${agravo}%`,
                    confirmButtonText: 'OK'
                }).then(() => {
                    document.getElementById(`alterar-${index}`).style.display = 'none';
                    buscarCotacao(); // Recarrega os dados
                });
            } else {
                throw new Error(data.message || 'Erro ao processar');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            // Reverte a visualização em caso de erro
            document.getElementById(`premio-${index}`).innerText = 
                premioOriginal.toLocaleString('pt-BR', {minimumFractionDigits: 2});
            
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: error.message,
                confirmButtonText: 'Entendi'
            });
        });
    }

    // Permite buscar pressionando Enter
    const inputNumero = document.getElementById('inputNumero');
    if (inputNumero) {
        inputNumero.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                buscarCotacao();
            }
        });
    }

    // Expor funções para uso nos botões inline
    window.buscarCotacao = buscarCotacao;
    window.mostrarAlterar = mostrarAlterar;
    window.aplicarAgravo = aplicarAgravo;

});