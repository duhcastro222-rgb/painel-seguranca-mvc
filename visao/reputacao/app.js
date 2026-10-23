/* Reputação de IPs: quem chama o ip-api e grava o cache é o servidor */
(function () {
  "use strict";

  var campoIps = document.getElementById("ips");
  var corpo = document.getElementById("corpo-ips");
  var msg = document.getElementById("msg-ips");
  var COLUNAS = 6;

  function mostrarRelatorio(r) {
    document.getElementById("info-relatorio").textContent =
      "Análise de " + r.data_da_analise + " · " + r.total_de_ips + " IP(s) · " +
      r.consultas_na_api + " consulta(s) na API · " + r.respostas_do_cache + " do cache";

    var resumo = r.resumo_por_risco;
    ["ALTO", "MEDIO", "BAIXO"].forEach(function (risco) {
      document.getElementById("stat-" + risco).textContent = resumo[risco] || 0;
    });
    document.getElementById("stat-INVALIDO").textContent = (resumo.INVALIDO || 0) + (resumo.ERRO || 0);

    if (r.resultados.length === 0) {
      CS.linhaEstado(corpo, COLUNAS, "O relatório não tem IPs.");
      return;
    }
    var rotulosOrigem = { api: "API", cache: "cache" };
    corpo.innerHTML = r.resultados.map(function (item) {
      return "<tr>" +
        '<td class="dado">' + CS.escapar(item.ip) + "</td>" +
        "<td>" + CS.badgeStatus(item.risco) + "</td>" +
        "<td>" + CS.escapar(item.motivo) + "</td>" +
        "<td>" + CS.escapar(item.pais || "—") + "</td>" +
        "<td>" + CS.escapar(item.provedor || "—") + "</td>" +
        '<td><span class="badge ' + (item.origem === "cache" ? "badge--ok" : "badge--info") + '">' +
          CS.escapar(rotulosOrigem[item.origem] || item.origem) + "</span></td>" +
      "</tr>";
    }).join("");
  }

  // ---------- Verificar (POST /api/reputacao/verificar) ----------
  document.getElementById("form-ips").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var ips = campoIps.value.split("\n").map(function (l) { return l.trim(); })
      .filter(function (l) { return l !== ""; });
    if (ips.length === 0) { CS.mostrarMensagem(msg, "erro", "Digite pelo menos um IP."); return; }

    var botao = document.getElementById("btn-verificar");
    botao.disabled = true;
    botao.textContent = "Consultando…";
    CS.mostrarMensagem(msg, "info", "Consultando… IPs fora do cache levam ~1,5 s cada (limite gratuito da API).");
    CS.linhaEstado(corpo, COLUNAS, "Carregando…");

    CS.api("/api/reputacao/verificar", "POST", { ips: ips })
      .then(function (r) {
        CS.mostrarMensagem(msg, "ok", "Relatório gravado em dados/relatorio_ips.json.");
        mostrarRelatorio(r);
      })
      .catch(function (erro) {
        CS.mostrarMensagem(msg, "erro", erro.message);
        CS.linhaEstado(corpo, COLUNAS, "Não foi possível gerar o relatório.", "erro");
      })
      .then(function () { botao.disabled = false; botao.textContent = "Verificar reputação"; });
  });

  // ---------- Limpar cache (DELETE /api/reputacao/cache) ----------
  document.getElementById("btn-limpar-cache").addEventListener("click", function () {
    CS.api("/api/reputacao/cache", "DELETE")
      .then(function (r) { CS.mostrarMensagem(msg, "ok", r.removidos + " IP(s) removido(s) do cache."); })
      .catch(function (erro) { CS.mostrarMensagem(msg, "erro", erro.message); });
  });

  // ---------- Ao abrir: lista padrão (ips.txt) + último relatório ----------
  CS.api("/api/reputacao/ips-padrao")
    .then(function (ips) { campoIps.value = ips.join("\n"); })
    .catch(function () { /* campo fica vazio para o usuário digitar */ });

  CS.linhaEstado(corpo, COLUNAS, "Carregando último relatório…");
  CS.api("/api/reputacao/relatorio")
    .then(mostrarRelatorio)
    .catch(function (erro) {
      if (erro.status === 404) CS.linhaEstado(corpo, COLUNAS, "Nenhum relatório ainda. Clique em “Verificar reputação”.");
      else CS.linhaEstado(corpo, COLUNAS, erro.message, "erro");
    });
})();
