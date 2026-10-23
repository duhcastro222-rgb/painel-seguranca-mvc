# Configurações do projeto, lidas do .env
# (as credenciais ficam fora do código)
import os
from dotenv import load_dotenv

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_PROJETO, "dados")
load_dotenv(os.path.join(PASTA_PROJETO, ".env"))

OBRIGATORIAS = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME",
                "MONGO_URI", "MONGO_DB", "MONGO_COLLECTION"]


def validar_configuracao():
    # O que faz: devolve as variáveis obrigatórias que faltam no .env
    return [nome for nome in OBRIGATORIAS if not os.getenv(nome)]


MYSQL = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT") or 3306),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD", ""),  # pode ser vazia no ambiente local
    "database": os.getenv("DB_NAME"),
}

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# servidor web: por padrão só na própria máquina e sem modo debug
HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORTA = int(os.getenv("FLASK_PORT") or 5000)
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

# quantas horas uma consulta de IP fica valendo no cache
CACHE_IPS_HORAS = float(os.getenv("CACHE_IPS_HORAS") or 24)
