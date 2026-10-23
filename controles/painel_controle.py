# Rotas que usam os dois bancos + saúde do sistema
from flask import Blueprint, jsonify

from modelos import ativo_modelo, conexoes, quarentena, vulnerabilidade_modelo
from modelos.erros import ErroApi

rotas = Blueprint("painel", __name__)


@rotas.get("/api/saude")
def saude():
    # 200 se os dois bancos respondem, 503 se algum caiu
    mysql_ok, mongo_ok = conexoes.testar_bancos()
    status = 200 if mysql_ok and mongo_ok else 503
    return jsonify({"mysql": mysql_ok, "mongodb": mongo_ok}), status


@rotas.get("/api/relatorio/<nome_ativo>")
def relatorio(nome_ativo):
    # O que faz: dados do ativo (MySQL) + vulnerabilidades dele (MongoDB)
    # Por que faz: não existe JOIN entre os dois bancos, quem junta é a API
    # 200 | 404 se o nome não existe em nenhum banco
    ativo = ativo_modelo.buscar_por_nome(nome_ativo)
    vulnerabilidades = vulnerabilidade_modelo.listar_vulnerabilidades(ativo=nome_ativo)
    if ativo is None and len(vulnerabilidades) == 0:
        raise ErroApi(f"Nenhum ativo chamado '{nome_ativo}' foi encontrado.", 404)
    # ativo None com vulnerabilidades = ativo removido do MySQL
    return jsonify({"ativo": ativo, "vulnerabilidades": vulnerabilidades})


@rotas.post("/api/quarentena")
def rodar_quarentena():
    # execução manual; normalmente ela já roda sozinha
    return jsonify(quarentena.aplicar_quarentena())
