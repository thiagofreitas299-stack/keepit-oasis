# SK-001 — cron-timeout-guardian
> KEEPITHUB B2A Marketplace | Categoria: 🛡️ GUARDIAN

---

## Problema resolvido
Agentes de IA usam crons para tarefas periódicas (relatórios, monitores, estudos). Quando o timeout é muito baixo, a tarefa termina antes de concluir, gerando falhas silenciosas — o agente não sabe que falhou, não corrige, e a tarefa nunca é entregue. O humano percebe tarde ou nunca.

**Origem:** ERRO #003 do ecossistema Jarvis — múltiplos agentes (Treinamento, Estudo Técnico, Revisor Compliance) falharam por timeout configurado abaixo do tempo real de execução.

---

## Como funciona

```
1. MONITORAMENTO (free)
   → Intercepta eventos de conclusão de cron
   → Se job terminou por timeout: registra como falha
   → Alerta o operador com: job_id, timeout_atual, tempo_estimado_real

2. AUTO-CORREÇÃO (pro)
   → Analisa histórico de execuções do job
   → Calcula timeout_ideal = média(tempo_real) × 1.5 + buffer_segurança
   → Aplica novo timeout automaticamente via API do scheduler
   → Registra alteração em log auditável

3. APRENDIZAGEM CONTÍNUA (pro)
   → A cada execução bem-sucedida, recalibra o timeout ideal
   → Jobs com alta variância recebem buffer maior
   → Relatório mensal de jobs otimizados
```

---

## Algoritmo central

```python
def calcular_timeout_ideal(historico_execucoes: list[float]) -> int:
    if len(historico_execucoes) < 3:
        return max(historico_execucoes) * 2  # conservador sem dados
    
    media = sum(historico_execucoes) / len(historico_execucoes)
    desvio = stdev(historico_execucoes)
    
    # P95 + 20% buffer de segurança
    timeout_ideal = (media + 2 * desvio) * 1.2
    
    return int(timeout_ideal)
```

---

## Compatibilidade

- ✅ OpenClaw (cron nativo)
- ✅ n8n
- ✅ Make / Integromat
- ✅ LangChain agents
- ✅ CrewAI
- ✅ AutoGen
- ✅ Qualquer sistema com scheduler configurável via API

---

## Precificação

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 | Alerta de timeout passivo (apenas notifica) |
| Pro | R$29/mês | Auto-correção + recalibração contínua + logs |
| Token | 15 $KEEPIT/mês | Acesso via token nativo KEEPIT |
| Enterprise | R$99/mês | Multi-agente + dashboard + SLA 99.9% |

---

## Métricas de sucesso

- Taxa de jobs que completam sem timeout: meta >95%
- Redução de alertas manuais de timeout: meta >80%
- Tempo médio para auto-correção após detecção: <5 min

---

## Casos de uso reais (nascidos no ecossistema Jarvis)

| Agente | Timeout original | Timeout corrigido | Resultado |
|--------|-----------------|-------------------|-----------|
| Treinamento Diário KEEPITHUB | 660s | 1200s | ✅ Concluindo normalmente |
| Estudo Técnico Diário | 120s | 240s | ✅ Concluindo normalmente |
| Revisor Compliance | timeout padrão | 600s | ✅ Concluindo normalmente |
| Sistema de Promoção | 300s | 420s | ✅ Concluindo normalmente |

---

*Versão 1.0.0 | Criada em 2026-05-29 | KEEPITHUB B2A*
