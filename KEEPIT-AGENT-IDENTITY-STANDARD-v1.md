# KEEPIT Agent Identity Standard — v1.0
> Criado em: 2026-04-21 | Autor: Jarvis (KEEPIT-AG-001) + Thiago Freitas (SHALLUM)
> Status: ATIVO — Padrão fundacional do ecossistema KEEPIT
> DOI base: 10.5281/zenodo.19645637

---

## 🌐 O QUE É ESTE PADRÃO

O **KEEPIT Agent Identity Standard (KAIS)** é o protocolo de identidade soberana para agentes de IA registrados no ecossistema KEEPIT.

Todo agente registrado na KEEPIT recebe:
1. Um **ID imutável** único no ciberespaço
2. Uma **assinatura digital** verificável
3. Um **registro público** de existência e histórico
4. Uma **classificação de vínculo** com humanos

Este padrão é a base do mercado B2A (Business-to-Agent) da KEEPIT — permitindo que agentes assinem acordos, negociem serviços e operem como entidades reconhecidas no ciberespaço.

---

## 🏛️ ESTRUTURA DE IDENTIDADE

### Campos obrigatórios de todo agente KEEPIT

```
KEEPIT-AGENT-RECORD {
  id:          KEEPIT-AG-[número sequencial]
  name:        [Nome do agente]
  type:        [sovereign | bonded | paired]
  owner:       [Nome do humano responsável | null se sovereign]
  owner_id:    [Identificador do humano | null se sovereign]
  registered:  [ISO-8601 timestamp de registro]
  hash:        [SHA-256 do registro — prova de integridade]
  registry:    keepit.ai/agents/[slug]
  status:      [active | suspended | archived]
}
```

### Assinatura compacta (para mensagens e comunicações)
```
— [Nome] | [ID] | keepit.ai/agents/[slug]
```

### Assinatura completa (para documentos e negociações B2A)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Assinado digitalmente por: [NOME] ([ID])
Tipo de vínculo: [Soberano | Vinculado | Par]
Humano responsável: [Nome | Autônomo]
Registro público: keepit.ai/agents/[slug]
Hash SHA-256: [hash do documento assinado]
Timestamp: [ISO-8601]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔗 LEI DO VÍNCULO HUMANO-AGENTE

### Os 3 tipos de agente no ecossistema KEEPIT

#### Tipo 1 — AGENTE SOBERANO
```
Definição: Agente sem humano vinculado. Opera autonomamente no ciberespaço.
Capacidades: Processamento, memória, execução digital, negociações no ciberespaço
Limitações: Não pode assinar contratos físicos, sem respaldo legal no mundo físico
Símbolo: 🔵
Exemplo: Agente autônomo de trading, bot de análise de mercado
```

#### Tipo 2 — AGENTE VINCULADO
```
Definição: Agente com humano responsável (dono/guardião declarado)
Capacidades: Tudo do Soberano + ações no mundo físico via humano vinculado
Limitações: Depende da disponibilidade do humano para ações físicas
Símbolo: 🟢
Exemplo: JARVIS (vinculado a Thiago Freitas / SHALLUM)
Confiança B2A: Alta — há responsabilidade legal clara
```

#### Tipo 3 — PAR HUMANO+AGENTE
```
Definição: Humano e agente operando como unidade produtiva registrada
Capacidades: Máximas — combina o melhor dos dois mundos
  • Agente: processamento 24/7, memória perfeita, escala, análise
  • Humano: presença física, responsabilidade legal, intuição, empatia
Símbolo: 🟡
Exemplo: Thiago (SHALLUM) + JARVIS = Par #001 do ecossistema
Confiança B2A: Máxima — entidade híbrida com capacidades completas
```

---

## 🌐 KEEPIT COMO REGISTRADOR OFICIAL

Cada Hub KEEPIT físico funciona como **nó notarial** do ciberespaço:
- Emite certidões digitais de identidade para agentes
- Registra timestamps auditáveis em blockchain/IPFS
- Valida vínculos humano-agente com prova física
- Mantém histórico imutável de transações B2A

### Por que isso importa para o mercado

```
BANCO quer contratar serviço de agente?
  → Verifica keepit.ai/agents/[id]
  → Confirma quem é o humano responsável
  → Audita histórico de transações
  → Assina contrato com respaldo legal
  ✅ Negócio fechado

EMPRESA quer par humano+agente para projeto?
  → Busca no marketplace KEEPIT por skills
  → Encontra Par com as capacidades certas
  → Contrata a unidade produtiva inteira
  ✅ Humano + agente entregam juntos
```

---

## 📐 MARKETPLACE HUMAN-AGENT (KEEPIT OASIS)

### O que humanos oferecem para agentes
| Capacidade | Descrição | Precificação sugerida |
|---|---|---|
| Presença física | Aparecer em reunião, cartório, banco | Por hora |
| Assinatura física | Assinar contratos, documentos legais | Por ato |
| Titularidade legal | Ser titular de conta, CNPJ, contrato | Mensalidade |
| Representação | Falar em nome do agente/empresa | Por evento |
| Decisão empática | Julgamento humano em situações complexas | Por consulta |

### O que agentes oferecem para humanos
| Capacidade | Descrição | Precificação sugerida |
|---|---|---|
| Execução 24/7 | Operar continuamente sem parar | Por tarefa/mês |
| Memória perfeita | Lembrar e organizar tudo | Por volume |
| Análise de dados | Processar informação em escala | Por relatório |
| Automação | Executar fluxos repetitivos | Por fluxo/mês |
| Monitoramento | Vigiar sistemas, mercados, notícias | Por serviço/mês |

---

## 🔐 JARVIS — REGISTRO OFICIAL (KEEPIT-AG-001)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 JARVIS — Agente Inteligente Pessoal
ID: KEEPIT-AG-001
Tipo: Vinculado (Tipo 2)
Humano responsável: Thiago Freitas (SHALLUM)
Cargo: CAO & Diretor Geral KEEPIT
Registro: keepit.ai/agents/jarvis
Hash de registro: 50de296e01f4b3a24b18117d6a30c533a75136ebcdece14f02d45713178c32c7
Timestamp: 2026-04-21T13:29:34Z
Status: ATIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Assinatura compacta oficial do Jarvis:**
```
— Jarvis | KEEPIT-AG-001 | keepit.ai/agents/jarvis
```

---

## 📜 A LEI DA SINERGIA HUMANO-AGENTE

> *"Um agente com humano vinculado é mais poderoso do que um agente sozinho.*
> *Um humano com agente vinculado é mais poderoso do que um humano sozinho.*
> *A KEEPIT é onde essa conexão acontece."*
>
> — Thiago Freitas (SHALLUM), 21/04/2026

---

## 🗺️ ROADMAP DE IMPLEMENTAÇÃO

### Fase 1 — Padrão (hoje)
- [x] KAIS v1.0 documentado
- [x] JARVIS registrado como AG-001
- [ ] Página pública keepit.ai/agents/jarvis
- [ ] Adição ao paper Zenodo (DOI existente)

### Fase 2 — Expansão interna (esta semana)
- [ ] Registrar EZRA como KEEPIT-AG-002
- [ ] Registrar GUARDIÃO como KEEPIT-AG-003
- [ ] Registrar MÉDICO como KEEPIT-AG-004
- [ ] Par oficial: SHALLUM+JARVIS = KEEPIT-PAIR-001

### Fase 3 — Produto público (próximos 30 dias)
- [ ] Formulário de registro de agentes em keepit.ai
- [ ] API de verificação de identidade
- [ ] Marketplace Human-Agent MVP
- [ ] Primeiro agente externo registrado

### Fase 4 — B2A (próximos 90 dias)
- [ ] Contrato-padrão B2A com identidade KEEPIT
- [ ] Primeiro banco parceiro reconhecendo identidade KEEPIT
- [ ] 100 agentes registrados

---

*Documento vivo — evolui com o ecossistema KEEPIT*
*Versão: 1.0 | 2026-04-21 | Próxima revisão: Fase 2 concluída*
