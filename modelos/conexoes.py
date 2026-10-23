# =========================================================================
# Conexões: MySQL (ativos) e MongoDB (vulnerabilidades)
# =========================================================================
# Ativo tem sempre os mesmos campos -> tabela (MySQL).
# Vulnerabilidade muda de campos conforme a categoria -> documento (MongoDB).
# O elo entre os dois: ativos.nome_ativo == vulnerabilidades.ativo_relacionado
# =========================================================================
import mysql.connector
from pymongo import MongoClient

import config

colecao = None  # coleção do MongoDB, preenchida por conectar_mongo()


def conectar_mysql():
    # O que faz: abre uma conexão nova com o MySQL
    # Por que faz: cada requisição do Flask roda numa thread, então cada
    # operação usa a sua própria conexão
    return mysql.connector.connect(**config.MYSQL)


def conectar_mongo():
    # O que faz: conecta no MongoDB e guarda a coleção de vulnerabilidades
    global colecao
    cliente = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
    cliente.admin.command("ping")  # o MongoClient só conecta de verdade aqui
    colecao = cliente[config.MONGO_DB][config.MONGO_COLLECTION]


def consultar(sql, parametros=()):
    # O que faz: roda um SELECT e devolve as linhas como dicionários
    # Por que faz: prepared=True manda o SQL separado dos valores, o que
    # evita SQL Injection
    conexao = conectar_mysql()
    try:
        cursor = conexao.cursor(prepared=True, dictionary=True)
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    finally:
        conexao.close()


def executar(sql, parametros=()):
    # O que faz: roda INSERT/UPDATE/DELETE e faz o commit
    # O que fazer com o resultado: (linhas afetadas, id gerado no INSERT)
    conexao = conectar_mysql()
    try:
        cursor = conexao.cursor(prepared=True)
        cursor.execute(sql, parametros)
        conexao.commit()
        return cursor.rowcount, cursor.lastrowid
    finally:
        conexao.close()


def testar_bancos():
    # O que faz: diz se cada banco está respondendo agora
    try:
        conectar_mysql().close()
        mysql_ok = True
    except mysql.connector.Error:
        mysql_ok = False
    try:
        colecao.database.client.admin.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False
    return mysql_ok, mongo_ok
