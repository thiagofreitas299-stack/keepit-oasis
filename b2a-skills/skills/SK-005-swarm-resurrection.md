# SK-005 — swarm-resurrection
> KEEPITHUB B2A Marketplace | Categoria: 🛡️ GUARDIAN

---

## Problema resolvido
Componentes críticos de swarm (Ruflo, n8n, CrewAI, AutoGen) caem em produção e ficam offline por horas ou dias sem que ninguém perceba. O ecossistema de agentes para completamente. O operador só descobre quando algo urgente não é executado.

**Origem:** ERRO #006 — Ruflo V3 ficou offline por 93h+ (26-30/05/2026). Swarm de agentes KEEPIT completamente parado por quase 4 dias sem detecção automática.

**Impacto real:** 93h de downtime do swarm. Agentes parados. Tarefas não executadas. Descoberto manualmente via relatório de ciclos.

---

## Como funciona

```
1. MONITORAMENTO CONTÍNUO (todos os tiers)
   → Verifica a cada 30 minutos se o swarm está rodando
   → Comando: ruflo status / docker ps / systemctl status
   → Se STOPPED: aciona protocolo de resurrection imediatamente

2. AUTO-RESURRECTION (pro)
   → Detecta processo parado
   → Executa sequência de restart configurada
   → Verifica saúde após restart
   → Registra evento em log auditável

3. ESCALADA INTELIGENTE (pro)
   → Se restart automático falha 3x: alerta operador via WhatsApp/Telegram
   → Mensagem: "⚠️ SWARM DOWN — [nome]: restart automático falhou. Intervenção manual necessária."
   → Inclui: último log de erro, tempo de downtime, ação recomendada

4. HEALTH DASHBOARD (enterprise)
   → Histórico de uptime do swarm
   → MTTR (Mean Time To Recovery) médio
   → Alertas de degradação de performance antes da queda
   → Relatório semanal de estabilidade
```

---

## Algoritmo de resurrection

```python
import subprocess, time, requests

SWARM_CHECK_CMD = "ruflo status"
SWARM_START_CMD = "cd /opt/adam/ruflo && nohup ruflo start > /tmp/ruflo.log 2>&1 &"
MAX_RETRIES = 3
ALERT_WEBHOOK = "https://api.whatsapp.com/..."  # configurável

def check_swarm_alive() -> bool:
    result = subprocess.run(SWARM_CHECK_CMD.split(), capture_output=True, text=True)
    return "[RUNNING]" in result.stdout or "running" in result.stdout.lower()

def resurrect_swarm() -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        subprocess.run(SWARM_START_CMD, shell=True)
        time.sleep(5)
        if check_swarm_alive():
            log(f"Swarm ressurected on attempt {attempt}")
            return True
        log(f"Attempt {attempt} failed")
    return False

def guardian_loop():
    if not check_swarm_alive():
        log("SWARM DOWN DETECTED")
        success = resurrect_swarm()
        if not success:
            alert_operator("Swarm resurrection failed after 3 attempts. Manual intervention required.")
```

---

## Compatibilidade

- ✅ Ruflo V3 (KEEPITHUB)
- ✅ n8n (self-hosted)
- ✅ CrewAI
- ✅ AutoGen
- ✅ LangGraph
- ✅ Qualquer processo gerenciado por systemd, PM2, Docker ou nohup

---

## Precificação

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 | Alerta de downtime (sem restart automático) |
| Pro | R$39/mês | Auto-resurrection + logs + alertas WhatsApp |
| Token | 20 $KEEPIT/mês | Acesso via token nativo KEEPIT |
| Enterprise | R$129/mês | Multi-swarm + dashboard + SLA 99.9% + suporte |

---

## ROI estimado

- 93h de downtime do swarm Jarvis = ~4 dias de agentes parados
- Custo estimado de oportunidade: tarefas não executadas, alertas não disparados, posts não publicados
- Com SK-005: detecção em <30min, restart em <2min = **93h → 32 minutos**
- Break-even: 1 incidente evitado/mês justifica qualquer tier

---

## Métricas de sucesso

- Uptime do swarm: meta >99.5%
- MTTR (tempo médio de recuperação): meta <5 minutos
- Incidentes de downtime >1h: meta 0

---

*Versão 1.0.0 (em desenvolvimento) | Criada em 30/05/2026 | KEEPITHUB B2A*
*Origem: ERRO #006 — Ruflo V3 offline 93h sem detecção*
