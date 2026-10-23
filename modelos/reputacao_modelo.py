# =========================================================================
# Verificador de reputação de IPs (vem da atividade de requests)
# API: ip-api.com (gratuita, até 45 consultas por minuto)
# Novidades: cache local em dados/cache_ips.json e relatório consolidado
# em dados/relatorio_ips.json
# =========================================================================
import json
import os
import time
from datetime import datetime

import requests

import config
from modelos.erros import ErroApi

arquivo_ips = os.path.join(config.PASTA_DADOS, "ips.txt")
arquivo_cache = os.path.join(config.PASTA_DADOS, "cache_ips.json")
arquivo_relatorio = os.path.join(config.PASTA_DADOS, "relatorio_ips.json")

# campos que pedimos para a API
campos = "status,message,country,isp,proxy,hosting"


def ler_json(caminho, padrao):
    # O que faz: lê um arquivo JSON; se ele não existir, devolve o padrão
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def gravar_json(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, indent=4, ensure_ascii=False)


def ler_ips():
    # lê a lista de IPs da atividade de requests, ignorando linhas vazias
    lista = []
    with open(arquivo_ips, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            ip = linha.strip()
            if ip != "":
                lista.append(ip)
    return lista


def consultar_ip(ip):
    # mesma função do verificador_ips.py
    resultado = {}
    resultado["ip"] = ip

    try:
        resposta = requests.get(f"http://ip-api.com/json/{ip}?fields={campos}", timeout=5)
    except requests.exceptions.RequestException:
        resultado["risco"] = "ERRO"
        resultado["motivo"] = "falha na conexao"
        return resultado

    if resposta.status_code != 200:
        resultado["risco"] = "ERRO"
        resultado["motivo"] = "a API nao respondeu direito"
        return resultado

    dados = resposta.json()

    # a API responde "fail" quando o IP e invalido ou reservado
    if dados["status"] != "success":
        resultado["risco"] = "INVALIDO"
        resultado["motivo"] = dados["message"]
        return resultado

    # regra simples de reputacao
    if dados["proxy"]:
        resultado["risco"] = "ALTO"
        resultado["motivo"] = "IP de proxy, VPN ou Tor"
    elif dados["hosting"]:
        resultado["risco"] = "MEDIO"
        resultado["motivo"] = "IP de datacenter"
    else:
        resultado["risco"] = "BAIXO"
        resultado["motivo"] = "IP comum de provedor"

    resultado["pais"] = dados["country"]
    resultado["provedor"] = dados["isp"]
    return resultado


def ainda_valido(consultado_em):
    # O que faz: diz se uma entrada do cache ainda está dentro do prazo
    idade = datetime.now() - datetime.fromisoformat(consultado_em)
    return idade.total_seconds() < config.CACHE_IPS_HORAS * 3600


def verificar_ips(ips):
    # O que faz: verifica os IPs (cache primeiro, depois API) e grava o
    # relatório consolidado
    if not isinstance(ips, list):
        raise ErroApi("Informe pelo menos um IP.")
    # ignora linhas vazias e IPs repetidos
    lista = []
    for ip in ips:
        ip = str(ip).strip()
        if ip != "" and ip not in lista:
            lista.append(ip)
    ips = lista
    if len(ips) == 0:
        raise ErroApi("Informe pelo menos um IP.")
    if len(ips) > 30:
        raise ErroApi("Informe no máximo 30 IPs por vez (limite gratuito da API).")

    cache = ler_json(arquivo_cache, {})
    resultados = []
    consultas_api = 0

    for ip in ips:
        if ip in cache and ainda_valido(cache[ip]["consultado_em"]):
            resultado = dict(cache[ip]["resultado"])  # cópia: não suja o cache
            resultado["origem"] = "cache"
        else:
            if consultas_api > 0:
                time.sleep(1.5)  # respeita o limite da API
            resultado = consultar_ip(ip)
            consultas_api = consultas_api + 1
            # erro de conexão não vai para o cache
            if resultado["risco"] != "ERRO":
                cache[ip] = {"resultado": resultado,
                             "consultado_em": datetime.now().isoformat(timespec="seconds")}
            resultado = dict(resultado)
            resultado["origem"] = "api"
        resultados.append(resultado)

    gravar_json(arquivo_cache, cache)

    # conta quantos IPs cairam em cada nivel de risco
    resumo = {}
    for resultado in resultados:
        risco = resultado["risco"]
        if risco in resumo:
            resumo[risco] = resumo[risco] + 1
        else:
            resumo[risco] = 1

    relatorio = {}
    relatorio["data_da_analise"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    relatorio["total_de_ips"] = len(resultados)
    relatorio["consultas_na_api"] = consultas_api
    relatorio["respostas_do_cache"] = len(resultados) - consultas_api
    relatorio["resumo_por_risco"] = resumo
    relatorio["resultados"] = resultados
    gravar_json(arquivo_relatorio, relatorio)
    return relatorio


def ultimo_relatorio():
    # O que faz: devolve o último relatório gravado, ou None se não houver
    return ler_json(arquivo_relatorio, None)


def limpar_cache():
    # O que faz: esvazia o cache (força nova consulta na API)
    total = len(ler_json(arquivo_cache, {}))
    gravar_json(arquivo_cache, {})
    return total
