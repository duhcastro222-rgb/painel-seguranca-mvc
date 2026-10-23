/* =========================================================================
   Peças usadas por todas as telas (vindas das interfaces-web):
   cabeçalho, menu, título em letras quadradas, CS.api() e helpers
   ========================================================================= */
(function () {
  "use strict";

  // Ordem dos painéis na navegação central. slug = nome da subpasta.
  var PAINEIS = [
    { slug: "index",            rotulo: "Início",            casa: true },
    { slug: "ativos",           rotulo: "Ativos (MySQL)" },
    { slug: "vulnerabilidades", rotulo: "Vulnerabilidades (MongoDB)" },
    { slug: "relatorio",        rotulo: "Relatório cruzado" },
    { slug: "reputacao",        rotulo: "Reputação de IPs" }
  ];

  var appAtual = document.body.dataset.app || "index";
  var ehCasa = document.body.dataset.depth !== "1";
  var prefixo = ehCasa ? "" : "../";

  function href(p) {
    if (p.casa) return prefixo + "index.html";
    return prefixo + p.slug + "/index.html";
  }

  // ---------- Cabeçalho + navegação ----------
  function montarTopo() {
    var itens = PAINEIS.map(function (p) {
      var ativo = (p.slug === appAtual) ? ' aria-current="page"' : "";
      return '<a class="nav__item" href="' + href(p) + '"' + ativo + ">" + p.rotulo + "</a>";
    }).join("");

    var topo = document.createElement("header");
    topo.className = "topo";
    topo.innerHTML =
      '<div class="topo__barra">' +
        '<a class="marca" href="' + prefixo + 'index.html">' +
          '<span class="marca__glifo">CS</span>' +
          '<span>' +
            '<span class="marca__nome">Painel de Segurança</span>' +
            '<span class="marca__sub">Coding for Security · RM 573427</span>' +
          "</span>" +
        "</a>" +
        '<span class="status-chip" id="status-bancos">' +
          '<span class="status-chip__pulso"></span>' +
          '<span id="status-bancos-texto">verificando bancos…</span>' +
          '<span aria-hidden="true">·</span>' +
          '<span id="relogio-topo" class="dado">--:--:--</span>' +
        "</span>" +
      "</div>" +
      '<nav class="nav" aria-label="Navegação entre painéis">' +
        '<div class="nav__lista">' + itens + "</div>" +
      "</nav>";

    document.body.insertBefore(topo, document.body.firstChild);
  }

  // ---------- Título em letras quadradas ----------
  // O que faz: troca o texto do h1 por um quadrado por letra
  // [OBS] o aria-label guarda o texto original para o leitor de tela
  function montarTitulo() {
    var h1 = document.querySelector("main h1");
    if (!h1) return;
    var texto = h1.textContent.trim();
    h1.setAttribute("aria-label", texto);
    h1.classList.add("titulo-quadrado");
    h1.innerHTML = texto.split(/\s+/).map(function (palavra) {
      var letras = palavra.split("").map(function (letra) {
        return '<span class="letra">' + escapar(letra) + "</span>";
      }).join("");
      return '<span class="palavra" aria-hidden="true">' + letras + "</span>";
    }).join("");
  }

  // ---------- Relógio ao vivo ----------
  function iniciarRelogio() {
    var el = document.getElementById("relogio-topo");
    function tique() { el.textContent = new Date().toLocaleTimeString("pt-BR"); }
    tique();
    setInterval(tique, 1000);
  }

  // ---------- Indicador dos bancos (GET /api/saude) ----------
  function verificarBancos() {
    var texto = document.getElementById("status-bancos-texto");
    var chip = document.getElementById("status-bancos");
    api("/api/saude").then(function () {
      texto.textContent = "MySQL e MongoDB online";
      chip.classList.remove("status-chip--erro");
    }).catch(function () {
      texto.textContent = "banco indisponível";
      chip.classList.add("status-chip--erro");
    });
  }

  // ---------- CS.api: único jeito de as telas falarem com o servidor ----------
  // O que faz: faz o fetch e, se der erro, lança a mensagem que a API mandou
  // Por que faz: toda tela trata erro igual e mostra uma frase compreensível
  function api(url, metodo, corpo) {
    var opcoes = { method: metodo || "GET", headers: {} };
    if (corpo !== undefined) {
      opcoes.headers["Content-Type"] = "application/json";
      opcoes.body = JSON.stringify(corpo);
    }
    return fetch(url, opcoes)
      .catch(function () {
        // fetch só cai aqui quando nem chegou resposta (servidor parado)
        throw new Error("Não foi possível falar com o servidor. Confira se o app.py está rodando.");
      })
      .then(function (resposta) {
        return resposta.json().catch(function () { return null; }).then(function (dados) {
          if (!resposta.ok) {
            var msg = (dados && dados.erro) ? dados.erro : "Erro inesperado (HTTP " + resposta.status + ").";
            var erro = new Error(msg);
            erro.status = resposta.status;
            throw erro;
          }
          return dados;
        });
      });
  }

  // ---------- Helpers de estado e de formatação ----------
  function escapar(txt) {
    return String(txt == null ? "" : txt)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // linha única ocupando a tabela inteira: "carregando", "vazio" ou "erro"
  function linhaEstado(tbody, colunas, texto, tipo) {
    var cor = tipo === "erro" ? ' style="color:var(--sev-critica);font-style:normal"' : "";
    tbody.innerHTML = '<tr class="vazio"><td colspan="' + colunas + '"' + cor + ">" +
      escapar(texto) + "</td></tr>";
  }

  // bloco de estado para listas que não são tabela (cartões)
  function blocoEstado(el, texto, tipo) {
    var cor = tipo === "erro" ? "mensagem--erro" : "mensagem--info";
    el.innerHTML = '<div class="mensagem visivel ' + cor + '">' + escapar(texto) + "</div>";
  }

  // caixa de mensagem (ok | erro | alerta | info) que já existe na página
  function mostrarMensagem(el, tipo, texto) {
    el.className = "mensagem visivel mensagem--" + tipo;
    el.textContent = texto;
  }

  // badge de severidade: baixa | media | alta | critica
  function badgeSeveridade(nivel) {
    var mapa = { baixa: "Baixa", media: "Média", alta: "Alta", critica: "Crítica" };
    var chave = String(nivel || "").toLowerCase();
    return '<span class="badge badge--' + escapar(chave) + '">' + escapar(mapa[chave] || nivel) + "</span>";
  }

  // badge de status genérico com dicionário de cores
  var CORES_STATUS = {
    corrigida: "ok", em_dia: "ok", BAIXO: "ok",
    aberta: "critica", critico: "critica", ALTO: "critica",
    em_correcao: "media", pendente: "media", MEDIO: "media",
    INVALIDO: "neutro", ERRO: "neutro"
  };
  var ROTULOS = {
    em_dia: "Em dia", pendente: "Pendente", critico: "Crítico",
    aberta: "Aberta", em_correcao: "Em correção", corrigida: "Corrigida",
    BAIXO: "Baixo", MEDIO: "Médio", ALTO: "Alto", INVALIDO: "Inválido", ERRO: "Erro"
  };
  function badgeStatus(status) {
    var cor = CORES_STATUS[status] || "neutro";
    return '<span class="badge badge--' + cor + '">' + escapar(ROTULOS[status] || status) + "</span>";
  }

  // cartão de vulnerabilidade (tela de vulnerabilidades e relatório)
  // "detalhes" é percorrido chave a chave porque muda em cada categoria
  function cartaoVulnerabilidade(v, rodape) {
    var detalhes = Object.keys(v.detalhes || {}).map(function (chave) {
      return "<li><span class=\"txt-muted\">" + escapar(chave.replace(/_/g, " ")) + ":</span> " +
        escapar(v.detalhes[chave]) + "</li>";
    }).join("");
    return '<article class="cartao-vuln cartao-vuln--' + escapar(v.severidade) + '">' +
      '<div class="cartao-vuln__topo">' +
        '<span class="cartao-vuln__cve">' + escapar(v.cve_id || "sem CVE (falha de configuração)") + "</span>" +
        badgeSeveridade(v.severidade) +
      "</div>" +
      '<p class="cartao-vuln__desc">' + escapar(v.descricao) + "</p>" +
      '<div class="cartao-vuln__meta">' +
        "<span>" + escapar(v.ativo_relacionado) + "</span>" +
        "<span>CVSS " + Number(v.score_cvss).toFixed(1) + "</span>" +
        "<span>" + escapar(v.categoria.replace(/_/g, " ")) + "</span>" +
        "<span>" + escapar(v.data_deteccao) + "</span>" +
      "</div>" +
      (detalhes ? '<ul class="cartao-vuln__detalhes">' + detalhes + "</ul>" : "") +
      '<div class="cartao-vuln__rodape">' + badgeStatus(v.status) + (rodape || "") + "</div>" +
    "</article>";
  }

  window.CS = {
    api: api,
    escapar: escapar,
    linhaEstado: linhaEstado,
    blocoEstado: blocoEstado,
    mostrarMensagem: mostrarMensagem,
    badgeSeveridade: badgeSeveridade,
    badgeStatus: badgeStatus,
    cartaoVulnerabilidade: cartaoVulnerabilidade
  };

  // ---------- Boot ----------
  montarTopo();
  montarTitulo();
  iniciarRelogio();
  verificarBancos();
})();
