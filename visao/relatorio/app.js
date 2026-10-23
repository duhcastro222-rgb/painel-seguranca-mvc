/* Relatório cruzado: GET /api/relatorio/<nome> (aceita ?nome= na URL) */
(function () {
  "use strict";

  var campoNome = document.getElementById("nome");
  var msg = document.getElementById("msg-relatorio");
  var resultado = document.getElementById("resultado");

  function gerarRelatorio(nome) {
    resultado.classList.add("esconder");
    CS.mostrarMensagem(msg, "info", "Consultando MySQL e MongoDB…");

    // encodeURIComponent: o nome vai dentro da URL, então é codificado
    CS.api("/api/relatorio/" + encodeURIComponent(nome))
      .then(function (r) {
        msg.className = "mensagem";
        mostrarAtivo(r.ativo, nome);
        mostrarVulnerabilidades(r.vulnerabilidades);
        resultado.classList.remove("esconder");
        history.replaceState(null, "", "?nome=" + encodeURIComponent(nome));
      })
      .catch(function (erro) {
        CS.mostrarMensagem(msg, erro.status === 404 ? "alerta" : "erro", erro.message);
      });
  }

  function mostrarAtivo(a, nome) {
    var ficha = document.getElementById("ficha-ativo");
    document.getElementById("titulo-ativo").textContent = nome;
    if (!a) {
      // existe vulnerabilidade no Mongo, mas o ativo foi removido do MySQL
      document.getElementById("badge-patch").innerHTML = '<span class="badge badge--neutro">fora do inventário</span>';
      ficha.innerHTML = '<div><dt>Aviso</dt><dd>Este ativo não está mais no MySQL; as vulnerabilidades abaixo ficaram órfãs no MongoDB.</dd></div>';
      return;
    }
    document.getElementById("badge-patch").innerHTML = CS.badgeStatus(a.status_patch);
    var campos = [
      ["ID", a.id], ["Tipo", a.tipo.replace(/_/g, " ")], ["IP interno", a.ip_interno],
      ["Setor", a.setor_responsavel], ["Sistema operacional", a.sistema_operacional],
      ["Última verificação", a.data_ultima_verificacao], ["Senha de acesso", a.tem_senha ? "definida (bcrypt)" : "não definida"]
    ];
    ficha.innerHTML = campos.map(function (c) {
      return "<div><dt>" + c[0] + "</dt><dd>" + CS.escapar(c[1]) + "</dd></div>";
    }).join("");
  }

  function mostrarVulnerabilidades(vulns) {
    var lista = document.getElementById("lista-vulnerabilidades");
    var abertas = vulns.filter(function (v) { return v.status === "aberta"; });
    var maior = abertas.reduce(function (m, v) { return Math.max(m, v.score_cvss); }, -1);

    document.getElementById("stat-total").textContent = vulns.length;
    document.getElementById("stat-abertas").textContent = abertas.length;
    document.getElementById("stat-maior").textContent = maior >= 0 ? maior.toFixed(1) : "—";

    if (vulns.length === 0) {
      CS.blocoEstado(lista, "Nenhuma vulnerabilidade registrada para este ativo.");
      return;
    }
    lista.innerHTML = vulns.map(function (v) { return CS.cartaoVulnerabilidade(v); }).join("");
  }

  document.getElementById("form-busca").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var nome = campoNome.value.trim();
    if (!nome) { CS.mostrarMensagem(msg, "erro", "Digite o nome de um ativo."); return; }
    gerarRelatorio(nome);
  });

  // sugestões de nome (autocompletar) vindas do MySQL
  CS.api("/api/ativos").then(function (ativos) {
    document.getElementById("lista-nomes").innerHTML = ativos.map(function (a) {
      return '<option value="' + CS.escapar(a.nome_ativo) + '"></option>';
    }).join("");
  }).catch(function () { /* sem sugestões; a busca continua funcionando */ });

  var nomeNaUrl = new URLSearchParams(location.search).get("nome");
  if (nomeNaUrl) {
    campoNome.value = nomeNaUrl;
    gerarRelatorio(nomeNaUrl);
  }
})();
