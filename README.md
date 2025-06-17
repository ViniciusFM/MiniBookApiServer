# Mini Book API Server

O **MiniBookApiServer** é um sistema de *backend* voltado para viabilizar a venda de livros. Ele expõe uma interface HTTP com diversos *endpoints* que permitem consultar o catálogo de livros disponíveis, iniciar uma venda adicionando livros a uma compra, e confirmar/cancelar a venda. A autenticação é simples, por meio de um *token* previamente definido. Neste [link](docs/insomnia/insomnia_config_file.yaml) é fornecida uma coleção configurável para o **Insomnia**.

A estrutura de dados do servidor é centrada em três tabelas principais: `books`, `sales` e `books_sales` (ver em [docs/api_docs](docs/api_docs.md#schema-do-bando-de-dados)). A tabela `books` armazena os dados do acervo de livros, incluindo título, autor, preço (em centavos), ano e unidades disponíveis. Já a tabela `sales` registra as vendas feitas, identificadas por um UUID único, com campos como valor total e data da compra. A tabela intermediária `books_sales` representa a relação N-para-N entre livros e vendas, indicando quantas unidades de cada livro foram adquiridas em uma venda específica.

O fluxo de funcionamento da API exige que uma venda seja confirmada em até 30 minutos após sua criação, sob risco de ser descartada automaticamente. A confirmação da venda é feita via *endpoint* [Confirm Sale](docs/api_docs.md#confirm-sale), momento em que as unidades dos livros são de fato debitadas do estoque. 

Este código possui partes do respositório [ChatAppServer](https://github.com/ViniciusFM/ChatApp-Server), sendo tanto este quanto aquele licenciados sob a AGPLv3. Veja [LICENSE](./LICENSE) e [DISCLAIMER](docs/DISCLAIMER.md) para mais informações.

<p align="center">
    <img src="docs/imgs/logo/minibookapi_logo.svg" width="200">
</p>

## Interação com o serviço Mini Book API

Veja em [docs/api_docs.md](docs/api_docs.md) a documentação completa do serviço Mini Book API, para saber como interagir com o sistema. Atente-se à seção [Fluxos de Compras](docs/api_docs.md#fluxos-de-compras) para compreender como criar um aplicativo de compra de livros.

## Configurando o servidor para executar localmente

1) Baixar o python 3.x
2) Instalar o **virtualenv**:
```bash
pip3 install virtualenv
```
3) Criar um ambiente virtual
```bash
virtualenv .venv
```
4) Entrar no ambiente virtual toda vez que for executar o MiniBookApiServer
```bash
# No unix-like
source ./.venv/bin/activate

# No windows
.\.venv\Scripts\activate

# para desativar
deactivate
```
5) Instalar as dependencias do projeto
```bash
pip install -r requirements.txt
```
6) Configure um arquivo `config.json`.
    * **Criando com um *script* automatizado**: para isso execute o comando abaixo e siga as instruções.
        ```bash
        python serverman.py
        ```
    * **Criando manualmente**: siga o exemplo do arquivo `config-example.json`.
        * Para criar um valor para o parâmetro `TOKEN` e `TOKEN_ADMIN` de `config.json` execute:
        ```bash
        python -c "import secrets; print(secrets.token_hex(32))"
        ```
        * Copie o valor gerado para o arquivo de configuração.
        * Insira as informações válidas de PIX para configurar um mecanismo de pagamento.
            * `PIX_NAME`: Corresponde ao nome da entidade recebedora.
            * `PIX_KEY`: Corresponde à chave da entidade recebedora. A chave tem que estar em conformidade com o que estipula o projeto [***pybrcode***](https://github.com/ViniciusFM/pybrcode?tab=readme-ov-file#how-to-use) para parâmetros de chave pix.
7) Executar a aplicação flask localmente:
```bash
flask run --debug --host=0.0.0.0 --port=5000
```
8) Utilize uma aplicação para testar a API. Sugestões:
    * [Insomnia](https://insomnia.rest/download)
    * [Postman](https://www.postman.com/)
