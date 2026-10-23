# Rotas de ATIVOS (MySQL)
from flask import Blueprint, jsonify, request

from controles import corpo_json
from modelos import ativo_modelo, quarentena, vulnerabilidade_modelo
from modelos.erros import ErroApi

rotas = Blueprint("ativos", __name__)


@rotas.get("/api/ativos")
def listar():
    # ?setor=TI&status=pendente -> 200 (lista vazia também é 200)
    return jsonify(ativo_modelo.listar_ativos(request.args.get("setor"),
                                              request.args.get("status")))


@rotas.get("/api/ativos/<int:id_ativo>")
def detalhar(id_ativo):
    return jsonify(ativo_modelo.buscar_por_id(id_ativo))  # 404 se não existir


@rotas.post("/api/ativos")
def cadastrar():
    # 201 criado | 400 inválido | 409 nome repetido
    # roda a quarentena: o ativo pode já ter falha crítica no Mongo
    ativo = ativo_modelo.cadastrar_ativo(corpo_json())
    resultado = quarentena.aplicar_quarentena()
    ativo = ativo_modelo.buscar_por_id(ativo["id"])
    return jsonify({"ativo": ativo, "quarentena": resultado}), 201


@rotas.patch("/api/ativos/<int:id_ativo>/status")
def atualizar_status(id_ativo):
    # 200 | 400 status inválido | 404 não existe | 409 ativo em quarentena
    novo_status = corpo_json().get("status_patch")
    ativo = ativo_modelo.buscar_por_id(id_ativo)
    if novo_status != "critico" and quarentena.ativo_em_quarentena(ativo["nome_ativo"]):
        raise ErroApi("Ativo em quarentena: ainda há vulnerabilidade aberta com CVSS "
                      "acima de 9.0. Corrija-a antes de mudar o status do patch.", 409)
    return jsonify(ativo_modelo.atualizar_status_patch(id_ativo, novo_status))


@rotas.delete("/api/ativos/<int:id_ativo>")
def remover(id_ativo):
    # 200 + quantas vulnerabilidades ficaram sem ativo | 404
    ativo = ativo_modelo.remover_ativo(id_ativo)
    orfas = vulnerabilidade_modelo.contar_por_ativo(ativo["nome_ativo"])
    return jsonify({"removido": ativo, "vulnerabilidades_orfas": orfas})


@rotas.put("/api/ativos/<int:id_ativo>/senha")
def definir_senha(id_ativo):
    # 200 | 400 senha fraca | 404
    ativo_modelo.definir_senha(id_ativo, corpo_json().get("senha"))
    return jsonify({"mensagem": "Senha de acesso gravada (somente o hash bcrypt)."})


@rotas.post("/api/ativos/<int:id_ativo>/senha/verificar")
def verificar_senha(id_ativo):
    # POST para a senha não aparecer na URL | 200 | 404 | 409 sem senha
    valida = ativo_modelo.verificar_senha(id_ativo, corpo_json().get("senha"))
    return jsonify({"valida": valida})
