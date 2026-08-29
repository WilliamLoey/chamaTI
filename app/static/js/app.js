/* ============================================================================
   ChamaTI — JavaScript da camada View.
   Nenhuma regra de negócio vive aqui: o front-end apenas antecipa o erro para
   o usuário. A validação que vale é sempre a do servidor (ver app/services).
   ========================================================================== */
(function () {
  "use strict";

  const ANEXO_MAX_MB = 5;

  document.addEventListener("DOMContentLoaded", function () {
    menuResponsivo();
    focarCampoComErro();
    validarAnexo();
    campoSolucaoCondicional();
    confirmarAcoes();
    evitarEnvioDuplicado();
    animarBarras();
  });

  /* Menu em telas pequenas -------------------------------------------------- */
  function menuResponsivo() {
    const botao = document.querySelector("[data-menu-alternar]");
    const menu = document.getElementById("menu-principal");
    if (!botao || !menu) return;

    botao.addEventListener("click", function () {
      const aberto = menu.classList.toggle("menu--aberto");
      botao.setAttribute("aria-expanded", String(aberto));
    });
  }

  /* Rola até o campo com problema e coloca o foco nele --------------------- */
  function focarCampoComErro() {
    const alerta = document.querySelector("[data-campo-erro]");
    if (!alerta) return;

    const nomeCampo = alerta.getAttribute("data-campo-erro");
    if (!nomeCampo) return;

    const campo = document.getElementById(nomeCampo);
    if (!campo) return;

    campo.scrollIntoView({ behavior: "smooth", block: "center" });
    campo.focus({ preventScroll: true });
  }

  /* Avisa sobre o tamanho do anexo antes de enviar -------------------------- */
  function validarAnexo() {
    const form = document.querySelector("[data-validar-anexo]");
    if (!form) return;

    const entrada = form.querySelector('input[type="file"]');
    const aviso = form.querySelector("[data-erro-anexo]");
    if (!entrada || !aviso) return;

    const limiteMb = Number(form.getAttribute("data-validar-anexo")) || ANEXO_MAX_MB;
    const limiteBytes = limiteMb * 1024 * 1024;

    function conferir() {
      const grandes = Array.from(entrada.files || []).filter(function (a) {
        return a.size > limiteBytes;
      });

      if (grandes.length === 0) {
        aviso.hidden = true;
        aviso.textContent = "";
        entrada.closest(".campo").classList.remove("campo--invalido");
        return true;
      }

      const nomes = grandes.map(function (a) {
        return a.name + " (" + (a.size / 1048576).toFixed(1) + " MB)";
      }).join(", ");
      aviso.textContent =
        "Arquivo acima do limite de " + limiteMb + " MB: " + nomes +
        ". Compacte o arquivo ou envie uma imagem menor.";
      aviso.hidden = false;
      entrada.closest(".campo").classList.add("campo--invalido");
      return false;
    }

    entrada.addEventListener("change", conferir);
    form.addEventListener("submit", function (evento) {
      if (!conferir()) {
        evento.preventDefault();
        aviso.scrollIntoView({ behavior: "smooth", block: "center" });
        entrada.focus({ preventScroll: true });
      }
    });
  }

  /* A solução só é pedida quando o status escolhido é "Resolvido" ----------- */
  function campoSolucaoCondicional() {
    const seletor = document.querySelector("[data-status-seletor]");
    const campo = document.querySelector("[data-campo-solucao]");
    if (!seletor || !campo) return;

    function alternar() {
      const resolvendo = seletor.value === "Resolvido";
      campo.hidden = !resolvendo;
      const area = campo.querySelector("textarea");
      if (area) area.required = resolvendo;
    }

    seletor.addEventListener("change", alternar);
    alternar();
  }

  /* Ações que mudam o estado do chamado pedem confirmação ------------------- */
  function confirmarAcoes() {
    document.querySelectorAll("[data-confirmar]").forEach(function (form) {
      form.addEventListener("submit", function (evento) {
        if (!window.confirm(form.getAttribute("data-confirmar"))) {
          evento.preventDefault();
        }
      });
    });
  }

  /* Feedback imediato: desabilita o botão e avisa que está processando ------ */
  function evitarEnvioDuplicado() {
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        const botao = form.querySelector("[data-envio]");
        if (!botao || form.querySelector(":invalid")) return;
        botao.disabled = true;
        botao.textContent = "Enviando…";
      });
    });
  }

  /* Barras do painel proporcionais ao maior valor da série ------------------ */
  function animarBarras() {
    document.querySelectorAll(".barras").forEach(function (lista) {
      const preenchimentos = Array.from(lista.querySelectorAll(".barra__preenchimento"));
      const maior = preenchimentos.reduce(function (max, el) {
        return Math.max(max, Number(el.getAttribute("data-total")) || 0);
      }, 0);

      preenchimentos.forEach(function (el) {
        const total = Number(el.getAttribute("data-total")) || 0;
        const percentual = maior > 0 ? (total / maior) * 100 : 0;
        window.requestAnimationFrame(function () {
          el.style.width = percentual.toFixed(1) + "%";
        });
      });
    });
  }
})();
