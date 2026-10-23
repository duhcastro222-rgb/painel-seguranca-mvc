# =========================================================================
# CRUD de ATIVOS (MySQL) - mesmas operações da atividade de bancos,
# agora devolvendo os dados para a rota em vez de dar print
# =========================================================================
import ipaddress
from datetime import date

import bcrypt
import mysql.connector

from modelos.conexoes import consultar, executar
from modelos.erros import ErroApi

TIPOS = ["servidor", "estacao", "dispositivo_rede"]
STATUS_PATCH = ["pendente", "em_dia", "critico"]

# colunas devolvidas SEM o senha_acesso_hash (nem o hash sai do servidor)
COLUNAS_ATIVO = """id, nome_ativo, tipo, ip_interno, setor_responsavel,
                   sistema_operacional, data_ultima_verificacao, status_patch,
                   senha_acesso_hash IS NOT NULL AS tem_senha"""


def criar_tabela():
    # O que faz: cria a tabela ativos, se ela ainda não existir
    # Por que faz: evita erro de "tabela não encontrada" na 1ª execução
    # [OBS] nome_ativo é UNIQUE por ser o elo com o MongoDB
    # [OBS] CHAR(60) porque o hash do bcrypt tem sempre 60 caracteres
    executar("""
        CREATE TABLE IF NOT EXISTS ativos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome_ativo VARCHAR(60) NOT NULL UNIQUE,
            tipo VARCHAR(30) NOT NULL,
            ip_interno VARCHAR(45) NOT NULL,
            setor_responsavel VARCHAR(50) NOT NULL,
            sistema_operacional VARCHAR(60) NOT NULL,
            data_ultima_verificacao DATE NOT NULL,
            status_patch VARCHAR(10) NOT NULL,
            senha_acesso_hash CHAR(60) NULL
        )
    """)


def formatar(ativo):
    # O que faz: ajusta o que o JSON não entende (data e o 0/1 do MySQL)
    ativo["data_ultima_verificacao"] = str(ativo["data_ultima_verificacao"])
    ativo["tem_senha"] = bool(ativo["tem_senha"])
    return ativo


def validar_status(status):
    if status not in STATUS_PATCH:
        raise ErroApi("Status de patch inválido. Use: pendente, em_dia ou critico.")


def validar_ativo(dados):
    # O que faz: confere os campos antes de gravar
    # Por que faz: a API pode ser chamada sem passar pela tela
    obrigatorios = ["nome_ativo", "tipo", "ip_interno", "setor_responsavel",
                    "sistema_operacional", "data_ultima_verificacao", "status_patch"]
    for campo in obrigatorios:
        if not str(dados.get(campo) or "").strip():
            raise ErroApi(f"O campo '{campo}' é obrigatório.")

    if len(dados["nome_ativo"]) > 60 or " " in dados["nome_ativo"]:
        raise ErroApi("Nome do ativo: até 60 caracteres e sem espaços (ex.: srv-web-01).")
    if dados["tipo"] not in TIPOS:
        raise ErroApi("Tipo inválido. Use: servidor, estacao ou dispositivo_rede.")
    validar_status(dados["status_patch"])
    try:
        ipaddress.ip_address(dados["ip_interno"])
    except ValueError:
        raise ErroApi("IP interno inválido (ex.: 10.0.10.11).")
    try:
        date.fromisoformat(dados["data_ultima_verificacao"])
    except ValueError:
        raise ErroApi("Data da última verificação deve estar no formato AAAA-MM-DD.")


# =========================================================================
# CRUD
# =========================================================================
def listar_ativos(setor=None, status=None):
    # O que faz: lista os ativos, filtrando por setor e/ou status se vierem
    # [OBS] os valores digitados vão sempre como parâmetro %s
    sql = f"SELECT {COLUNAS_ATIVO} FROM ativos WHERE 1 = 1"
    parametros = []
    if setor:
        sql += " AND setor_responsavel = %s"
        parametros.append(setor)
    if status:
        sql += " AND status_patch = %s"
        parametros.append(status)
    sql += " ORDER BY nome_ativo"
    return [formatar(ativo) for ativo in consultar(sql, tuple(parametros))]


def buscar_por_id(id_ativo):
    # O que faz: devolve um ativo pelo id, ou erro 404
    linhas = consultar(f"SELECT {COLUNAS_ATIVO} FROM ativos WHERE id = %s", (id_ativo,))
    if not linhas:
        raise ErroApi(f"Ativo de id {id_ativo} não encontrado.", 404)
    return formatar(linhas[0])


def buscar_por_nome(nome_ativo):
    # O que faz: devolve o ativo pelo nome, ou None (usado no relatório cruzado)
    linhas = consultar(f"SELECT {COLUNAS_ATIVO} FROM ativos WHERE nome_ativo = %s",
                       (nome_ativo,))
    return formatar(linhas[0]) if linhas else None


def cadastrar_ativo(dados):
    # O que faz: insere um novo ativo (C do CRUD)
    # [OBS] a senha em texto puro nunca chega ao banco, só o hash
    validar_ativo(dados)
    senha = dados.get("senha_acesso")
    senha_hash = gerar_hash_senha(senha) if senha else None
    try:
        linhas, novo_id = executar("""
            INSERT INTO ativos (nome_ativo, tipo, ip_interno, setor_responsavel,
                sistema_operacional, data_ultima_verificacao, status_patch,
                senha_acesso_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (dados["nome_ativo"].strip(), dados["tipo"], dados["ip_interno"].strip(),
             dados["setor_responsavel"].strip(), dados["sistema_operacional"].strip(),
             dados["data_ultima_verificacao"], dados["status_patch"], senha_hash))
    except mysql.connector.IntegrityError:
        # o único campo UNIQUE além do id é o nome_ativo
        raise ErroApi(f"Já existe um ativo chamado '{dados['nome_ativo']}'.", 409)
    return buscar_por_id(novo_id)


def atualizar_status_patch(id_ativo, novo_status):
    # O que faz: muda o status de patch de um ativo (U do CRUD)
    validar_status(novo_status)
    buscar_por_id(id_ativo)  # dá 404 se o id não existir
    executar("UPDATE ativos SET status_patch = %s WHERE id = %s", (novo_status, id_ativo))
    return buscar_por_id(id_ativo)


def marcar_como_critico(nome_ativo):
    # O que faz: coloca status_patch = 'critico' no ativo (quarentena)
    # O que fazer com o resultado: True se o ativo mudou de status agora
    # [OBS] o nome vem do Mongo, mas também vai como parâmetro
    linhas, _ = executar("""UPDATE ativos SET status_patch = 'critico'
                            WHERE nome_ativo = %s AND status_patch <> 'critico'""",
                         (nome_ativo,))
    return linhas > 0


def remover_ativo(id_ativo):
    # O que faz: remove um ativo pelo id (D do CRUD)
    # [OBS] as vulnerabilidades dele continuam no Mongo: não existe
    # cascata entre bancos diferentes
    ativo = buscar_por_id(id_ativo)
    executar("DELETE FROM ativos WHERE id = %s", (id_ativo,))
    return ativo


# =========================================================================
# SENHA DE ACESSO AO ATIVO (bcrypt) - vinda da atividade de bancos
# =========================================================================
def gerar_hash_senha(senha):
    # O que faz: transforma a senha em hash bcrypt (salt aleatório, custo 12)
    # [OBS] o bcrypt só considera os primeiros 72 bytes da senha
    if not senha or len(senha) < 8:
        raise ErroApi("A senha de acesso precisa ter pelo menos 8 caracteres.")
    if len(senha.encode("utf-8")) > 72:
        raise ErroApi("A senha passa de 72 bytes, o limite do bcrypt.")
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def definir_senha(id_ativo, nova_senha):
    # O que faz: grava (ou troca) o hash da senha de um ativo
    buscar_por_id(id_ativo)
    executar("UPDATE ativos SET senha_acesso_hash = %s WHERE id = %s",
             (gerar_hash_senha(nova_senha), id_ativo))


def verificar_senha(id_ativo, senha_informada):
    # O que faz: confere a senha informada com o hash salvo (checkpw)
    # O que fazer com o resultado: True = senha correta
    linhas = consultar("SELECT senha_acesso_hash FROM ativos WHERE id = %s", (id_ativo,))
    if not linhas:
        raise ErroApi(f"Ativo de id {id_ativo} não encontrado.", 404)
    if linhas[0]["senha_acesso_hash"] is None:
        raise ErroApi("Este ativo ainda não tem senha definida.", 409)
    if not senha_informada:
        raise ErroApi("Informe a senha.")
    return bcrypt.checkpw(senha_informada.encode("utf-8"),
                          linhas[0]["senha_acesso_hash"].encode("utf-8"))
