/* Tela de vulnerabilidades: tudo passa por /api/vulnerabilidades (MongoDB) */
(function () {
  "use strict";

  var lista = document.getElementById("lista-vulnerabilidades");
  var selSev = document.getElementById("filtro-severidade");
  var selStatus = document.getElementById("filtro-status");
  var selAtivo = document.getElementById("filtro-ativo");
  var msgLista = document.getElementById("msg-lista");
  var msgCadastro = document.getElementById("msg-cadastro");

  // avisa quando uma escrita colocou algum ativo em quarentena
  function avisoQuarentena(quarentena) {
    if (quarentena && quarentena.isolados_agora.length > 0) {
      return " Quarentena automática: " + quarentena.isolados_agora.join(", ") + " passou(aram) para patch crítico.";
    }
    return "";
  }

  // ---------- Listagem (GET /api/vulnerabilidades?severidade=&status=&ativo=) ----------
  function carregarVulnerabilidades() {
    CS.blocoEstado(lista, "Carregando vulnerabilidades…");
    var params = new URLSearchParams();
    if (selSev.value) params.set("severidade", selSev.value);
    if (selStatus.value) params.set("status", selStatus.value);
    if (selAtivo.value) params.set("ativo", selAtivo.value);

    CS.api("/api/vulnerabilidades?" + params.toString())
      .then(function (vulns) {
        if (vulns.length === 0) {
          CS.blocoEstado(lista, "Nenhuma vulnerabilidade com esses filtros. Se a coleção estiver vazia, use “Carregar dataset”.");
          return;
        }
        lista.innerHTML = vulns.map(function (v) {
          var opcoes = ["aberta", "em_correcao", "corrigida"].map(function (s) {
            return '<option value="' + s + '"' + (s === v.status ? " selected" : "") + ">" +
              { aberta: "Aberta", em_correcao: "Em correção", corrigida: "Corrigida" }[s] + "</option>";
          }).join("");
          var acoes = '<span class="acoes-linha">' +
            '<select data-status-id="' + v._id + '" aria-label="Novo status">' + opcoes + "</select>" +
            '<button type="button" class="btn btn--mini" data-salvar="' + v._id + '">Salvar</button>' +
          "</span>";
          return CS.cartaoVulnerabilidade(v, acoes);
        }).join("");
      })
      .catch(function (erro) { CS.blocoEstado(lista, erro.message, "erro"); });
  }

  // ---------- Mudar status (PATCH /api/vulnerabilidades/<_id>/status) ----------
  lista.addEventListener("click", function (ev) {
    var botao = ev.target.closest("button[data-salvar]");
    if (!botao) return;
    var id = botao.dataset.salvar;
    var novo = lista.querySelector('[data-status-id="' + id + '"]').value;
    botao.disabled = true;
    CS.api("/api/vulnerabilidades/" + id + "/status", "PATCH", { status: novo })
      .then(function (r) {
        CS.mostrarMensagem(msgLista, "ok", "Status atualizado para " + { aberta: "aberta", em_correcao: "em correção", corrigida: "corrigida" }[novo] + "." + avisoQuarentena(r.quarentena));
        carregarVulnerabilidades();
      })
      .catch(function (erro) { CS.mostrarMensagem(msgLista, "erro", erro.message); botao.disabled = false; });
  });

  // ---------- Carga inicial (POST /api/vulnerabilidades/carga) ----------
  document.getElementById("btn-carga").addEventListener("click", function () {
    CS.api("/api/vulnerabilidades/carga", "POST")
      .then(function (r) {
        CS.mostrarMensagem(msgLista, "ok", r.carregadas + " vulnerabilidade(s) carregada(s)." + avisoQuarentena(r.quarentena));
        carregarVulnerabilidades();
      })
      .catch(function (erro) {
        // 409 = já tem dados: não é falha grave, é um aviso
        CS.mostrarMensagem(msgLista, erro.status === 409 ? "alerta" : "erro", erro.message);
      });
  });

  // ---------- Remover corrigidas (DELETE /api/vulnerabilidades/corrigidas) ----------
  document.getElementById("btn-remover-corrigidas").addEventListener("click", function () {
    if (!confirm("Apagar TODAS as vulnerabilidades com status corrigida?")) return;
    CS.api("/api/vulnerabilidades/corrigidas", "DELETE")
      .then(function (r) {
        CS.mostrarMensagem(msgLista, "ok", r.removidas + " vulnerabilidade(s) corrigida(s) removida(s).");
        carregarVulnerabilidades();
      })
      .catch(function (erro) { CS.mostrarMensagem(msgLista, "erro", erro.message); });
  });

  // ---------- Projeção (GET /api/vulnerabilidades/resumo) ----------
  document.getElementById("btn-resumo").addEventListener("click", function () {
    var corpo = document.getElementById("corpo-resumo");
    CS.linhaEstado(corpo, 3, "Carregando…");
    CS.api("/api/vulnerabilidades/resumo")
      .then(function (itens) {
        if (itens.length === 0) { CS.linhaEstado(corpo, 3, "Coleção vazia."); return; }
        corpo.innerHTML = itens.map(function (v) {
          return '<tr><td class="dado">' + CS.escapar(v.cve_id || "—") + "</td>" +
            '<td class="dado">' + CS.escapar(v.ativo_relacionado) + "</td>" +
            '<td class="col-num">' + Number(v.score_cvss).toFixed(1) + "</td></tr>";
        }).join("");
      })
      .catch(function (erro) { CS.linhaEstado(corpo, 3, erro.message, "erro"); });
  });

  // ---------- Cadastro (POST /api/vulnerabilidades) ----------
  // transforma "chave: valor" (uma por linha) no objeto "detalhes"
  function lerDetalhes(texto) {
    var detalhes = {};
    texto.split("\n").forEach(function (linha) {
      var pos = linha.indexOf(":");
      if (pos > 0) {
        var chave = linha.slice(0, pos).trim().replace(/\s+/g, "_");
        var valor = linha.slice(pos + 1).trim();
        // número vira número (ex.: porta 443), o resto fica texto
        detalhes[chave] = valor !== "" && !isNaN(valor) ? Number(valor) : valor;
      }
    });
    return detalhes;
  }

  document.getElementById("form-vuln").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var form = ev.target;
    var dados = {
      ativo_relacionado: form.ativo_relacionado.value,
      cve_id: form.cve_id.value.trim(),
      categoria: form.categoria.value,
      severidade: form.severidade.value,
      score_cvss: form.score_cvss.value,
      status: form.status.value,
      data_deteccao: form.data_deteccao.value,
      descricao: form.descricao.value.trim(),
      detalhes: lerDetalhes(form.detalhes.value)
    };
    if (!dados.ativo_relacionado || !dados.descricao || dados.score_cvss === "" || !dados.data_deteccao) {
      CS.mostrarMensagem(msgCadastro, "erro", "Preencha ativo, score, data e descrição.");
      return;
    }

    var botao = document.getElementById("btn-registrar");
    botao.disabled = true;
    CS.api("/api/vulnerabilidades", "POST", dados)
      .then(function (r) {
        CS.mostrarMensagem(msgCadastro, "ok", "Vulnerabilidade registrada em " + r.vulnerabilidade.ativo_relacionado + "." + avisoQuarentena(r.quarentena));
        form.reset();
        form.data_deteccao.value = new Date().toISOString().slice(0, 10);
        carregarVulnerabilidades();
      })
      .catch(function (erro) { CS.mostrarMensagem(msgCadastro, "erro", erro.message); })
      .then(function () { botao.disabled = false; });
  });

  // ---------- Selects de ativo (GET /api/ativos) ----------
  function carregarAtivos() {
    CS.api("/api/ativos").then(function (ativos) {
      var opcoes = ativos.map(function (a) {
        return '<option value="' + CS.escapar(a.nome_ativo) + '">' + CS.escapar(a.nome_ativo) + "</option>";
      }).join("");
      selAtivo.innerHTML = '<option value="">Todos os ativos</option>' + opcoes;
      document.getElementById("ativo_relacionado").innerHTML = opcoes;
    }).catch(function (erro) { CS.mostrarMensagem(msgCadastro, "erro", erro.message); });
  }

  [selSev, selStatus, selAtivo].forEach(function (s) { s.addEventListener("change", carregarVulnerabilidades); });
  document.getElementById("data_deteccao").value = new Date().toISOString().slice(0, 10);
  carregarAtivos();
  carregarVulnerabilidades();
})();
