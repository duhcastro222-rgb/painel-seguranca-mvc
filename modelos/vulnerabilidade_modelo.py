# =========================================================================
# CRUD de VULNERABILIDADES (MongoDB) - mesmas operações da atividade de
# bancos, mais o cadastro de uma vulnerabilidade nova pela tela
# =========================================================================
import json
import os

from bson.objectid import ObjectId
from pymongo.errors import WriteError

import config
from modelos import conexoes
from modelos.erros import ErroApi

STATUS = ["aberta", "em_correcao", "corrigida"]

# $jsonSchema: o próprio MongoDB recusa documento fora do formato
# [OBS] "detalhes" fica livre porque muda por categoria
VALIDADOR_VULNERABILIDADES = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["cve_id", "ativo_relacionado", "categoria", "severidade",
                     "score_cvss", "descricao", "status", "data_deteccao", "detalhes"],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "cve_id": {"bsonType": ["string", "null"], "pattern": "^CVE-[0-9]{4}-[0-9]{4,}$"},
            "ativo_relacionado": {"bsonType": "string", "minLength": 1, "maxLength": 60},
            "categoria": {"enum": ["sistema_operacional", "rede", "aplicacao_web", "endpoint"]},
            "severidade": {"enum": ["baixa", "media", "alta", "critica"]},
            "score_cvss": {"bsonType": "number", "minimum": 0, "maximum": 10},
            "descricao": {"bsonType": "string", "minLength": 1},
            "status": {"enum": STATUS},
            "data_deteccao": {"bsonType": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"},
            "detalhes": {"bsonType": "object"},
        },
    }
}


def aplicar_validador():
    # O que faz: liga o $jsonSchema na coleção (collMod se ela já existe)
    banco = conexoes.colecao.database
    opcoes = {"validator": VALIDADOR_VULNERABILIDADES,
              "validationLevel": "strict", "validationAction": "error"}
    if conexoes.colecao.name in banco.list_collection_names():
        banco.command("collMod", conexoes.colecao.name, **opcoes)
    else:
        banco.create_collection(conexoes.colecao.name, **opcoes)


def formatar(vulnerabilidade):
    # O que faz: troca o ObjectId (que o JSON não entende) por texto
    vulnerabilidade["_id"] = str(vulnerabilidade["_id"])
    return vulnerabilidade


def filtro_por_identificador(identificador):
    # O que faz: aceita o _id ou o CVE para achar o documento
    # Por que faz: falha de configuração não tem CVE, só o _id
    if ObjectId.is_valid(identificador):
        return {"_id": ObjectId(identificador)}
    return {"cve_id": identificador}


# =========================================================================
# CRUD
# =========================================================================
def listar_vulnerabilidades(severidade=None, status=None, ativo=None):
    # O que faz: find() com filtros opcionais, do maior score para o menor
    # [OBS] str() impede mandar operador como {"$ne": ""} (NoSQL Injection)
    filtro = {}
    if severidade:
        filtro["severidade"] = str(severidade)
    if status:
        filtro["status"] = str(status)
    if ativo:
        filtro["ativo_relacionado"] = str(ativo)
    return [formatar(v) for v in conexoes.colecao.find(filtro).sort("score_cvss", -1)]


def listar_resumo():
    # O que faz: consulta com projeção (só cve_id, ativo e score)
    projecao = {"_id": 0, "cve_id": 1, "ativo_relacionado": 1, "score_cvss": 1}
    return list(conexoes.colecao.find({}, projecao).sort("score_cvss", -1))


def contar_por_ativo(nome_ativo):
    return conexoes.colecao.count_documents({"ativo_relacionado": nome_ativo})


def cadastrar_vulnerabilidade(dados):
    # O que faz: insere uma vulnerabilidade nova
    # [OBS] só os campos conhecidos são copiados; o formato quem confere é
    # o $jsonSchema
    try:
        score = float(dados.get("score_cvss"))
    except (TypeError, ValueError):
        raise ErroApi("Score CVSS deve ser um número entre 0 e 10.")

    documento = {
        "cve_id": (dados.get("cve_id") or "").strip().upper() or None,
        "ativo_relacionado": str(dados.get("ativo_relacionado") or "").strip(),
        "categoria": dados.get("categoria"),
        "severidade": dados.get("severidade"),
        "score_cvss": score,
        "descricao": str(dados.get("descricao") or "").strip(),
        "status": dados.get("status") or "aberta",
        "data_deteccao": dados.get("data_deteccao"),
        "detalhes": dados.get("detalhes") or {},
    }
    try:
        resultado = conexoes.colecao.insert_one(documento)
    except WriteError:
        # código 121 = Document failed validation
        raise ErroApi("O MongoDB recusou a vulnerabilidade: confira CVE (CVE-AAAA-NNNN "
                      "ou vazio), categoria, severidade, score de 0 a 10, descrição e data.")
    documento["_id"] = resultado.inserted_id
    return formatar(documento)


def carregar_vulnerabilidades():
    # O que faz: carga inicial a partir de dados/vulnerabilidades.json
    # [OBS] recusa (409) se a coleção já tem dados, para não duplicar
    if conexoes.colecao.count_documents({}) > 0:
        raise ErroApi("A coleção já tem documentos. Carga cancelada para não duplicar.", 409)
    with open(os.path.join(config.PASTA_DADOS, "vulnerabilidades.json"), encoding="utf-8") as arquivo:
        documentos = json.load(arquivo)
    conexoes.colecao.insert_many(documentos)
    return len(documentos)


def atualizar_status_vulnerabilidade(identificador, novo_status):
    # O que faz: muda o status (aberta -> em_correcao -> corrigida)
    if novo_status not in STATUS:
        raise ErroApi("Status inválido. Use: aberta, em_correcao ou corrigida.")
    filtro = filtro_por_identificador(identificador)
    resultado = conexoes.colecao.update_one(filtro, {"$set": {"status": novo_status}})
    if resultado.matched_count == 0:
        raise ErroApi(f"Vulnerabilidade '{identificador}' não encontrada.", 404)
    return formatar(conexoes.colecao.find_one(filtro))


def remover_corrigidas():
    # O que faz: apaga todas as vulnerabilidades corrigidas (D do CRUD)
    return conexoes.colecao.delete_many({"status": "corrigida"}).deleted_count


def ativos_para_quarentena():
    # O que faz: nomes dos ativos com falha aberta e score acima de 9.0
    # [OBS] $gt = maior que, então 9.0 exato não entra
    filtro = {"score_cvss": {"$gt": 9.0}, "status": "aberta"}
    return conexoes.colecao.distinct("ativo_relacionado", filtro)
