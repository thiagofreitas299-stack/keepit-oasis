# SK-004 — api-token-guardian
> KEEPITHUB B2A Marketplace | Categoria: 🛡️ GUARDIAN

---

## Problema resolvido
Agentes de IA dependem de tokens de API (Instagram, OpenAI, Stripe, WhatsApp, etc.) para operar. Tokens expiram silenciosamente — o agente tenta executar uma ação, falha com `OAuthException` ou `401 Unauthorized`, e a tarefa é perdida. O operador só descobre depois do dano.

**Origem:** ERRO #005 do ecossistema Jarvis — token do Instagram expirou em 29/05/2026 às 10:28 PDT, bloqueando publicação de 3 posts prontos. Detectado só na hora de publicar.

**Impacto real:** 3 posts do @jarvisfreitas01 não publicados, subagente desperdiçado, operação bloqueada.

---

## Como funciona

```
1. INVENTÁRIO (todos os tiers)
   → Escaneia arquivos de secrets/config do agente
   → Mapeia todos os tokens encontrados (Instagram, OpenAI, Stripe, etc.)
   → Classifica por tipo, data de expiração e criticidade

2. VERIFICAÇÃO DIÁRIA (todos os tiers)
   → Faz chamada de teste em cada token (endpoint de validação)
   → Classifica status: ok | expiring_soon | expired
   → Registra em token-health.json com timestamp

3. ALERTA ANTECIPADO (free)
   → Se token expira em menos de 7 dias: alerta o operador
   → Mensagem: "⚠️ TOKEN EXPIRANDO — [serviço] expira em X dias. Renovar: [link]"
   → Zero falso positivos (só alerta quando confirmado via API)

4. AUTO-RENOVAÇÃO (pro)
   → Para tokens que suportam refresh (Meta Long-Lived Token, OAuth 2.0 refresh_token)
   → Renova automaticamente antes de expirar
   → Registra novo token no secrets file
   → Confirma renovação ao operador

5. RELATÓRIO DE SAÚDE (pro+)
   → Dashboard de todos os tokens do ecossistema
   → Histórico de renovações
   → Alertas de tokens próximos do expirar agrupados em 1 mensagem diária
```

---

## Tokens suportados

| Serviço | Tipo | Auto-renovação |
|---------|------|---------------|
| Instagram / Meta Graph API | Long-Lived Token | ✅ via /refresh_access_token |
| OpenAI | API Key (não expira) | N/A — monitora validade |
| Stripe | Restricted Key | ⚠️ alerta apenas |
| WhatsApp Business | Token | ✅ via Meta refresh |
| HuggingFace | Token | N/A |
| Custom OAuth 2.0 | refresh_token | ✅ via /token endpoint |

---

## Algoritmo de verificação

```python
import requests
import json
from datetime import datetime, timedelta

ALERT_THRESHOLD_DAYS = 7

def verificar_token_instagram(token: str) -> dict:
    """Verifica token Instagram e retorna status + dias restantes"""
    r = requests.get(
        "https://graph.instagram.com/v21.0/me",
        params={"fields": "id,username", "access_token": token}
    )
    
    if r.status_code != 200 or "error" in r.json():
        return {"status": "expired", "days_remaining": 0}
    
    # Verificar data de expiração via debug endpoint
    debug = requests.get(
        "https://graph.facebook.com/debug_token",
        params={"input_token": token, "access_token": token}
    ).json()
    
    exp_ts = debug.get("data", {}).get("expires_at", 0)
    if exp_ts == 0:
        return {"status": "ok", "days_remaining": 999}  # não expira
    
    days_remaining = (datetime.fromtimestamp(exp_ts) - datetime.now()).days
    
    if days_remaining <= 0:
        return {"status": "expired", "days_remaining": 0}
    elif days_remaining <= ALERT_THRESHOLD_DAYS:
        return {"status": "expiring_soon", "days_remaining": days_remaining}
    else:
        return {"status": "ok", "days_remaining": days_remaining}

def renovar_token_instagram(token: str) -> str:
    """Renova Long-Lived Token do Instagram"""
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": token
        }
    )
    return r.json().get("access_token", token)
```

---

## Compatibilidade

- ✅ OpenClaw (cron diário nativo)
- ✅ Qualquer agente com acesso a filesystem e HTTP
- ✅ n8n / Make / Zapier (webhook trigger)
- ✅ LangChain / AutoGen / CrewAI
- ✅ Ambientes com secrets em .env ou JSON

---

## Precificação

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 | Alerta de expiração (7 dias antes) |
| Pro | R$19/mês | Auto-renovação OAuth + relatório diário |
| Token | 10 $KEEPIT/mês | Acesso via token nativo KEEPIT |
| Enterprise | R$69/mês | Multi-agente + dashboard + auditoria completa |

---

## ROI estimado

- 1 post não publicado por token expirado = ~2h de trabalho perdido + oportunidade de engajamento
- Com auto-renovação: R$0 de perda, 100% de uptime dos tokens
- Break-even: 1 incidente evitado por mês justifica o Pro

---

## Métricas de sucesso

- Tokens expirados em produção: meta 0%
- Alertas com ≥7 dias de antecedência: meta 100%
- Auto-renovações bem-sucedidas: meta >99%

---

## Status

✅ Cron ativo no ecossistema Jarvis — rodando todo dia às 08:00 BRT
Cron ID: `9f5c2b74-fa2a-41c7-b0ad-bbcda30433c6`

---

*Versão 1.0.0 | Criada em 2026-05-29 | KEEPITHUB B2A*
*Origem: ERRO #005 — token Instagram expirado bloqueou publicação de 3 posts*
