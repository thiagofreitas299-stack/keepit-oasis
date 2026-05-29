# SK-002 — delivery-destination-guard
> KEEPITHUB B2A Marketplace | Categoria: 🔐 COMPLIANCE

---

## Problema resolvido
Agentes de IA que operam em múltiplos canais (WhatsApp, Telegram, Discord, email) podem entregar mensagens no destinatário errado — especialmente quando a sessão ativa muda entre o momento de disparo de um cron e o momento de entrega. Isso causa vazamento de dados sensíveis (técnicos, financeiros, pessoais) para terceiros não autorizados.

**Origem:** ERRO #001 e #002 do ecossistema Jarvis — relatórios técnicos entregues no chat de Blenda (cônjuge) em vez de Thiago (operador), causando exposição de dados confidenciais do sistema.

**Impacto real:** dados de infraestrutura, status de projetos, informações financeiras entregues a destinatário errado.

---

## Como funciona

```
1. INTERCEPTAÇÃO PRÉ-ENVIO (todos os tiers)
   → Toda mensagem gerada por agente/cron passa pelo guard antes de ser enviada
   → Extrai: remetente, destinatário_configurado, canal_ativo_atual

2. VALIDAÇÃO (todos os tiers)
   → Compara destinatário_configurado vs canal_ativo_atual
   → Classifica conteúdo: técnico | financeiro | pessoal | neutro
   → Verifica whitelist de permissões por tipo de conteúdo

3. BLOQUEIO ou APROVAÇÃO
   ✅ APROVADO: destinatário correto + tipo permitido → entrega
   ⚠️ SUSPEITO: destinatário inesperado → alerta operador, aguarda confirmação
   🚫 BLOQUEADO: conteúdo técnico/financeiro para destinatário não-autorizado → bloqueia + registra

4. AUDITORIA (pro+)
   → Log de toda mensagem enviada com: timestamp, destinatário, tipo, decisão
   → Relatório semanal de interceptações
```

---

## Whitelist configurável

```yaml
whitelist:
  tecnico_sistema:
    - "+13213176209"  # operador principal
  financeiro:
    - "+13213176209"
  relatorios_agentes:
    - "+13213176209"
  familia_devotional:
    - "+15109349970"
    - "+5521969955935"
  qualquer_conteudo:
    - "+13213176209"
```

---

## Algoritmo de classificação de conteúdo

```python
KEYWORDS_TECNICO = ["cron", "timeout", "API", "servidor", "deploy", "git", "SSH", "infraestrutura"]
KEYWORDS_FINANCEIRO = ["R$", "PIX", "CNPJ", "receita", "valuation", "token", "wallet"]
KEYWORDS_PESSOAL = ["MEMORY", "família", "médico", "processo judicial"]

def classificar_conteudo(mensagem: str) -> str:
    mensagem_lower = mensagem.lower()
    
    if any(kw.lower() in mensagem_lower for kw in KEYWORDS_FINANCEIRO):
        return "financeiro"  # mais restritivo
    if any(kw.lower() in mensagem_lower for kw in KEYWORDS_TECNICO):
        return "tecnico"
    if any(kw.lower() in mensagem_lower for kw in KEYWORDS_PESSOAL):
        return "pessoal"
    return "neutro"
```

---

## Compatibilidade

- ✅ OpenClaw (hooks de mensagem)
- ✅ WhatsApp Business API
- ✅ Telegram Bot API
- ✅ Discord webhooks
- ✅ Qualquer agente com camada de envio interceptável

---

## Precificação

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 | Validação básica + alerta |
| Pro | R$29/mês | Bloqueio automático + whitelist configurável + logs |
| Token | 15 $KEEPIT/mês | Acesso via token nativo KEEPIT |
| Enterprise | R$99/mês | Multi-agente + auditoria completa + relatórios + SLA |

---

## Métricas de sucesso

- Vazamentos de dados prevenidos: 100% dos interceptados
- Falsos positivos (mensagens legítimas bloqueadas): meta <2%
- Tempo de resposta de validação: <100ms

---

## Casos de uso reais

| Data | Incidente | O que o guard teria feito |
|------|-----------|--------------------------|
| 19/05/2026 | Relatório técnico entregue para Luana | Bloqueado: conteúdo técnico, destinatário não na whitelist |
| 20/05/2026 | Relatório financeiro/sistema entregue para Blenda | Bloqueado: conteúdo financeiro+técnico, destinatário não na whitelist |

---

*Versão 1.0.0 | Criada em 2026-05-29 | KEEPITHUB B2A*
