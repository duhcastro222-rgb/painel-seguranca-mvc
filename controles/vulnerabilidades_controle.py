# Rotas de VULNERABILIDADES (MongoDB)
from flask import Blueprint, jsonify, request

from controles import corpo_json
from modelos import ativo_modelo, quarentena, vulnerabilidade_modelo
from modelos.erros import ErroApi

rotas = Blueprint("vulnerabilidades", __name__)


@rotas.get("/api/vulnerabilidades")
def listar():
    # ?severidade=critica&status=aberta&ativo=srv-web-01 -> 200
    return jsonify(vulnerabilidade_modelo.listar_vulnerabilidades(
        request.args.get("severidade"), request.args.get("status"), request.args.get("ativo")))


@rotas.get("/api/vulnerabilidades/resumo")
def resumo():
    # consulta com projeção
    return jsonify(vulnerabilidade_modelo.listar_resumo())


@rotas.post("/api/vulnerabilidades")
def cadastrar():
    # 201 | 400 fora do esquema | 422 ativo não cadastrado
    # [OBS] não há chave estrangeira entre bancos, então a API confere no MySQL
    dados = corpo_json()
    nome = str(dados.get("ativo_relacionado") or "").strip()
    if ativo_modelo.buscar_por_nome(nome) is None:
        raise ErroApi(f"O ativo '{nome}' não está cadastrado no inventário (MySQL).", 422)
    vulnerabilidade = vulnerabilidade_modelo.cadastrar_vulnerabilidade(dados)
    return jsonify({"vulnerabilidade": vulnerabilidade,
                    "quarentena": quarentena.aplicar_quarentena()}), 201


@rotas.post("/api/vulnerabilidades/carga")
def carregar_dataset():
    # 201 | 409 se a coleção já tem dados
    total = vulnerabilidade_modelo.carregar_vulnerabilidades()
    return jsonify({"carregadas": total, "quarentena": quarentena.aplicar_quarentena()}), 201


@rotas.patch("/api/vulnerabilidades/<identificador>/status")
def atualizar_status(identificador):
    # <_id ou CVE> | 200 | 400 status inválido | 404 não existe
    vulnerabilidade = vulnerabilidade_modelo.atualizar_status_vulnerabilidade(
        identificador, corpo_json().get("status"))
    return jsonify({"vulnerabilidade": vulnerabilidade,
                    "quarentena": quarentena.aplicar_quarentena()})


@rotas.delete("/api/vulnerabilidades/corrigidas")
def remover_corrigidas():
    return jsonify({"removidas": vulnerabilidade_modelo.remover_corrigidas()})
