# Documentação da API

Esta é a documentação do MiniBookApi. Caso esteja usando o software [**Insomnia**](https://insomnia.rest/download), você pode utilizar a coleção pré-definida disponível [aqui](./insomnia/insomnia_config_file.yaml). Após a [importação](https://docs.insomnia.rest/insomnia/import-export-data) do arquivo de configuração do **Insomnia**, o usuário deve alterar o `Ambiente da Coleção` de `Localhost` para `PythonAnywhere`, caso queira realizar requisições ao servidor remoto. É importante que você edite o ambiente `PythonAnywhere` com as credenciais (i.e. *token*) que lhe foram passadas.

Confira [aqui](#endpoints) o índice de *endpoints* que você pode utilizar para implementar um aplicativo de vendas de livros.

### Sumário

1. [*Schema* do Banco de Dados](#schema-do-bando-de-dados): 
    * Veja como são organizados os dados na API.
2. [Fluxos de Compras](#fluxos-de-compras): 
    * Entenda o fluxo de requisições para realizar uma compra pela API.
3. [*Endpoints*](#endpoints):
    * Veja a lista de *endpoints* disponíveis para a interação com a API.
4. [Exceções da API](#exceções-da-api):
    * Entenda como interpretar as exceções da API.

# *Schema* do Bando de Dados

Leia os comentários do código abaixo para entender como os dados estão organizados neste servidor.

```sql
/* 
 * Tabela de vendas
 * ----------------
 * OBS: perceba que preços são tratados como [integers] neste
 * servidor. Pense nas unidades como "centavos", ou seja, se
 * total = 50000, então o valor total da compra é R$ 50,00
 * - Uma [Sale] precisa ser concluída em até 30 minutos.
 *   Ou será deletada do sistema automaticamente.
 * - Para concluir uma venda, você precisa requisitar /sale/confirm
 */
CREATE TABLE sales (
        id INTEGER NOT NULL, 
        total INTEGER NOT NULL, /* valor total da venda*/
        sale_ts DATETIME,       /* data e hora da compra */
        uuid VARCHAR(32),       /* identificador de compra */
        concluded BOOLEAN,      /* se a venda foi concluída */
        PRIMARY KEY (id)
);
/* 
 * Tabela de livros
 * ----------------
 * OBS: aqui também o preço de cada livro é tratado como
 * unidades de "centavo"
 * - O valor de [unities] decresce conforme as vendas para os
 *   livros são confirmadas. Este valor não será negativo.
 * - Para pegar a imagem, utilize a rota /img/:img_res
 */

CREATE TABLE books (
        id INTEGER NOT NULL, 
        title VARCHAR(256) NOT NULL,        /* Título do livro */
        author VARCHAR(256) NOT NULL,       /* Nome do autor do livro */
        publisher VARCHAR(256) NOT NULL,    /* Nome da editora que lançou o livro */
        description TEXT,                   /* Descrição do produto */
        price INTEGER NOT NULL,             /* preço do livro */
        year INTEGER NOT NULL,              /* ano de lançamento do livro */
        unities INTEGER NOT NULL,           /* unidades disponíveis no acervo */
        img_res VARCHAR(32),                /* ref. da imagem no servidor */
        PRIMARY KEY (id)
);
/* 
 * Tabela da relação Livro-Venda
 * -------------------------------
 * 1 venda pode ter N livros
 * 1 livro pode estar envolvido em N vendas
 * Portanto, a relação Livro-Venda é N para N
 * A relação carrega consigo o valor de [unities]
 * resultando no número de unidades consumidas de
 * um determinado livro pela venda realizada.
 * ex. books_sales(2, 1, 3) significa:
 *  - "3" unidades do livro "2" foram adquiridos na venda "1"
 */
CREATE TABLE books_sales (
        book_id INTEGER NOT NULL, 
        sale_id INTEGER NOT NULL, 
        unities INTEGER NOT NULL, /* unidades vendidas do livro */
        PRIMARY KEY (book_id, sale_id), 
        FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE RESTRICT, 
        FOREIGN KEY(sale_id) REFERENCES sales (id) ON DELETE CASCADE
);
```

## Fluxos de Compras

Para realizar uma compra no sistema, a aplicação, que está consumindo a `MiniBookApi`, deverá ter acesso a um `token` para conseguir prosseguir com a sequência de cadastro de compra. Peça ao `Admin` do sistema esta informação para acessar.

<img src="imgs/seq_diagram_sale.png">

### Sequência de passos

1. Peça ao servidor o [acesso ao acervo de livros](#list-books) armazenados no servidor. O servidor irá lhe retornar um **JSONArray** de **Books** contendo todos os livros [cadastrados](#new-book) no servidor.

2. Após receber os livros, complete a requisição carregando, sob demanda, as [imagens das capas dos livros](#get-img). O **JSONArray** do passo anterior contém o *UUID* de `img_res` que correponde ao complementa a requisição [Get Image](#get-img).

3. Inicie a compra, requisitando por uma [New Sale](#new-sale). Para cada livro da compra, insira um par de *chave-valor* `{<id do livro>: <unidades>}` no corpo JSON da requisição.

4. [Confirme](#confirm-sale) ou [Cancele](#cancel-sale) a compra. Você tem até 30 minutos para [confirmar a sua compra](#confirm-sale), caso contrário, o servidor irá automaticamente remover a sua compra não concluída.

# *Endpoints*

> OBS: Os *endpoints* que requerem *token* passam pela verificação [*auth_required*](#auth-required).

<table>
    <thead>
        <tr><th colspan="2">Requer autenticação via <i>Token</i></th><th>Não requer <i>Token</i></th></tr>
    </thead>
    <tbody>
        <tr>
            <td><a href="#cancel-sale"><img src="imgs/route-01.png"></a></td>
            <td><a href="#new-sale"><img src="imgs/route-03.png"></a></td>
            <td><a href="#get-img"><img src="imgs/route-05.png"></a></td>
        </tr>
        <tr>
            <td><a href="#confirm-sale"><img src="imgs/route-02.png"></a></td>
            <td><a href="#new-book"><img src="imgs/route-04.png"></a> <b>[1]</b></td>
            <td rowspan="2"><a href="#list-books"><img src="imgs/route-06.png"></a></td>
        </tr>
        <tr>
            <td colspan="2"><a href="#list-sales"><img src="imgs/route-07.png"></a></td>
        </tr>
    </tbody>
    <tfoot>
        <tr>
            <td colspan="3"><i>OBS: <b>[1]</b> Necessita token de administrador.</i></td>
        </tr>
    </tfoot>
</table>

## Auth Required

Todas as rotas marcadas com `auth_required` devem incluir um `HTTP Header` tal como a especificação abaixo:

```plain
Header:
    Authorization: Bearer this-should-be-the-token
Error Status:
	* 403, if the token is invalid or expired.
```
**Importante**: Há dois tipos de *tokens*. confira o [config-example.json](../config-example.json) para configurá-los:
* `TOKEN`: permissão de acesso para registrar compras de livros.
* `TOKEN_ADMIN`: permissão para inserir novos livros no acervo.

## Cancel Sale
> OBS: Esta rota requer autenticação ([auth_required](#auth-required))

Cancele uma compra ainda não concluída.

```plain
Methods:
    DELETE
Route:
    /sale/cancel
Input:
    JSON(sales_uuid:str)
Output:
    Response(status=200)
Exceptions:
    * 404 - SALE_NOT_FOUND
    * 422 - SALE_CAN_NOT_BE_CANCELED
```

### Input

Envie o UUID da venda, em um corpo JSON, para **CANCELAR** a venda.

```json
{
    "sale_uuid": "352d309c1d52496589535313b09c4a82"
}
```

## Confirm Sale
> OBS: Esta rota requer autenticação ([auth_required](#auth-required))

Conclua uma compra que ainda não foi marcada como concluída.

```plain
Methods:
    PUT
Route:
    /sale/confirm
Input:
    JSON(sales_uuid:str)
Output:
    Response(status=200)
Exceptions:
    * 404 - SALE_NOT_FOUND
    * 422 - SALE_ALREADY_CONCLUDED
    * 422 - SALE_UNITIES_NOT_ENOUGH
```

### Input

Envie o UUID da venda, em um corpo JSON, para **CONCLUIR** a venda.

```json
{
    "sale_uuid": "352d309c1d52496589535313b09c4a82"
}
```

## Get Img

Retorna um `JPEG` de um recurso de imagem identificada por um `UUID`.

```plain
Methods:
    GET
Route:
    /img/<string:img_res>
Input:
    URL Path (img_res): uuid to image resource
Output:
    image/jpeg
Exceptions:
    * 404 - IMG_NOT_FOUND
```

## List Books

Colete a lista completa de livros disponíveis no acervo da API.

```plain
Methods:
    GET
Route:
    /book/ls
Input:
    Nenhum
Output:
    JSONArray<Book>
Exceptions:
    Nenhum
```

### Output

Veja o [*Schema* do Banco de Dados](#schema-do-bando-de-dados) para compreender os campos.

```json
[
	{
		"author": "Fulano da Silva",
		"description": "Este é um livro sobre...",
		"id": 1,
		"img_res": "f1a000ee80da4ed2a050df83d15c1758",
		"price": 5000,
        "publisher": "Editora Hello",
		"title": "O Mundo das Compras Online: A Saga",
		"unities": 5,
		"year": 1985
	},
	{
		"author": "Siclano da Silva",
		"description": "Este é um livro sobre...",
		"id": 2,
		"img_res": "fa273196396c4df8b6fd4476ab5323e9",
		"price": 3200,
        "publisher": "Editora Hello",
		"title": "Uma Aventura e Tanto",
		"unities": 1,
		"year": 2003
	},
    ...
]
```

## List Sales
> OBS: Esta rota requer autenticação ([auth_required](#auth-required))

Colete a lista completa de vendas realizadas na API.

```plain
Methods:
    GET
Route:
    /sale/ls
Input:
    Nenhum
Output:
    JSONArray<Sale>
Exceptions:
    Nenhum
```

### Output

Veja o [*Schema* do Banco de Dados](#schema-do-bando-de-dados) para compreender os campos.

> OBS: `books_sales` é construído a partir da relação **Book-Sale**.

```json
[
	{
		"books_sales": [
			{
				"book_id": 1,
				"book_price": 5000,
				"book_title": "O Mundo das Compras Online: A Saga",
				"unities": 2
			},
			{
				"book_id": 2,
				"book_price": 3200,
				"book_title": "Uma Aventura e Tanto",
				"unities": 1
			}
		],
		"id": 1,
		"sale_ts": "Sun, 15 Jun 2025 19:45:46 GMT",
		"total": 13200,
		"uuid": "7cdce07d6216483f8efa106a0c2a83fb"
	},
    ...
]
```

## New Sale
> OBS: Esta rota requer autenticação ([auth_required](#auth-required))

Crie a intenção de compra de uma lista de livros na API. A disponibilidade dos livros é verificada somente durante a confirmação da compra. Caso a compra não seja [confirmada](#confirm-sale) em até 30 minutos, ela desaparecerá da base de dados.

```plain
Methods:
    POST
Route:
    /sale/new
Input:
    JSON(books_sale_data:json)
Output:
    JSON<Sale + Pix QRCode in Base64>
Exceptions:
    * 404 - BOOK_NOT_FOUND
    * 422 - SALE_IS_EMPTY
```

### Input

A entrada consiste em um `JSON` o par chave-valor representa, respectivamente, o **ID do livro** e as **unidades** que se deseja levar daquele livro na compra.

```json
{
    "books_sale_data": {
        "1": 2, 
        "2": 1
    }
}
```

### Output

Veja o [*Schema* do Banco de Dados](#schema-do-bando-de-dados) para compreender os campos. Você pode disponibilizar um **QR Code** para facilitar o pagamento do livro, bastando decodificar em `Base64` o valor do campo `pix_b64` que irá produzir um `PNG` contendo a informação de [**PIX**](https://www.bcb.gov.br/estabilidadefinanceira/pix) (Método de pagamento comum no Brasil), ou pela coleta direta do código em `pix_str`.

> OBS: `books_sales` é construído a partir da relação **Book-Sale**.

```json
{
	"books_sales": [
		{
			"book_id": 3,
			"book_price": 5000,
			"book_title": "Test 1",
			"unities": 2
		},
		{
			"book_id": 4,
			"book_price": 5000,
			"book_title": "Test 2",
			"unities": 1
		}
	],
	"id": 6,
	"pix_b64": "data:image/png;base64,...",
    "pix_str": "00020101021226750014BR.GOV.BCB.PIX0...",
	"sale_ts": "Sun, 15 Jun 2025 19:53:39 GMT",
	"total": 15000,
	"uuid": "352d309c1d52496589535313b09c4a82"
}
```

## New Book
> OBS: Esta rota requer autenticação com **TOKEN_ADMIN** ([auth_required](#auth-required))

Insira um livro no acervo de vendas da API.

```plain
Methods:
    POST
Route:
    /sale/new
Input:
    JSON:
        - title: str,
        - author: str,
        - price: int,
        - unities: int,
        - year: int,
        - description: str (optional),
        - img: base64 (optional)
Output:
    JSON<Book>
Exceptions:
    * 406 - INVALID_IMG_RESOLUTION
    * 406 - INVALID_B64_FORMAT
    * 400 - UNKNOW_IMG_CRETION_PROBLEM
```

### Input

> OBS[*img*]: A resolução máxima para a imagem é descrita em [res.py](../res.py) como: 1080px de largura por 1080px de altura.

```json
{
	"title": "Test 3",
	"author": "Test Author 3",
    "publisher": "Editora Hello",
	"price": 5000,
	"unities": 10,
	"year": 2025,
	"description": "desc test",
	"img": "base64 encoding of a image for cover..."
}
```

### Output

> OBS: *img_res* pode ser usada na requisição [Get Image](#get-img) para acessar o recurso de imagem.

```json
{
	"author": "Test Author 3",
	"description": "desc test",
	"id": 3,
	"img_res": "b92535fca827441d97d879712f3197ed",
	"price": 5000,
    "publisher": "Editora Hello",
	"title": "Test 3",
	"unities": 10,
	"year": 2025
}
```

# Exceções da API

As exceções possíveis do servidor são as listadas na [tabela abaixo](#tabela-de-exceções). Você pode conferir a partir do código-fonte em [exceptions.py](../exceptions.py).

## Um exemplo de resposta com exceção

Abaixo consta a resposta do servidor a uma requisição para encontrar uma imagem utilizando a rota [Get Image](#get-img). O *status code* de resposta foi `404`.

```json
{
    "errcode": 7,
    "errmsg": "Image resource not found.",
    "extra": null
}
```

* *errcode* [**INT**]: corresponde a um identificador numérico único do tipo de exceção.
* *errmsg* [**STR**]: mensagem informativa da exceção ocorrida na API.
* *extra* [**STR?**]: retorna um conteúdo extra informativo da falha.

## Tabela de Exceções

| Classe de Exceção          | *errmsg* | *errcode* | HTTP Status |
|----------------------------|---------------------------|---|-----|
| MINI_BOOK_API_EXCP         | 'Mini Book API Exception' | 0 | 400 |
| INVALID_BODY               | 'Invalid request body.' | 1 | 400 |
| TOKEN_REQUIRED             | 'A token is required to proceed this operation' | 2 | 403 |
| TOKEN_INVALID              | 'The token is invalid or expired' | 3 | 403 |
| BOOK_NOT_FOUND             | 'Book not found.' | 4 | 404 |
| INVALID_B64_FORMAT         | 'Invalid base64 encoding.' | 5 | 406 |
| UNKNOW_IMG_CRETION_PROBLEM | 'Problem during image creation.' | 6 | 400 |
| IMG_NOT_FOUND              | 'Image resource not found.' | 7 | 404 |
| INVALID_IMG_RESOLUTION     | 'Invalid image resolution.' | 8 | 406 |
| SALE_NOT_FOUND             | 'Sale not found.' | 9 | 404 |
| SALE_UNITIES_NOT_ENOUGH    | 'Not enough unities for sale.' | 10 | 422 |
| SALE_IS_EMPTY              | 'Sale does not have any books.' | 11 | 422 |
| SALE_CAN_NOT_BE_CANCELED   | 'This sale can not be canceled because it is already concluded.' | 12 | 422 |
| SALE_ALREADY_CONCLUDED     | 'This sale is already concluded.' | 13 | 422 |
| PIX_EXCEPTION              | 'Something went wrong on generating pix qrcode. Contact admin.' | 14 | 500 |

## Para uso em **StringRes** no Android

### Versão en-us

```xml
<string name="MINI_BOOK_API_EXCP"> Mini Book API Exception.</string>
<string name="INVALID_BODY"> Invalid request body.</string>
<string name="TOKEN_REQUIRED"> A token is required to proceed this operation.</string>
<string name="TOKEN_INVALID"> The token is invalid or expired.</string>
<string name="BOOK_NOT_FOUND"> Book not found.</string>
<string name="INVALID_B64_FORMAT"> Invalid base64 encoding.</string>
<string name="UNKNOW_IMG_CRETION_PROBLEM"> Problem during image creation.</string>
<string name="IMG_NOT_FOUND"> Image resource not found.</string>
<string name="INVALID_IMG_RESOLUTION"> Invalid image resolution.</string>
<string name="SALE_NOT_FOUND"> Sale not found.</string>
<string name="SALE_UNITIES_NOT_ENOUGH"> Not enough unities for sale.</string>
<string name="SALE_IS_EMPTY"> Sale does not have any books.</string>
<string name="SALE_CAN_NOT_BE_CANCELED"> This sale can not be canceled because it is already concluded.</string>
<string name="SALE_ALREADY_CONCLUDED"> This sale is already concluded.</string>
<string name="PIX_EXCEPTION"> Something went wrong on generating pix qrcode. Contact admin.</string>
```

### Versão pt-br

```xml
<string name="MINI_BOOK_API_EXCP">Exceção da Mini Book API.</string>
<string name="INVALID_BODY">Corpo da requisição inválido.</string>
<string name="TOKEN_REQUIRED">Um token é necessário para prosseguir com esta operação.</string>
<string name="TOKEN_INVALID">O token é inválido ou expirou.</string>
<string name="BOOK_NOT_FOUND">Livro não encontrado.</string>
<string name="INVALID_B64_FORMAT">Codificação base64 inválida.</string>
<string name="UNKNOW_IMG_CRETION_PROBLEM">Problema durante a criação da imagem.</string>
<string name="IMG_NOT_FOUND">Recurso de imagem não encontrado.</string>
<string name="INVALID_IMG_RESOLUTION">Resolução de imagem inválida.</string>
<string name="SALE_NOT_FOUND">Venda não encontrada.</string>
<string name="SALE_UNITIES_NOT_ENOUGH">Unidades insuficientes para a venda.</string>
<string name="SALE_IS_EMPTY">A venda não possui nenhum livro.</string>
<string name="SALE_CAN_NOT_BE_CANCELED">Esta venda não pode ser cancelada porque já foi concluída.</string>
<string name="SALE_ALREADY_CONCLUDED">Esta venda já foi concluída.</string>
<string name="PIX_EXCEPTION">Ocorreu um erro ao gerar o QR Code do Pix. Contate o administrador.</string>
```
