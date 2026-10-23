# =========================================================================
# Quarentena automática: ativo com vulnerabilidade aberta e score acima
# de 9.0 passa a ter status_patch "critico".
# A condição está no MongoDB e o efeito no MySQL. Roda na subida do
# servidor e depois de toda gravação que pode mudar o resultado.
# =========================================================================
from modelos import ativo_modelo, vulnerabilidade_modelo


def aplicar_quarentena():
    # O que faz: busca os ativos no Mongo e marca como critico no MySQL
    # O que fazer com o resultado: "isolados_agora" é usado no aviso da tela
    em_quarentena = vulnerabilidade_modelo.ativos_para_quarentena()
    isolados_agora = []
    for nome_ativo in em_quarentena:
        if ativo_modelo.marcar_como_critico(nome_ativo):
            isolados_agora.append(nome_ativo)
    return {"em_quarentena": em_quarentena, "isolados_agora": isolados_agora}


def ativo_em_quarentena(nome_ativo):
    # O que faz: diz se o ativo ainda tem falha aberta com score > 9.0
    # Por que faz: enquanto for verdade, não deixa tirar o status critico
    return nome_ativo in vulnerabilidade_modelo.ativos_para_quarentena()
