function preencherCanal() {
    const canalSelect = document.getElementById('canal_select');
    const nomeInput = document.getElementById('nome_canal');
    const selectedOption = canalSelect.options[canalSelect.selectedIndex];

    const nome = selectedOption.getAttribute('data-nome') || "";
    nomeInput.value = nome;
}