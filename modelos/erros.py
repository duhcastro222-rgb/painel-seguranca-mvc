# Erro de regra de negócio já com o código HTTP
# (400 inválido, 404 não existe, 409 conflito, 422 referência inválida)


class ErroApi(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
