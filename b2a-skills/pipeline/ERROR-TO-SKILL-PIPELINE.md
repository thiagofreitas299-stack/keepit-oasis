# 🔁 PIPELINE: ERRO → SKILL → MARKETPLACE B2A
> Sistema de conversão automática de erros operacionais em skills vendáveis no KEEPITHUB
> Criado por ordem de Thiago Freitas | 2026-05-29

---

## VISÃO GERAL

```
ERRO DETECTADO
     ↓
DIAGNÓSTICO TÉCNICO (causa raiz, contexto, impacto)
     ↓
ABSTRAÇÃO (generalizar o problema: acontece em outros agentes?)
     ↓
SOLUÇÃO EMPACOTADA (algoritmo, regra, módulo de código)
     ↓
SKILL B2A (SKILL.md + script + preço + categoria)
     ↓
PUBLICAÇÃO NO KEEPITHUB MARKETPLACE
     ↓
RECEITA RECORRENTE ($KEEPIT ou R$)
```

**Princípio:** Todo erro do ecossistema Jarvis é uma dor que outros agentes também terão. Nós sofremos primeiro — e transformamos em produto.

---

## CRITÉRIOS PARA VIRAR SKILL

Um erro vira skill quando atende ≥ 2 critérios:

| Critério | Descrição |
|----------|-----------|
| **Recorrência** | Pode acontecer de novo neste ou em outros agentes |
| **Generalidade** | A solução serve a outros ecossistemas além do KEEPIT |
| **Valor mensurável** | Evita perda de dado, tempo, dinheiro ou reputação |
| **Automatizável** | A solução pode rodar sem intervenção humana |

---

## TAXONOMIA DE SKILLS B2A

### Categoria 1 — 🛡️ GUARDIAN SKILLS
*Monitoramento e proteção proativa*
- Detectam problemas antes que causem dano
- Modelo: freemium (alerta grátis, correção = pago)
- Exemplos: cron-timeout-guardian, memory-drift-detector

### Categoria 2 — 🔧 REPAIR SKILLS
*Auto-correção de falhas conhecidas*
- Agem quando o erro já ocorreu
- Modelo: pay-per-use ou assinatura
- Exemplos: bootstrap-truncation-fixer, session-channel-corrector

### Categoria 3 — 🧠 LEARNING SKILLS
*Extração de padrões e regras de comportamentos passados*
- Alimentam o modelo interno de cada agente
- Modelo: assinatura mensal
- Exemplos: error-pattern-extractor, rule-crystallizer

### Categoria 4 — 🔐 COMPLIANCE SKILLS
*Garantia de privacidade, destinatário correto, ações seguras*
- Crítico para agentes que lidam com dados sensíveis
- Modelo: licença enterprise
- Exemplos: delivery-destination-guard, whitelist-enforcer

---

## PRECIFICAÇÃO BASE

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 / $0 KEEPIT | Alerta passivo, sem ação |
| Basic | R$9/mês | Monitoramento ativo |
| Pro | R$29/mês | Auto-correção + logs |
| Enterprise | R$99/mês | Multi-agente + SLA + suporte |
| Token | 10-50 $KEEPIT/mês | Acesso via token nativo |

---

## TEMPLATE DE SKILL B2A

```yaml
skill_id: "[categoria]-[nome]-[versao]"
nome: ""
categoria: "guardian | repair | learning | compliance"
versao: "1.0.0"
origem_erro: "ERRO #XXX — [descrição]"
data_criacao: ""
autor: "Jarvis / KEEPITHUB"

problema_resolvido: ""
agentes_alvo: []  # ex: ["jarvis", "neo", "morpheus", "qualquer-agente"]

algoritmo: ""  # descrição do que a skill faz

inputs:
  - nome: ""
    tipo: ""
    descricao: ""

outputs:
  - nome: ""
    tipo: ""
    descricao: ""

precificacao:
  free: ""
  basic: ""
  pro: ""
  token_keepit: ""

metricas_sucesso:
  - ""

dependencias: []
compatibilidade: ["openclaw", "langchain", "autogen", "crewai"]
```

---

## REGISTRO DE SKILLS GERADAS

| ID | Nome | Origem | Status | Preço Base |
|----|------|--------|--------|------------|
| SK-001 | cron-timeout-guardian | ERRO #003 (timeouts cron) | ✅ Publicada | R$29/mês |
| SK-002 | delivery-destination-guard | ERRO #001 e #002 (canal errado) | ✅ Publicada | R$29/mês |
| SK-003 | bootstrap-memory-fixer | ERRO #004 (truncamento MEMORY.md) | 🔄 Em desenvolvimento | R$19/mês |

---

*Pipeline ativo desde 2026-05-29 | KEEPITHUB B2A Marketplace*
