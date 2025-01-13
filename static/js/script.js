// Criar as variaveis botao e formulario
const showFormBtn = document.getElementById("show-form-btn");
const formulario = document.getElementById("formulario");

// Adicionar o evento de clique ao botao
showFormBtn.addEventListener("click", () => {
  formulario.classList.remove("hidden"); // mostra o formulario
  showFormBtn.style.display = "none"; // esconde o botao
});
