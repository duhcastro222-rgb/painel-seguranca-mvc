# Transforma qualquer erro em {"erro": "mensagem"} com o código HTTP certo.
# Detalhe técnico (SQL, stack trace) fica só no terminal do servidor.
import mysql.connector
from flask import jsonify, request
from pymongo.errors import PyMongoError
from werkzeug.exceptions import HTTPException

from modelos.erros import ErroApi


def registrar_erros(app):

    @app.errorhandler(ErroApi)
    def erro_da_regra(erro):
        return jsonify({"erro": erro.mensagem}), erro.status

    @app.errorhandler(mysql.connector.Error)
    def erro_mysql(erro):
        # 503 = banco fora do ar
        app.logger.error(f"MySQL falhou em {request.path}: {erro}")
        return jsonify({"erro": "O banco de ativos (MySQL) não respondeu. Tente de novo em instantes."}), 503

    @app.errorhandler(PyMongoError)
    def erro_mongo(erro):
        app.logger.error(f"MongoDB falhou em {request.path}: {erro}")
        return jsonify({"erro": "O banco de vulnerabilidades (MongoDB) não respondeu. Tente de novo em instantes."}), 503

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        # rota inexistente (404) ou método errado (405) - só a API vira JSON
        if request.path.startswith("/api/"):
            return jsonify({"erro": f"Requisição inválida: {erro.name}."}), erro.code
        return erro

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.exception(f"Erro inesperado em {request.path}")
        return jsonify({"erro": "Erro interno no servidor. Veja o terminal do Flask."}), 500
