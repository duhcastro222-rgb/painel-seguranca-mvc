# Rotas do verificador de reputação de IPs (ip-api + arquivos .json)
from flask import Blueprint, jsonify

from controles import corpo_json
from modelos import reputacao_modelo

rotas = Blueprint("reputacao", __name__)


@rotas.get("/api/reputacao/ips-padrao")
def ips_padrao():
    # lista de dados/ips.txt
    return jsonify(reputacao_modelo.ler_ips())


@rotas.post("/api/reputacao/verificar")
def verificar():
    # {"ips": [...]} -> 200 relatório | 400 lista inválida
    return jsonify(reputacao_modelo.verificar_ips(corpo_json().get("ips")))


@rotas.get("/api/reputacao/relatorio")
def relatorio():
    # último relatório gravado | 404 se ainda não existe
    dados = reputacao_modelo.ultimo_relatorio()
    if dados is None:
        return jsonify({"erro": "Nenhum relatório gerado ainda."}), 404
    return jsonify(dados)


@rotas.delete("/api/reputacao/cache")
def limpar_cache():
    return jsonify({"removidos": reputacao_modelo.limpar_cache()})
