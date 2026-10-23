# =========================================================================
# Painel de Segurança - ponto de entrada (Flask)
# =========================================================================
# MVC: modelos/ (bancos e API externa), visao/ (telas), controles/ (rotas)
# O navegador só fala com as rotas /api; quem acessa os bancos é o servidor.
# =========================================================================
from flask import Flask

import config
from controles import (ativos_controle, painel_controle, reputacao_controle,
                       vulnerabilidades_controle)
from controles.erros import registrar_erros
from modelos import ativo_modelo, conexoes, quarentena, vulnerabilidade_modelo

# as telas da pasta visao são servidas pelo próprio Flask (mesmo endereço da API)
app = Flask(__name__, static_folder="visao", static_url_path="")
app.json.ensure_ascii = False
app.json.sort_keys = False

app.register_blueprint(ativos_controle.rotas)
app.register_blueprint(vulnerabilidades_controle.rotas)
app.register_blueprint(painel_controle.rotas)
app.register_blueprint(reputacao_controle.rotas)
registrar_erros(app)


@app.get("/")
def inicio():
    return app.send_static_file("index.html")


def preparar_bancos():
    # O que faz: conecta no MySQL e no MongoDB e prepara tabela e validador
    # Por que faz: o servidor só pode subir se os dois bancos responderem
    faltando = config.validar_configuracao()
    if faltando:
        print(f"[ERRO] Variáveis ausentes no .env: {', '.join(faltando)}")
        print("       Copie o .env.example para .env e preencha.")
        return False
    try:
        conexoes.conectar_mysql().close()
        print("[OK] Conectado no MySQL.")
    except Exception as erro:
        print(f"[ERRO] MySQL: {erro}")
        return False
    try:
        conexoes.conectar_mongo()
        print("[OK] Conectado no MongoDB.")
    except Exception as erro:
        print(f"[ERRO] MongoDB: {erro}")
        return False

    ativo_modelo.criar_tabela()
    vulnerabilidade_modelo.aplicar_validador()
    print(f"[OK] Quarentena automática: {quarentena.aplicar_quarentena()}")
    return True


if __name__ == "__main__":
    if not preparar_bancos():
        print("[ERRO] Sem os dois bancos o servidor não inicia. Confira o .env "
              "e se o MySQL e o MongoDB estão rodando.")
        exit(1)
    app.run(host=config.HOST, port=config.PORTA, debug=config.DEBUG)
