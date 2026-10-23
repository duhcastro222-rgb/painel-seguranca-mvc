# =========================================================================
# Prepara os bancos antes do primeiro uso: cria banco e tabela, cadastra
# 10 ativos e 12 vulnerabilidades de exemplo e roda a quarentena.
# Rodar de novo não duplica nada.
# =========================================================================
import mysql.connector

import config
from modelos import ativo_modelo, conexoes, quarentena, vulnerabilidade_modelo
from modelos.erros import ErroApi

ATIVOS_EXEMPLO = [
    ("srv-web-01", "servidor", "10.0.10.11", "TI", "Ubuntu Server 22.04", "2026-09-01", "pendente"),
    ("srv-banco-dados-01", "servidor", "10.0.10.12", "TI", "Debian 12", "2026-08-15", "em_dia"),
    ("srv-arquivos-02", "servidor", "10.0.10.13", "TI", "Windows Server 2019", "2026-07-30", "em_dia"),
    ("portal-clientes", "servidor", "10.0.10.20", "Comercial", "Ubuntu Server 22.04", "2026-08-20", "em_dia"),
    ("notebook-financeiro-07", "estacao", "10.0.20.7", "Financeiro", "Windows 11 Pro", "2026-09-05", "pendente"),
    ("notebook-diretoria-01", "estacao", "10.0.20.1", "Diretoria", "Windows 11 Pro", "2026-09-06", "pendente"),
    ("estacao_rh_04", "estacao", "10.0.20.44", "Recursos Humanos", "Windows 10 Pro", "2026-08-10", "em_dia"),
    ("switch-core-02", "dispositivo_rede", "10.0.0.2", "Infraestrutura", "Cisco IOS 15.2", "2026-09-03", "pendente"),
    ("firewall-perimetro-01", "dispositivo_rede", "10.0.0.1", "Infraestrutura", "FortiOS 7.2", "2026-09-09", "pendente"),
    ("vpn-gateway-01", "dispositivo_rede", "10.0.0.3", "Infraestrutura", "Ivanti Connect Secure 22.6", "2026-09-08", "pendente"),
]

# 1. banco MySQL - conecta sem escolher banco, porque ele pode não existir
# [OBS] nome de banco não aceita %s, por isso é conferido antes
nome_banco = config.MYSQL["database"]
if not nome_banco.replace("_", "").isalnum():
    exit("[ERRO] DB_NAME inválido no .env (use só letras, números e _).")
dados_conexao = dict(config.MYSQL)
del dados_conexao["database"]
conexao = mysql.connector.connect(**dados_conexao)
conexao.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {nome_banco}")
conexao.close()
print(f"[OK] Banco MySQL '{nome_banco}' pronto.")

ativo_modelo.criar_tabela()

# 2. ativos de exemplo
if len(ativo_modelo.listar_ativos()) == 0:
    for nome, tipo, ip, setor, so, data, status in ATIVOS_EXEMPLO:
        ativo_modelo.cadastrar_ativo({
            "nome_ativo": nome, "tipo": tipo, "ip_interno": ip,
            "setor_responsavel": setor, "sistema_operacional": so,
            "data_ultima_verificacao": data, "status_patch": status,
        })
    print(f"[OK] {len(ATIVOS_EXEMPLO)} ativos de exemplo cadastrados.")
else:
    print("[INFO] A tabela ativos já tem dados; nada inserido.")

# 3. vulnerabilidades
conexoes.conectar_mongo()
vulnerabilidade_modelo.aplicar_validador()
try:
    print(f"[OK] {vulnerabilidade_modelo.carregar_vulnerabilidades()} vulnerabilidades carregadas.")
except ErroApi:
    print("[INFO] A coleção de vulnerabilidades já tem dados; nada inserido.")

# 4. quarentena
print(f"[OK] Quarentena automática: {quarentena.aplicar_quarentena()}")
