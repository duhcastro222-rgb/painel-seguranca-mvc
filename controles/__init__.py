# Controle: rotas Flask que devolvem JSON. Cada rota chama o modelo do
# banco certo:
#   /api/ativos           -> MySQL
#   /api/vulnerabilidades -> MongoDB
#   /api/relatorio e quarentena -> os dois
#   /api/reputacao        -> API externa ip-api + arquivos .json
from flask import request

from modelos.erros import ErroApi


def corpo_json():
    # O que faz: lê o JSON da requisição ou responde 400
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroApi("O corpo da requisição deve ser um JSON válido.")
    return dados
