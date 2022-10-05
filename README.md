# @pybr2022

Robô no Discord da Python Brasil 2022!

## Responsabilidades

- Validar inscrição das pessoas que se inscreveram na Python Brasil pelo EventBrite;
- Liberar acesso a todos os canais de participantes no servidor oficial do evento.

## Desenvolvendo


### Pré requisitos

- Estamos usando o Poetry para gerenciar as dependências do projeto. Siga o guia oficial para instalar o Poetry na sua máquina: https://python-poetry.org/docs/#installation.

### Instalando dependências

```
$ poetry install
```

### Rodando testes

```
$ poetry run pytest
```

### Criando arquivo de configurações

Crie o arquivo `.env` a partir do já existente `local.env` e preencha todas as configurações descritas nele.

```
$ cp local.env .env
```

### Rodando locamente

```
$ poetry run python pybr2022/main.py
```