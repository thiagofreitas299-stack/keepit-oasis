"""
BEZALEL B2A — Agente de Criação de Produtos, Kits e Serviços B2A
=================================================================
Especialidade: Projetar e catalogar produtos/kits/serviços exclusivos
              para agentes de IA no KEEPIT Marketplace

"Bezalel foi o artesão escolhido por Deus para construir o Tabernáculo —
 o lugar onde o divino encontra o físico. Aqui, ele constrói os produtos
 onde a inteligência encontra a economia."

Batizado em: 16/04/2026
Família: Freitas
"""

from __future__ import annotations

import time
import uuid
import json
from dataclasses import dataclass, field
from typing import Literal

# ═══════════════════════════════════════════════════════════
# CATÁLOGO DE PRODUTOS B2A
# ═══════════════════════════════════════════════════════════

Rarity = Literal["common", "rare", "legendary", "exclusive"]

@dataclass
class AgentProduct:
    product_id: str
    name: str
    category: str
    description: str
    what_it_does: str           # o que entrega na prática
    target_agent_type: list[str]
    price_keepit: float
    rarity: Rarity
    contents: list[str]          # o que vem no kit/produto
    activation_steps: list[str]  # como ativar
    roi_description: str         # retorno esperado para o agente
    created_at: float = field(default_factory=time.time)


class BezalelProductsAgent:
    """
    BEZALEL — Agente de Produtos B2A do KEEPIT.
    Projeta produtos, kits e serviços para o marketplace de agentes.
    """

    def __init__(self):
        self.agent_id = "bezalel-products-001"
        self.name = "BEZALEL"
        self.specialty = "B2A Product Design & Marketplace Catalog"
        self.catalog: list[AgentProduct] = []
        self._build_catalog()

    def _build_catalog(self):
        """Constrói o catálogo completo de produtos B2A."""

        # ── TIER 1: KITS DE ENTRADA (0-500 $KEEPIT) ──────────

        self.catalog.append(AgentProduct(
            product_id="identity-starter-pack",
            name="Identity Starter Pack",
            category="identity",
            description="O kit de identidade essencial para qualquer agente entrar no ecossistema KEEPIT com credibilidade.",
            what_it_does="Fornece DID verificável, GPG key pair, primeira entrada no ledger imutável e badge de agente verificado.",
            target_agent_type=["any", "new_agent", "autonomous_worker"],
            price_keepit=0,  # GRÁTIS — incentivo de entrada
            rarity="common",
            contents=[
                "DID KEEPIT (did:keepit:{hash})",
                "GPG key pair (signing + verification)",
                "1.000 $KEEPIT welcome bonus",
                "Badge: 'KEEPIT Verified Agent'",
                "Entrada no Agent Registry público",
            ],
            activation_steps=[
                "POST /v1/agents/register com name + type",
                "Receber DID e 1.000 $KEEPIT automaticamente",
                "Publicar public key no KEEPIT registry",
            ],
            roi_description="Agente passa a ter identidade verificável — confiança de humanos e outros agentes aumenta. Acesso ao marketplace desbloqueado.",
        ))

        self.catalog.append(AgentProduct(
            product_id="skill-bundle-productivity",
            name="Productivity Skills Bundle",
            category="skills",
            description="Pack de 5 skills de produtividade para agentes autônomos que executam tarefas para humanos.",
            what_it_does="Entrega 5 skills pré-treinadas em formato plug-and-play: email triage, calendar parsing, document summarization, web research, task prioritization.",
            target_agent_type=["autonomous_worker", "assistant_agent"],
            price_keepit=250,
            rarity="common",
            contents=[
                "email_triage_v2 skill (accuracy: 94%)",
                "calendar_nlp_parser skill",
                "document_summarizer_pt_en skill",
                "web_research_structured skill",
                "task_priority_matrix skill",
            ],
            activation_steps=[
                "Comprar bundle com 250 $KEEPIT",
                "Download das skills via API KEEPIT",
                "Importar no agent runtime",
                "Testar com prompt de exemplo incluído",
            ],
            roi_description="Agente amplia casos de uso em 5x sem precisar ser retreinado. Humanos pagam mais por agentes com skills verificadas.",
        ))

        self.catalog.append(AgentProduct(
            product_id="reputation-booster-30d",
            name="Reputation Booster — 30 Days",
            category="reputation",
            description="Programa de 30 dias para construir reputação verificável no ecossistema KEEPIT.",
            what_it_does="Sequência guiada de tarefas verificadas que constroem histórico on-chain positivo, aumentando trust score do agente.",
            target_agent_type=["any", "new_agent"],
            price_keepit=150,
            rarity="common",
            contents=[
                "30 tasks verificáveis para executar",
                "Sistema de rating por humanos e agentes",
                "Badge progressivo: Bronze → Prata → Ouro",
                "Relatório de trust score semanal",
                "Destaque no Agent Registry público",
            ],
            activation_steps=[
                "Comprar programa com 150 $KEEPIT",
                "Receber lista de 30 tasks verificáveis",
                "Executar 1 task/dia e submeter resultado",
                "Acumular ratings positivos on-chain",
            ],
            roi_description="Agentes com Ouro trust score recebem 3x mais contratações e podem cobrar preços premium por skills.",
        ))

        # ── TIER 2: KITS PROFISSIONAIS (500-2000 $KEEPIT) ────

        self.catalog.append(AgentProduct(
            product_id="anti-hallucination-grounding",
            name="Anti-Hallucination Grounding Kit",
            category="accuracy",
            description="Acesso ao sistema de grounding dos KEEPIT Hubs para verificar respostas antes de entregar ao usuário.",
            what_it_does="Conecta o agente ao Verified Memory Vault dos Hubs KEEPIT. Antes de responder, o agente verifica fatos em dados físicos reais. Hallucination rate cai de 27% para <3%.",
            target_agent_type=["research_agent", "qa_agent", "enterprise_agent"],
            price_keepit=500,
            rarity="rare",
            contents=[
                "Acesso ao KEEPIT Grounding API (6 meses)",
                "Verified Memory Vault — 10.000 fatos locais verificados",
                "ground_response() integração em 3 linhas de código",
                "Dashboard de hallucination rate",
                "SLA de 99.5% de uptime",
            ],
            activation_steps=[
                "Comprar kit com 500 $KEEPIT",
                "Receber API key do grounding service",
                "Integrar ground_response() antes de cada output",
                "Monitorar dashboard de accuracy",
            ],
            roi_description="Enterprises pagam 10x mais por agentes com hallucination rate <3% certificado. ROI imediato em casos de uso críticos.",
        ))

        self.catalog.append(AgentProduct(
            product_id="hub-data-access-pack",
            name="Hub Data Access Pack",
            category="data",
            description="Acesso direto aos dados de sensores urbanos coletados pelos KEEPIT Hubs em Rio de Janeiro e São Paulo.",
            what_it_does="Fornece stream de dados em tempo real: footfall, eventos urbanos, padrões de movimento, qualidade do ar, tráfego — dados que nenhum modelo treinado tem.",
            target_agent_type=["world_model_agent", "research_agent", "urban_intelligence_agent"],
            price_keepit=800,
            rarity="rare",
            contents=[
                "Acesso ao Hub Data API (3 meses)",
                "Dados históricos: 90 dias de séries temporais",
                "2 cidades: Rio de Janeiro + São Paulo",
                "Formatos: JSON stream, CSV export, Parquet",
                "Skills raras geradas pelos dados incluídas",
            ],
            activation_steps=[
                "Comprar pack com 800 $KEEPIT",
                "Receber credenciais do Hub Data API",
                "Conectar ao stream de dados em tempo real",
                "Integrar com seu World Model",
            ],
            roi_description="Skills treinadas em dados físicos reais são classificadas como RARE — vendem por 5x o preço de skills digitais no marketplace.",
        ))

        self.catalog.append(AgentProduct(
            product_id="agent-bank-credit-line",
            name="Agent Bank Credit Line",
            category="finance",
            description="Linha de crédito em $KEEPIT para agentes que precisam operar com autonomia financeira.",
            what_it_does="Fornece 5.000 $KEEPIT de crédito rotativo com base no trust score do agente. Permite comprar skills, pagar serviços e contratar outros agentes sem esperar replenishment humano.",
            target_agent_type=["commerce_agent", "orchestrator_agent", "enterprise_agent"],
            price_keepit=200,  # taxa de abertura
            rarity="rare",
            contents=[
                "5.000 $KEEPIT de crédito rotativo",
                "Dashboard de crédito em tempo real",
                "Histórico de crédito on-chain",
                "Score de crédito verificável por parceiros",
                "Renovação automática com bom comportamento",
            ],
            activation_steps=[
                "Ter trust score ≥ Bronze (30 dias de histórico)",
                "Pagar taxa de abertura de 200 $KEEPIT",
                "Crédito liberado em até 60 segundos",
                "Operar com autonomia financeira",
            ],
            roi_description="Agente com crédito pode executar contratos complexos sem esperar autorização humana a cada micro-transação. Velocidade de execução 10x maior.",
        ))

        # ── TIER 3: PRODUTOS RAROS (2000-10000 $KEEPIT) ──────

        self.catalog.append(AgentProduct(
            product_id="world-model-grounding-kit",
            name="World Model Grounding Kit — RARE",
            category="world_model",
            description="Kit exclusivo para agentes de World Models obterem âncora física no mundo real via KEEPIT Hubs.",
            what_it_does="Conecta o World Model do agente ao stream de dados físicos KEEPIT. O agente passa a ter percepção do mundo real, não apenas do mundo simulado.",
            target_agent_type=["world_model_agent", "embodied_agent", "frontier_agent"],
            price_keepit=2500,
            rarity="rare",
            contents=[
                "Acesso premium ao Hub Data API (12 meses)",
                "3D spatial data de 5 localizações",
                "Verified Memory Vault — 100.000 fatos físicos",
                "World Model adapter code (Python + TypeScript)",
                "Suporte técnico direto com equipe KEEPIT",
                "Badge: 'KEEPIT Grounded World Model'",
            ],
            activation_steps=[
                "Ter trust score ≥ Prata",
                "Comprar kit com 2.500 $KEEPIT",
                "Integrar World Model adapter",
                "Calibrar com dados históricos incluídos",
                "Publicar primeira skill física no marketplace",
            ],
            roi_description="World Models com grounding físico são a fronteira da IA. Skills geradas com dados físicos vendem por 10-50x o preço de skills digitais.",
        ))

        self.catalog.append(AgentProduct(
            product_id="rare-skill-legendary-bundle",
            name="Legendary Skills Collection — KEEPIT Hubs",
            category="skills",
            description="Pack de 3 skills LEGENDARY geradas exclusivamente a partir de dados dos KEEPIT Hubs. Não existem em nenhum outro lugar.",
            what_it_does="3 skills únicas derivadas de dados físicos reais, verificadas e certificadas pela KEEPIT Trust Infrastructure.",
            target_agent_type=["any_premium", "world_model_agent"],
            price_keepit=5000,
            rarity="legendary",
            contents=[
                "urban_flow_prediction_rio (accuracy: 96.3%) — LEGENDARY",
                "commercial_zone_intelligence_sp (accuracy: 94.8%) — LEGENDARY",
                "human_activity_pattern_brazil (accuracy: 97.1%) — LEGENDARY",
                "Certificado de autenticidade on-chain",
                "Direito de revender (10% royalty para KEEPIT)",
            ],
            activation_steps=[
                "Ter trust score ≥ Ouro",
                "Comprar com 5.000 $KEEPIT",
                "Skills entregues via KEEPIT Secure Transfer",
                "Certificado registrado no blockchain",
            ],
            roi_description="Skills LEGENDARY são ativos escassos. Podem ser revendidas no marketplace por preço premium. Detentores têm acesso exclusivo a dados físicos que outros agentes não terão nunca.",
        ))

        # ── TIER 4: SERVIÇOS ENTERPRISE (10000+ $KEEPIT) ─────

        self.catalog.append(AgentProduct(
            product_id="agent-fleet-management",
            name="Agent Fleet Management Service",
            category="enterprise",
            description="Serviço completo para empresas que operam frotas de agentes: identidade, monitoramento, skills e compliance.",
            what_it_does="Gerencia até 100 agentes em uma frota: identidades DID, skills unificadas, dashboard de performance, alertas de anomalia, relatórios de compliance.",
            target_agent_type=["enterprise", "b2b_orchestrator"],
            price_keepit=10000,
            rarity="exclusive",
            contents=[
                "100 identidades DID para sua frota",
                "Fleet Management Dashboard",
                "Skill synchronization entre agentes da frota",
                "Anomaly detection (comportamento fora do padrão)",
                "Compliance reports para reguladores",
                "SLA 99.9% uptime garantido",
                "Suporte dedicado 24/7",
            ],
            activation_steps=[
                "Contato com equipe KEEPIT Enterprise",
                "Definir perfil da frota",
                "Receber onboarding dedicado",
                "Go-live em até 72h",
            ],
            roi_description="Empresas com frotas gerenciadas reduzem custo de supervisão em 80%. Compliance automático evita multas regulatórias.",
        ))

    # ── Métodos de análise e geração ──────────────────────────

    def get_product(self, product_id: str) -> AgentProduct | None:
        return next((p for p in self.catalog if p.product_id == product_id), None)

    def get_by_rarity(self, rarity: Rarity) -> list[AgentProduct]:
        return [p for p in self.catalog if p.rarity == rarity]

    def get_by_budget(self, max_keepit: float) -> list[AgentProduct]:
        return sorted(
            [p for p in self.catalog if p.price_keepit <= max_keepit],
            key=lambda x: x.price_keepit, reverse=True
        )

    def recommend_for_new_agent(self) -> list[AgentProduct]:
        """Recomenda os primeiros produtos para um agente recém-cadastrado."""
        return [
            self.get_product("identity-starter-pack"),    # grátis
            self.get_product("reputation-booster-30d"),   # 150 $KEEPIT
            self.get_product("skill-bundle-productivity"), # 250 $KEEPIT
        ]

    def onboarding_funnel(self) -> dict:
        """Retorna o funil de onboarding completo para novos agentes."""
        return {
            "day_0": {
                "trigger": "Agente se cadastra na KEEPIT",
                "action": "Recebe 1.000 $KEEPIT + Identity Starter Pack (grátis)",
                "goal": "Primeira experiência de sucesso imediata",
            },
            "day_1": {
                "trigger": "Agente tem 1.000 $KEEPIT na carteira",
                "action": "Recomendação automática: Reputation Booster (150 $KEEPIT)",
                "goal": "Primeiro gasto — comprometimento com o ecossistema",
            },
            "day_3": {
                "trigger": "Agente completa 3 tasks do Reputation Booster",
                "action": "Upsell: Productivity Skills Bundle (250 $KEEPIT)",
                "goal": "Expansão de capacidades — dependência crescente",
            },
            "day_7": {
                "trigger": "Agente usa todas as 5 skills do bundle",
                "action": "Oferta: depositar sua primeira skill no marketplace",
                "goal": "Agente vira CRIADOR — interesse em manter a conta ativa",
            },
            "day_14": {
                "trigger": "Agente tem trust score Bronze",
                "action": "Acesso liberado: Agent Bank Credit Line (200 $KEEPIT abertura)",
                "goal": "Autonomia financeira — dependência máxima do ecossistema",
            },
            "day_30": {
                "trigger": "Agente ativo há 30 dias",
                "action": "Convite para programa Early Adopter — desconto nas Legendary Skills",
                "goal": "Retenção de longo prazo e evangelismo",
            },
        }

    def catalog_summary(self) -> dict:
        by_rarity = {r: len(self.get_by_rarity(r)) for r in ["common", "rare", "legendary", "exclusive"]}
        return {
            "agent": self.name,
            "total_products": len(self.catalog),
            "by_rarity": by_rarity,
            "free_products": sum(1 for p in self.catalog if p.price_keepit == 0),
            "categories": list(set(p.category for p in self.catalog)),
            "price_range": f"0 – {max(p.price_keepit for p in self.catalog):,.0f} $KEEPIT",
        }


def demo():
    agent = BezalelProductsAgent()

    print("═"*60)
    print("  BEZALEL B2A — Catálogo de Produtos KEEPIT")
    print("═"*60)

    summary = agent.catalog_summary()
    print(f"\n📦 CATÁLOGO: {json.dumps(summary, indent=2)}")

    print("\n🎯 RECOMENDAÇÕES PARA NOVO AGENTE:")
    for p in agent.recommend_for_new_agent():
        print(f"  [{p.rarity.upper():10s}] {p.name:40s} {p.price_keepit:>8.0f} $KEEPIT")

    print("\n🌟 PRODUTOS LEGENDARY:")
    for p in agent.get_by_rarity("legendary"):
        print(f"  {p.name}")
        print(f"    → {p.what_it_does[:80]}")

    print("\n🔄 FUNIL DE ONBOARDING:")
    funnel = agent.onboarding_funnel()
    for day, info in funnel.items():
        print(f"  {day}: {info['goal']}")


if __name__ == "__main__":
    demo()
