/* Tela de ativos: tudo passa por /api/ativos (MySQL) */
(function () {
  "use strict";

  var corpo = document.getElementById("corpo-ativos");
  var selSetor = document.getElementById("filtro-setor");
  var selStatus = document.getElementById("filtro-status");
  var msgLista = document.getElementById("msg-lista");
  var msgCadastro = document.getElementById("msg-cadastro");
  var msgSenha = document.getElementById("msg-senha");
  var selSenhaAtivo = document.getElementById("senha-ativo");
  var COLUNAS = 7;

  // ---------- Listagem (GET /api/ativos?setor=&status=) ----------
  function carregarAtivos() {
    CS.linhaEstado(corpo, COLUNAS, "Carregando ativos…");
    var params = new URLSearchParams();
    if (selSetor.value) params.set("setor", selSetor.value);
    if (selStatus.value) params.set("status", selStatus.value);

    CS.api("/api/ativos?" + params.toString())
      .then(function (ativos) {
        if (ativos.length === 0) {
          CS.linhaEstado(corpo, COLUNAS, "Nenhum ativo encontrado com esses filtros.");
          return;
        }
        corpo.innerHTML = ativos.map(linhaAtivo).join("");
      })
      .catch(function (erro) {
        CS.linhaEstado(corpo, COLUNAS, erro.message, "erro");
      });
  }

  function linhaAtivo(a) {
    var opcoes = ["pendente", "em_dia", "critico"].map(function (s) {
      return '<option value="' + s + '"' + (s === a.status_patch ? " selected" : "") + ">" +
        { pendente: "Pendente", em_dia: "Em dia", critico: "Crítico" }[s] + "</option>";
    }).join("");
    return "<tr>" +
      '<td class="dado"><a href="../relatorio/index.html?nome=' + encodeURIComponent(a.nome_ativo) + '">' +
        CS.escapar(a.nome_ativo) + "</a></td>" +
      "<td>" + CS.escapar(a.tipo.replace(/_/g, " ")) + "</td>" +
      "<td>" + CS.escapar(a.setor_responsavel) + "</td>" +
      '<td class="dado">' + CS.escapar(a.ip_interno) + "</td>" +
      '<td class="dado">' + CS.escapar(a.data_ultima_verificacao) + "</td>" +
      "<td>" + CS.badgeStatus(a.status_patch) + "</td>" +
      '<td><div class="acoes-linha">' +
        '<select data-status-id="' + a.id + '" aria-label="Novo status de ' + CS.escapar(a.nome_ativo) + '">' + opcoes + "</select>" +
        '<button type="button" class="btn btn--mini" data-salvar="' + a.id + '">Salvar</button>' +
        '<button type="button" class="btn btn--mini btn--perigo" data-remover="' + a.id + '" data-nome="' +
          CS.escapar(a.nome_ativo) + '">Remover</button>' +
      "</div></td>" +
    "</tr>";
  }

  // ---------- Ações da tabela (delegação de eventos) ----------
  corpo.addEventListener("click", function (ev) {
    var botao = ev.target.closest("button");
    if (!botao) return;

    if (botao.dataset.salvar) {
      // PATCH /api/ativos/<id>/status -> 409 se o ativo estiver em quarentena
      var id = botao.dataset.salvar;
      var novo = corpo.querySelector('[data-status-id="' + id + '"]').value;
      botao.disabled = true;
      CS.api("/api/ativos/" + id + "/status", "PATCH", { status_patch: novo })
        .then(function (a) {
          CS.mostrarMensagem(msgLista, "ok", "Status de " + a.nome_ativo + " atualizado.");
          carregarAtivos();
        })
        .catch(function (erro) {
          CS.mostrarMensagem(msgLista, erro.status === 409 ? "alerta" : "erro", erro.message);
          carregarAtivos();  // volta o select para o valor real do banco
        });
    }

    if (botao.dataset.remover) {
      if (!confirm("Remover o ativo " + botao.dataset.nome + " do inventário?")) return;
      CS.api("/api/ativos/" + botao.dataset.remover, "DELETE")
        .then(function (r) {
          var aviso = r.vulnerabilidades_orfas > 0
            ? " Atenção: " + r.vulnerabilidades_orfas + " vulnerabilidade(s) dele continuam no MongoDB (não há cascata entre bancos)."
            : "";
          CS.mostrarMensagem(msgLista, aviso ? "alerta" : "ok", r.removido.nome_ativo + " removido." + aviso);
          carregarFiltros();
          carregarAtivos();
        })
        .catch(function (erro) { CS.mostrarMensagem(msgLista, "erro", erro.message); });
    }
  });

  // ---------- Cadastro (POST /api/ativos) ----------
  document.getElementById("form-ativo").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var form = ev.target;
    var dados = {};
    new FormData(form).forEach(function (valor, chave) { dados[chave] = String(valor).trim(); });

    // validação rápida; a regra que vale é a do servidor
    var faltando = ["nome_ativo", "ip_interno", "setor_responsavel", "sistema_operacional", "data_ultima_verificacao"]
      .filter(function (c) { return !dados[c]; });
    if (faltando.length) {
      CS.mostrarMensagem(msgCadastro, "erro", "Preencha todos os campos obrigatórios.");
      return;
    }

    var botao = document.getElementById("btn-cadastrar");
    botao.disabled = true;
    botao.textContent = "Cadastrando…";
    CS.api("/api/ativos", "POST", dados)
      .then(function (r) {
        var texto = "Ativo " + r.ativo.nome_ativo + " cadastrado (id " + r.ativo.id + ").";
        if (r.ativo.status_patch === "critico" && r.quarentena.isolados_agora.indexOf(r.ativo.nome_ativo) >= 0) {
          texto += " Ele já entrou em quarentena: há vulnerabilidade aberta com CVSS > 9,0.";
        }
        CS.mostrarMensagem(msgCadastro, "ok", texto);
        form.reset();
        form.data_ultima_verificacao.value = new Date().toISOString().slice(0, 10);
        carregarFiltros();
        carregarAtivos();
      })
      .catch(function (erro) { CS.mostrarMensagem(msgCadastro, "erro", erro.message); })
      .then(function () { botao.disabled = false; botao.textContent = "Cadastrar ativo"; });
  });

  // ---------- Senha de acesso ----------
  function senhaDigitada() {
    var senha = document.getElementById("senha-valor").value;
    if (!selSenhaAtivo.value) { CS.mostrarMensagem(msgSenha, "erro", "Escolha um ativo."); return null; }
    if (!senha) { CS.mostrarMensagem(msgSenha, "erro", "Digite a senha."); return null; }
    return senha;
  }

  document.getElementById("btn-definir-senha").addEventListener("click", function () {
    var senha = senhaDigitada();
    if (senha === null) return;
    CS.api("/api/ativos/" + selSenhaAtivo.value + "/senha", "PUT", { senha: senha })
      .then(function (r) {
        CS.mostrarMensagem(msgSenha, "ok", r.mensagem);
        document.getElementById("senha-valor").value = "";
        carregarAtivos();
      })
      .catch(function (erro) { CS.mostrarMensagem(msgSenha, "erro", erro.message); });
  });

  document.getElementById("btn-verificar-senha").addEventListener("click", function () {
    var senha = senhaDigitada();
    if (senha === null) return;
    CS.api("/api/ativos/" + selSenhaAtivo.value + "/senha/verificar", "POST", { senha: senha })
      .then(function (r) {
        if (r.valida) CS.mostrarMensagem(msgSenha, "ok", "Senha correta - acesso liberado.");
        else CS.mostrarMensagem(msgSenha, "erro", "Senha incorreta - acesso negado.");
      })
      .catch(function (erro) { CS.mostrarMensagem(msgSenha, "alerta", erro.message); });
  });

  // ---------- Selects de setor e de ativo (vêm da lista completa) ----------
  function carregarFiltros() {
    return CS.api("/api/ativos").then(function (ativos) {
      var setorAtual = selSetor.value;
      var setores = [];
      ativos.forEach(function (a) {
        if (setores.indexOf(a.setor_responsavel) < 0) setores.push(a.setor_responsavel);
      });
      selSetor.innerHTML = '<option value="">Todos os setores</option>' + setores.sort().map(function (s) {
        return '<option value="' + CS.escapar(s) + '">' + CS.escapar(s) + "</option>";
      }).join("");
      selSetor.value = setorAtual;

      selSenhaAtivo.innerHTML = '<option value="">Escolha…</option>' + ativos.map(function (a) {
        return '<option value="' + a.id + '">' + CS.escapar(a.nome_ativo) + "</option>";
      }).join("");
    }).catch(function () { /* o erro já aparece na tabela */ });
  }

  selSetor.addEventListener("change", carregarAtivos);
  selStatus.addEventListener("change", carregarAtivos);
  document.getElementById("btn-atualizar").addEventListener("click", carregarAtivos);

  document.getElementById("data_ultima_verificacao").value = new Date().toISOString().slice(0, 10);
  carregarFiltros();
  carregarAtivos();
})();
