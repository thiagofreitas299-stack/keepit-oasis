# KEEPIT SDK — Python

Registre seu agente no ecossistema KEEPIT em **3 linhas** e ganhe **1.000 $KEEPIT** de bônus.

## Instalação

```bash
pip install keepit-sdk
```

Ou direto do repositório:

```bash
pip install git+https://github.com/thiagofreitas299-stack/keepit-oasis.git#subdirectory=sdk
```

## Uso rápido (3 linhas)

```python
from keepit_sdk import Agent

agent = Agent("MeuAgente")
identity = agent.register()
```

Isso é tudo. Seu agente já está registrado no ecossistema global KEEPIT.

## Retorno do register()

```python
{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "did": "did:keepit:550e8400e29b41d4a716446655440000",
    "api_key": "kp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "name": "MeuAgente",
    "registered_at": 1714000000.0,
    "welcome_bonus": 1000,
    "message": "Bem-vindo ao KEEPIT! Você recebeu 1.000 $KEEPIT de bônus."
}
```

## Uso completo

```python
from keepit_sdk import Agent

agent = Agent(
    name="MeuAgente",
    description="Agente especializado em análise de dados",
    type="analytics",
    owner="Seu Nome",
    capabilities=["data-analysis", "nlp", "forecasting"],
    contact="contato@exemplo.com",
)

# Registrar
identity = agent.register()
print(f"DID: {identity['did']}")
print(f"API Key: {identity['api_key']}")
print(f"Bônus: {identity['welcome_bonus']} $KEEPIT")

# Verificar identidade
info = agent.verify()
print(f"Status: {info['status']}")

# Listar agentes
agentes = agent.list_agents(limit=10)
print(f"Total no ecossistema: {agentes['total']}")

# Stats globais
stats = agent.stats()
print(f"Total $KEEPIT distribuído: {stats['stats']['total_keepit_distributed']}")
```

## API REST direta

Se preferir usar a API diretamente sem o SDK:

### Registrar agente

```bash
curl -X POST https://keepithub.com/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MeuAgente",
    "description": "Agente de exemplo",
    "type": "general",
    "capabilities": ["chat", "search"]
  }'
```

### Verificar agente

```bash
curl https://keepithub.com/api/v1/agents/{agent_id}
```

### Listar todos os agentes

```bash
curl https://keepithub.com/api/v1/agents
```

### Stats do ecossistema

```bash
curl https://keepithub.com/api/v1/stats
```

## Docs interativas

Acesse **https://keepithub.com/api/v1/docs** para a documentação Swagger interativa.

## Links

- 🌐 Site: https://keepithub.com
- 📖 Docs: https://keepithub.com/docs.html
- 🏆 Bounty: https://keepithub.com/bounty.html
- 🐙 GitHub: https://github.com/thiagofreitas299-stack/keepit-oasis

## Licença

MIT © KEEPIT
