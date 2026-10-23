ATIVIDADE 3 - Painel de Segurança (Web + MySQL + MongoDB)
RM 573427

Painel web para controlar os ativos de TI (MySQL) e as vulnerabilidades
encontradas neles (MongoDB). Usa as peças das atividades anteriores: as
telas de interfaces-web, o CRUD do quasecpBD e o verificador de IPs da
atividade de requests.


COMO EXECUTAR

Precisa de Python 3.11+, MySQL e MongoDB rodando na máquina.

1. pip install -r requirements.txt
2. copiar o .env.example para .env e ajustar usuário/senha se precisar
3. python inicializar_bancos.py   (cria o banco e carrega os dados de exemplo)
4. python app.py
5. abrir http://127.0.0.1:5000

Se o MySQL ou o MongoDB não conectar, o servidor não inicia e mostra o motivo.


ESTRUTURA (MVC)

modelos/    acesso ao MySQL, ao MongoDB e ao ip-api
controles/  rotas da API em Flask (devolvem JSON)
visao/      telas em HTML, CSS e JavaScript (fetch)
dados/      dataset de vulnerabilidades, lista de IPs, cache e relatório .json
prints/     prints das telas


PERGUNTAS DA ATIVIDADE

Por que ativos em tabela e vulnerabilidades em documentos?
Todo ativo tem os mesmos campos, então cabe numa tabela. Já cada
vulnerabilidade tem detalhes diferentes conforme a categoria (porta,
endpoint, pacote...), e no MongoDB cada documento guarda só o que precisa.

Por que o navegador nunca fala direto com o banco?
Porque a senha do banco ficaria exposta no JavaScript e qualquer pessoa
poderia rodar qualquer comando. A API é a única porta: valida os dados e
aplica as regras antes de acessar o banco.

Como a API decide qual banco consultar?
Pela rota. /api/ativos usa o MySQL, /api/vulnerabilidades usa o MongoDB.
O relatório cruzado e a quarentena usam os dois e juntam o resultado no
Python, ligando nome_ativo com ativo_relacionado.


EXTRAS

Quarentena automática: se um ativo tem vulnerabilidade aberta com
score_cvss acima de 9.0, o status de patch dele vira "critico". Roda
sozinha sempre que uma vulnerabilidade ou ativo é gravado.

Reputação de IPs: consulta o ip-api.com, guarda as respostas em
dados/cache_ips.json (validade de 24h) e grava o relatório consolidado em
dados/relatorio_ips.json.


PRINTS

01_inicio.png                  visão geral
02_ativos.png                  CRUD de ativos
03_vulnerabilidades.png        CRUD de vulnerabilidades
04_relatorio_cruzado.png       relatório do ativo srv-web-01
05_reputacao_ips.png           verificação de IPs
06_erro_ativo_inexistente.png  mensagem de erro para ativo que não existe
