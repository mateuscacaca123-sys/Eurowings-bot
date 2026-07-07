# ✈️ EuroWings Digital Assistant — Discord Bot

Assistente virtual da Eurowings para atendimento ao cliente no Discord.

## Comandos

| Comando | O que faz |
|---|---|
| `!ajuda` | Lista todos os comandos |
| `!faq` | Mostra as perguntas frequentes |
| `!faq <número>` | Resposta detalhada (ex: `!faq 1`) |
| `!checkin` | Como fazer check-in online |
| `!bagagem` | Guia de bagagem |
| `!voo` | Informações sobre voos |
| `!contato` | Canais de suporte Eurowings |
| `!status` | Verifica se o bot está online |

## Perguntas frequentes incluídas

1. Como fazer check-in online
2. Regras de bagagem de mão
3. Como adicionar bagagem despachada
4. Como alterar ou cancelar reserva
5. Direitos em caso de atraso/cancelamento (EU 261/2004)
6. Programa de fidelidade Boomerang Club
7. Viagem com animais de estimação
8. Franquia de bagagem por tarifa

## Como rodar o bot

### 1. Criar o bot no Discord Developer Portal

1. Acesse [discord.com/developers/applications](https://discord.com/developers/applications)
2. Clique em **New Application** → dê o nome **EuroWings Digital Assistant**
3. Vá em **Bot** → clique em **Reset Token** → copie o token
4. Ative **Message Content Intent** (em Privileged Gateway Intents)

> ⚠️ **Nunca compartilhe seu token publicamente.** Se exposto, regenere-o imediatamente.

### 2. Convidar o bot para o servidor

No painel do desenvolvedor:
1. Vá em **OAuth2 → URL Generator**
2. Marque o escopo: `bot`
3. Permissões: `Send Messages`, `Read Message History`, `Embed Links`
4. Copie o link e abra no navegador

### 3. Rodar o bot

O token já está configurado como secret do Replit (`DISCORD_TOKEN`).

```bash
cd bot
source .venv/bin/activate
python bot.py
```

## Resposta automática por palavras-chave

Em canais chamados `#suporte`, `#atendimento`, `#duvidas`, `#help` ou `#ajuda`, o bot detecta automaticamente palavras-chave nas mensagens e responde sem precisar de comando.

**Exemplos de palavras detectadas:**
- "check-in", "embarque", "boarding"
- "bagagem", "mala", "cabine"
- "cancelar", "alterar", "remarcar"
- "atrasado", "cancelado", "compensação"
- "pet", "animal", "cachorro", "gato"

## Personalizar

### Editar FAQ

No `bot.py`, edite o dicionário `FAQ`:

```python
FAQ = {
    1: {
        "pergunta": "Sua pergunta?",
        "resposta": "Sua resposta.",
    },
    # ...
}
```

### Editar canais com resposta automática

```python
CANAIS_SUPORTE = {"suporte", "atendimento", "duvidas", "help"}
```
