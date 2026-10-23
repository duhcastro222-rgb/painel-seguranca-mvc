/* Visão geral: números dos dois bancos (/api/ativos e /api/vulnerabilidades) */
(function () {
  "use strict";

  Promise.all([CS.api("/api/ativos"), CS.api("/api/vulnerabilidades")])
    .then(function (respostas) {
      var ativos = respostas[0], vulns = respostas[1];
      document.getElementById("stat-ativos").textContent = ativos.length;
      document.getElementById("stat-quarentena").textContent =
        ativos.filter(function (a) { return a.status_patch === "critico"; }).length;
      document.getElementById("stat-vulns").textContent = vulns.length;
      document.getElementById("stat-abertas").textContent =
        vulns.filter(function (v) { return v.status === "aberta"; }).length;
    })
    .catch(function (erro) {
      ["stat-ativos", "stat-quarentena", "stat-vulns", "stat-abertas"].forEach(function (id) {
        document.getElementById(id).textContent = "—";
      });
      CS.mostrarMensagem(document.getElementById("msg-inicio"), "erro", erro.message);
    });
})();
