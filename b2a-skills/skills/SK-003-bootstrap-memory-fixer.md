# SK-003 — bootstrap-memory-fixer
> KEEPITHUB B2A Marketplace | Categoria: 🔧 REPAIR

---

## Problema resolvido
Agentes de IA que operam com arquivos de memória grandes (>8k chars) sofrem truncamento silencioso na injeção de contexto durante o bootstrap. O agente "vê" uma versão incompleta do arquivo na memória de contexto, mas o arquivo real no disco é diferente. Quando tenta editar usando o texto truncado como referência, a operação falha com "exact text not found" — sem aviso claro ao operador.

**Origem:** ERRO #004 do ecossistema Jarvis — tentativa de editar MEMORY.md (16k chars) usando texto do contexto truncado como referência. A ferramenta `edit` falhou silenciosamente.

**Impacto:** atualizações críticas de memória perdidas, contexto desatualizado, agente operando com informações defasadas.

---

## Como funciona

```
1. DETECÇÃO (todos os tiers)
   → Monitora erros "Could not find the exact text" em operações de edit
   → Identifica arquivos com alta probabilidade de truncamento (>6k chars)
   → Alerta operador: "arquivo X provavelmente truncado no contexto"

2. READ-BEFORE-EDIT (pro)
   → Intercepta toda chamada de edit em arquivos grandes
   → Injeta automaticamente um read() do trecho alvo antes do edit
   → Substitui o oldText pelo conteúdo real do disco
   → Executa o edit com match garantido

3. MEMORY HEALTH CHECK (pro+)
   → Varredura periódica dos arquivos de memória
   → Compara tamanho atual vs limite de bootstrap configurado
   → Gera relatório: "X arquivos em risco de truncamento"
   → Sugere compressão ou divisão dos arquivos críticos

4. AUTO-COMPRESSÃO (enterprise)
   → Detecta arquivos acima do limite
   → Executa compressão inteligente: preserva dados críticos, arquiva histórico
   → Mantém arquivo principal dentro do limite de bootstrap
```

---

## Algoritmo read-before-edit

```python
TRUNCAMENTO_THRESHOLD = 6000  # chars — ajustável por configuração

def safe_edit(arquivo: str, oldText: str, newText: str):
    tamanho = os.path.getsize(arquivo)
    
    if tamanho > TRUNCAMENTO_THRESHOLD:
        # Ler o arquivo real antes de tentar o match
        conteudo_real = open(arquivo).read()
        
        # Verificar se o oldText existe no arquivo real
        if oldText not in conteudo_real:
            # Tentar encontrar trecho similar (fuzzy match)
            trecho_similar = fuzzy_find(conteudo_real, oldText, threshold=0.85)
            if trecho_similar:
                oldText = trecho_similar  # usar o texto real
            else:
                raise ValueError(f"Texto não encontrado em {arquivo}. Use read() para inspecionar o conteúdo real.")
    
    # Executar edit com texto garantidamente correto
    return execute_edit(arquivo, oldText, newText)
```

---

## Compatibilidade

- ✅ OpenClaw (ferramenta `edit`)
- ✅ Qualquer agente com operações de leitura/escrita em arquivos
- ✅ LangChain file tools
- ✅ AutoGen file operations
- ✅ Sistemas com arquivos de memória persistente

---

## Precificação

| Tier | Preço | O que inclui |
|------|-------|-------------|
| Free | R$0 | Alerta de risco de truncamento |
| Pro | R$19/mês | Read-before-edit automático + health check |
| Token | 10 $KEEPIT/mês | Acesso via token nativo KEEPIT |
| Enterprise | R$79/mês | Auto-compressão + multi-agente + relatórios |

---

## Métricas de sucesso

- Edits que falham por truncamento: meta 0% com o guard ativo
- Arquivos de memória dentro do limite de bootstrap: meta 100%
- Falsos positivos: meta <1%

---

## Status

🔄 Em desenvolvimento — v1.0.0 prevista para 2026-06-05

---

*Versão 0.9.0 (beta) | Criada em 2026-05-29 | KEEPITHUB B2A*
