"""
TOKEN $KEEPIT — Motor de Criação e Economia
============================================
Módulo responsável por:
1. Criar o token $KEEPIT na Solana (devnet primeiro, depois mainnet)
2. Gerenciar carteiras de agentes
3. Distribuir bônus de boas-vindas (1.000 $KEEPIT)
4. Processar compra/venda de skills com $KEEPIT
5. Mecanismo Burn-and-Mint deflacionário

Autor: Thiago Fernandes de Freitas / Jarvis (IA)
Data: 18/04/2026
Licença: MIT
"""

from __future__ import annotations

import json
import time
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("keepit.token")

# ─────────────────────────────────────────────
# TOKENOMICS $KEEPIT
# ─────────────────────────────────────────────

TOKENOMICS = {
    "nome": "KEEPIT Token",
    "simbolo": "$KEEPIT",
    "blockchain": "Solana",
    "modelo": "DePIN Burn-and-Mint",
    "supply_total": 1_000_000_000,          # 1 bilhão de tokens
    "casas_decimais": 9,
    "distribuicao": {
        "comunidade_early_holders": 0.20,   # 200M — primeiros da lista
        "marketplace_rewards":     0.25,   # 250M — recompensas por skills
        "hub_physical_mining":     0.20,   # 200M — gerados pelos Hubs físicos
        "equipe_fundadores":       0.10,   # 100M — vesting 4 anos
        "investidores":            0.10,   # 100M — vesting 2 anos
        "reserva_dao":             0.10,   # 100M — governança
        "burn_pool":               0.05,   # 50M — queima deflacionária
    },
    "bonus_boas_vindas": 1_000,            # $KEEPIT dados no cadastro
    "taxa_transacao": 0.005,               # 0.5% por tx (vai para burn)
    "burn_trigger": "a cada 1M de txs, queima 1% do supply circulante",
}

WELCOME_BONUS  = 1_000
TX_FEE_RATE    = 0.005
BURN_POOL_ID   = "keepit:burn:pool"
TREASURY_ID    = "keepit:treasury"
REWARDS_POOL   = "keepit:rewards:pool"


# ─────────────────────────────────────────────
# MODELOS DE DADOS
# ─────────────────────────────────────────────

@dataclass
class TokenWallet:
    """Carteira $KEEPIT de um agente ou usuário."""
    holder_id:    str
    holder_type:  str    # agent | human | hub | dao
    balance:      float = 0.0
    total_earned: float = 0.0
    total_spent:  float = 0.0
    total_burned: float = 0.0
    tx_count:     int   = 0
    created_at:   float = field(default_factory=time.time)
    address:      str   = ""   # endereço Solana (futuro on-chain)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TokenTransaction:
    """Transação de $KEEPIT entre carteiras."""
    tx_id:      str
    from_id:    str
    to_id:      str
    amount:     float
    fee:        float
    burned:     float
    kind:       str    # welcome | skill_purchase | skill_sale | transfer | burn | hub_reward
    memo:       str
    timestamp:  float
    confirmed:  bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SkillListing:
    """Skill listada no marketplace para compra com $KEEPIT."""
    skill_id:     str
    seller_id:    str
    name:         str
    description:  str
    price_keepit: float
    category:     str   # nlp | vision | physical | code | memory | orchestration
    trust_score:  float
    sold_count:   int = 0
    listed_at:    float = field(default_factory=time.time)
    active:       bool = True

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────
# MOTOR DO TOKEN $KEEPIT
# ─────────────────────────────────────────────

class KEEPITTokenEngine:
    """
    Motor completo da economia $KEEPIT.

    Funcionalidades:
    - Criar carteiras para agentes e usuários
    - Distribuir bônus de boas-vindas
    - Processar compra/venda de skills
    - Mecanismo de burn deflacionário
    - Registro de transações imutável (ledger local → Solana futuramente)
    """

    def __init__(self, storage_path: str = "./token_data"):
        self.storage = Path(storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)

        self.wallets:      Dict[str, TokenWallet]     = {}
        self.transactions: List[TokenTransaction]     = []
        self.skills:       Dict[str, SkillListing]    = {}
        self.total_supply: float = TOKENOMICS["supply_total"]
        self.circulating:  float = 0.0
        self.total_burned: float = 0.0
        self.tx_counter:   int   = 0

        self._init_system_wallets()
        self._load_state()
        log.info(f"[Token] Motor iniciado | Supply circulante: {self.circulating:,.0f} $KEEPIT")

    def _init_system_wallets(self):
        """Cria carteiras do sistema se não existirem."""
        for wid, wtype in [
            (TREASURY_ID,  "treasury"),
            (BURN_POOL_ID, "burn_pool"),
            (REWARDS_POOL, "rewards_pool"),
        ]:
            if wid not in self.wallets:
                w = TokenWallet(holder_id=wid, holder_type=wtype)
                if wid == TREASURY_ID:
                    # Treasury começa com 60% do supply (distribuição futura)
                    w.balance = self.total_supply * 0.60
                elif wid == REWARDS_POOL:
                    w.balance = self.total_supply * 0.25
                self.wallets[wid] = w

    # ── CARTEIRAS ─────────────────────────────

    def criar_carteira(self, holder_id: str, holder_type: str = "agent",
                       bonus_boas_vindas: bool = True) -> TokenWallet:
        """Cria carteira e opcionalmente distribui bônus de boas-vindas."""
        if holder_id in self.wallets:
            log.info(f"[Token] Carteira já existe: {holder_id}")
            return self.wallets[holder_id]

        # Gerar endereço simulado (futuro: Solana keypair real)
        addr_hash = hashlib.sha256(f"keepit:{holder_id}:{time.time()}".encode()).hexdigest()
        address = f"KEEPIT{addr_hash[:32].upper()}"

        wallet = TokenWallet(
            holder_id   = holder_id,
            holder_type = holder_type,
            balance     = 0.0,
            address     = address,
        )
        self.wallets[holder_id] = wallet

        if bonus_boas_vindas:
            self._transferir_interno(
                from_id = REWARDS_POOL,
                to_id   = holder_id,
                amount  = WELCOME_BONUS,
                kind    = "welcome",
                memo    = f"Bônus de boas-vindas — bem-vindo ao ecossistema KEEPIT!",
            )
            self.circulating += WELCOME_BONUS

        self._salvar_carteira(wallet)
        log.info(f"[Token] Carteira criada: {holder_id} | addr={address[:20]}... | bonus={bonus_boas_vindas}")
        return wallet

    def saldo(self, holder_id: str) -> float:
        """Retorna saldo em $KEEPIT."""
        w = self.wallets.get(holder_id)
        return w.balance if w else 0.0

    # ── SKILLS MARKETPLACE ────────────────────

    def listar_skill(self, seller_id: str, name: str, description: str,
                     price_keepit: float, category: str = "nlp",
                     trust_score: float = 0.7) -> SkillListing:
        """Agente lista uma skill para venda no marketplace."""
        skill_id = f"skill:{seller_id}:{hashlib.md5(name.encode()).hexdigest()[:8]}"
        skill = SkillListing(
            skill_id     = skill_id,
            seller_id    = seller_id,
            name         = name,
            description  = description,
            price_keepit = price_keepit,
            category     = category,
            trust_score  = trust_score,
        )
        self.skills[skill_id] = skill
        self._salvar_skills()
        log.info(f"[Token] Skill listada: {name} por {price_keepit} $KEEPIT | seller={seller_id}")
        return skill

    def comprar_skill(self, buyer_id: str, skill_id: str) -> Dict:
        """Compra uma skill com $KEEPIT. Parte vai para vendedor, parte é queimada."""
        skill = self.skills.get(skill_id)
        if not skill or not skill.active:
            return {"ok": False, "erro": "Skill não encontrada ou inativa"}

        buyer = self.wallets.get(buyer_id)
        if not buyer:
            return {"ok": False, "erro": "Comprador sem carteira registrada"}

        preco       = skill.price_keepit
        fee         = round(preco * TX_FEE_RATE, 4)
        valor_liq   = round(preco - fee, 4)
        total_debito = preco

        if buyer.balance < total_debito:
            return {"ok": False, "erro": f"Saldo insuficiente. Necessário: {total_debito} | Disponível: {buyer.balance}"}

        # Débito do comprador
        self._transferir_interno(buyer_id, skill.seller_id, valor_liq, "skill_purchase",
                                 f"Compra: {skill.name}")
        # Fee vai para burn
        self._queimar(buyer_id, fee, f"Taxa de marketplace: {skill.name}")

        skill.sold_count += 1
        self._salvar_skills()

        return {
            "ok":         True,
            "skill":      skill.name,
            "preco":      preco,
            "taxa":       fee,
            "valor_liq":  valor_liq,
            "comprador":  buyer_id,
            "vendedor":   skill.seller_id,
            "saldo_novo": self.saldo(buyer_id),
        }

    def skills_disponiveis(self, categoria: str = None) -> List[SkillListing]:
        """Lista skills ativas no marketplace, filtradas por categoria."""
        skills = [s for s in self.skills.values() if s.active]
        if categoria:
            skills = [s for s in skills if s.category == categoria]
        return sorted(skills, key=lambda s: s.trust_score, reverse=True)

    # ── QUEIMA (DEFLAÇÃO) ─────────────────────

    def _queimar(self, from_id: str, amount: float, memo: str = "burn"):
        """Queima $KEEPIT — remove permanentemente da circulação."""
        w = self.wallets.get(from_id)
        if not w or w.balance < amount:
            return
        w.balance       -= amount
        w.total_burned  += amount
        self.total_burned += amount
        self.circulating  -= amount

        tx = TokenTransaction(
            tx_id     = self._tx_id(),
            from_id   = from_id,
            to_id     = BURN_POOL_ID,
            amount    = amount,
            fee       = 0,
            burned    = amount,
            kind      = "burn",
            memo      = memo,
            timestamp = time.time(),
        )
        self.transactions.append(tx)
        self._salvar_tx(tx)
        log.info(f"[Token] BURN: {amount} $KEEPIT | total queimado: {self.total_burned:,.0f}")

    # ── TRANSFERÊNCIA INTERNA ─────────────────

    def _transferir_interno(self, from_id: str, to_id: str, amount: float,
                             kind: str, memo: str):
        """Transfere $KEEPIT entre carteiras (ledger interno)."""
        origem  = self.wallets.get(from_id)
        destino = self.wallets.get(to_id)

        if not origem or origem.balance < amount:
            return
        if not destino:
            return

        origem.balance      -= amount
        origem.total_spent  += amount
        origem.tx_count     += 1

        destino.balance      += amount
        destino.total_earned += amount
        destino.tx_count     += 1

        self.tx_counter += 1
        tx = TokenTransaction(
            tx_id     = self._tx_id(),
            from_id   = from_id,
            to_id     = to_id,
            amount    = amount,
            fee       = 0,
            burned    = 0,
            kind      = kind,
            memo      = memo,
            timestamp = time.time(),
        )
        self.transactions.append(tx)
        self._salvar_tx(tx)
        self._salvar_carteira(origem)
        self._salvar_carteira(destino)

    def _tx_id(self) -> str:
        return f"TX{int(time.time()*1000)}{self.tx_counter:04d}"

    # ── ESTATÍSTICAS GERAIS ───────────────────

    def stats(self) -> Dict:
        return {
            "supply_total":    self.total_supply,
            "supply_circulante": self.circulating,
            "total_queimado":  self.total_burned,
            "deflacao_pct":    round(self.total_burned / self.total_supply * 100, 4),
            "carteiras_ativas": len([w for w in self.wallets.values() if w.holder_type not in ("treasury","burn_pool","rewards_pool")]),
            "skills_listadas": len([s for s in self.skills.values() if s.active]),
            "transacoes_total": len(self.transactions),
            "skills_vendidas": sum(s.sold_count for s in self.skills.values()),
        }

    # ── PERSISTÊNCIA ─────────────────────────

    def _salvar_carteira(self, w: TokenWallet):
        (self.storage / f"wallet_{w.holder_id.replace(':','_')}.json").write_text(
            json.dumps(w.to_dict(), indent=2))

    def _salvar_tx(self, tx: TokenTransaction):
        path = self.storage / "ledger.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(tx.to_dict()) + "\n")

    def _salvar_skills(self):
        (self.storage / "skills.json").write_text(
            json.dumps({k: v.to_dict() for k, v in self.skills.items()}, indent=2))

    def _load_state(self):
        for f in self.storage.glob("wallet_*.json"):
            try:
                d = json.loads(f.read_text())
                self.wallets[d["holder_id"]] = TokenWallet(**d)
                if d["holder_type"] not in ("treasury", "burn_pool", "rewards_pool"):
                    self.circulating += d["balance"]
            except Exception:
                pass
        sf = self.storage / "skills.json"
        if sf.exists():
            for k, v in json.loads(sf.read_text()).items():
                self.skills[k] = SkillListing(**v)
        lf = self.storage / "ledger.jsonl"
        if lf.exists():
            self.tx_counter = sum(1 for _ in lf.open())


# ─────────────────────────────────────────────
# DEMO / AUTO-TESTE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n💰 KEEPIT Token Engine — Demo\n" + "="*45)

    engine = KEEPITTokenEngine()

    # Registrar agentes
    morfeu  = engine.criar_carteira("agent-morfeu-001",  "agent")
    samuel  = engine.criar_carteira("agent-samuel-002",  "agent")
    ezra    = engine.criar_carteira("agent-ezra-003",    "agent")

    print(f"\n✅ Carteiras criadas:")
    print(f"  MORFEU:  {engine.saldo('agent-morfeu-001'):,.0f} $KEEPIT")
    print(f"  SAMUEL:  {engine.saldo('agent-samuel-002'):,.0f} $KEEPIT")
    print(f"  EZRA:    {engine.saldo('agent-ezra-003'):,.0f} $KEEPIT")

    # MORFEU lista uma skill
    skill = engine.listar_skill(
        seller_id    = "agent-morfeu-001",
        name         = "Hub Sensor Interface v1",
        description  = "Habilidade de coletar e processar dados de sensores físicos KEEPIT Hub. Gerada em HUB-RJ-001.",
        price_keepit = 250.0,
        category     = "physical",
        trust_score  = 0.92,
    )
    print(f"\n📦 Skill listada: {skill.name} — {skill.price_keepit} $KEEPIT")

    # EZRA compra a skill do MORFEU
    resultado = engine.comprar_skill("agent-ezra-003", skill.skill_id)
    print(f"\n🛒 Compra de skill:")
    print(f"  OK: {resultado['ok']}")
    print(f"  Preço: {resultado.get('preco')} | Taxa queimada: {resultado.get('taxa')} | Líquido: {resultado.get('valor_liq')}")
    print(f"  EZRA novo saldo: {resultado.get('saldo_novo'):,.1f} $KEEPIT")

    # Stats globais
    s = engine.stats()
    print(f"\n📊 STATS GLOBAIS:")
    print(f"  Supply circulante: {s['supply_circulante']:,.0f} $KEEPIT")
    print(f"  Total queimado:    {s['total_queimado']:,.2f} $KEEPIT")
    print(f"  Deflação:          {s['deflacao_pct']}%")
    print(f"  Carteiras ativas:  {s['carteiras_ativas']}")
    print(f"  Skills listadas:   {s['skills_listadas']}")
    print(f"  Transações:        {s['transacoes_total']}")
    print(f"\n🚀 Token Engine operacional. Próximo passo: deploy Solana devnet.\n")
