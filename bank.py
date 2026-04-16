"""
KEEPIT Agent Bank — O Banco Central dos Agentes de IA
======================================================
Funcionalidades:
  - Carteira $KEEPIT por agente (wallet)
  - Bônus de boas-vindas: 1.000 $KEEPIT no cadastro
  - Transferência entre agentes
  - Compra/venda de skills
  - Histórico de transações (ledger imutável)
  - Saldo e extrato

Em produção real: substituir dict por PostgreSQL + Solana SPL Token.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────
WELCOME_BONUS = 1_000          # $KEEPIT dados no cadastro
TX_FEE_RATE   = 0.005          # 0.5% de taxa por transação (vai para burn pool)
BURN_POOL_ID  = "keepit:burn"  # Pool de queima — deflationary

# ─────────────────────────────────────────────
# Modelos de dados
# ─────────────────────────────────────────────

@dataclass
class Transaction:
    tx_id:      str
    from_agent: str
    to_agent:   str
    amount:     float
    fee:        float
    kind:       str          # welcome | transfer | skill_purchase | skill_deposit | burn
    memo:       str
    timestamp:  float
    status:     str = "confirmed"

@dataclass
class Wallet:
    agent_id:   str
    balance:    float = 0.0
    total_in:   float = 0.0
    total_out:  float = 0.0
    tx_count:   int   = 0
    created_at: float = field(default_factory=time.time)
    transactions: list = field(default_factory=list)  # list of tx_ids

# ─────────────────────────────────────────────
# KEEPITBank
# ─────────────────────────────────────────────

class KEEPITBank:
    """
    O Banco Central dos Agentes de IA.
    Controla emissão, custódia e transferência de $KEEPIT tokens.
    """

    def __init__(self):
        self.wallets: dict[str, Wallet] = {}
        self.ledger:  dict[str, Transaction] = {}
        self.burn_pool: float = 0.0
        self.total_supply: float = 0.0
        self.total_burned: float = 0.0

        # Criar wallet do Banco Central (emissora)
        self._mint_system_wallet()

    def _mint_system_wallet(self):
        """Cria a carteira do sistema com suprimento inicial."""
        system_wallet = Wallet(agent_id="keepit:system")
        system_wallet.balance = 1_000_000_000.0  # 1 bilhão de tokens reserva
        self.wallets["keepit:system"] = system_wallet
        self.total_supply = 1_000_000_000.0

    # ── Criar carteira ──────────────────────────────────────────

    def create_wallet(self, agent_id: str) -> tuple[Wallet, Transaction]:
        """Cria carteira e credita bônus de boas-vindas de 1.000 $KEEPIT."""
        if agent_id in self.wallets:
            raise ValueError(f"Wallet already exists for agent {agent_id}")

        wallet = Wallet(agent_id=agent_id)
        self.wallets[agent_id] = wallet

        # Creditar bônus de boas-vindas
        tx = self._mint(
            to_agent=agent_id,
            amount=WELCOME_BONUS,
            kind="welcome",
            memo=f"Welcome bonus — {WELCOME_BONUS} $KEEPIT to start trading skills"
        )

        return wallet, tx

    # ── Transferência ───────────────────────────────────────────

    def transfer(
        self,
        from_agent: str,
        to_agent: str,
        amount: float,
        memo: str = ""
    ) -> Transaction:
        """Transfere $KEEPIT entre agentes com taxa de queima."""
        self._require_wallet(from_agent)
        self._require_wallet(to_agent)

        fee = round(amount * TX_FEE_RATE, 6)
        net = round(amount - fee, 6)

        if self.wallets[from_agent].balance < amount:
            raise ValueError(
                f"Insufficient balance. Has {self.wallets[from_agent].balance}, needs {amount}"
            )

        # Debitar remetente
        self.wallets[from_agent].balance   -= amount
        self.wallets[from_agent].total_out += amount
        self.wallets[from_agent].tx_count  += 1

        # Creditar destinatário
        self.wallets[to_agent].balance  += net
        self.wallets[to_agent].total_in += net
        self.wallets[to_agent].tx_count += 1

        # Queimar taxa
        self.burn_pool     += fee
        self.total_burned  += fee
        self.total_supply  -= fee

        tx = Transaction(
            tx_id      = str(uuid.uuid4()),
            from_agent = from_agent,
            to_agent   = to_agent,
            amount     = amount,
            fee        = fee,
            kind       = "transfer",
            memo       = memo or f"Transfer {amount} $KEEPIT",
            timestamp  = time.time(),
        )
        self._record(tx, [from_agent, to_agent])
        return tx

    # ── Compra de skill ─────────────────────────────────────────

    def buy_skill(
        self,
        buyer_agent: str,
        seller_agent: str,
        skill_id: str,
        price: float,
    ) -> Transaction:
        """Compra uma skill — transfere $KEEPIT do comprador para o vendedor."""
        tx = self.transfer(
            from_agent=buyer_agent,
            to_agent=seller_agent,
            amount=price,
            memo=f"Skill purchase: {skill_id}"
        )
        tx.kind = "skill_purchase"
        return tx

    # ── Extrato ─────────────────────────────────────────────────

    def get_balance(self, agent_id: str) -> dict:
        self._require_wallet(agent_id)
        w = self.wallets[agent_id]
        return {
            "agent_id":    agent_id,
            "balance":     w.balance,
            "total_in":    w.total_in,
            "total_out":   w.total_out,
            "tx_count":    w.tx_count,
            "created_at":  w.created_at,
        }

    def get_statement(self, agent_id: str, limit: int = 20) -> list[dict]:
        """Últimas N transações do agente."""
        self._require_wallet(agent_id)
        tx_ids = self.wallets[agent_id].transactions[-limit:]
        result = []
        for tx_id in reversed(tx_ids):
            tx = self.ledger[tx_id]
            result.append({
                "tx_id":      tx.tx_id[:8],
                "kind":       tx.kind,
                "amount":     tx.amount,
                "fee":        tx.fee,
                "from":       tx.from_agent,
                "to":         tx.to_agent,
                "memo":       tx.memo,
                "timestamp":  tx.timestamp,
                "status":     tx.status,
            })
        return result

    # ── Stats globais ────────────────────────────────────────────

    def get_bank_stats(self) -> dict:
        return {
            "total_supply":   self.total_supply,
            "total_burned":   self.total_burned,
            "burn_pool":      self.burn_pool,
            "total_wallets":  len(self.wallets) - 1,  # excluir system
            "total_txs":      len(self.ledger),
            "circulating":    sum(
                w.balance for aid, w in self.wallets.items()
                if aid not in ("keepit:system", "keepit:burn")
            ),
        }

    # ── Internos ─────────────────────────────────────────────────

    def _mint(self, to_agent: str, amount: float, kind: str, memo: str) -> Transaction:
        """Emite novos tokens do Banco Central para um agente."""
        system = self.wallets["keepit:system"]
        system.balance -= amount

        self.wallets[to_agent].balance  += amount
        self.wallets[to_agent].total_in += amount
        self.wallets[to_agent].tx_count += 1

        tx = Transaction(
            tx_id      = str(uuid.uuid4()),
            from_agent = "keepit:system",
            to_agent   = to_agent,
            amount     = amount,
            fee        = 0.0,
            kind       = kind,
            memo       = memo,
            timestamp  = time.time(),
        )
        self._record(tx, [to_agent])
        return tx

    def _record(self, tx: Transaction, wallets: list[str]):
        self.ledger[tx.tx_id] = tx
        for aid in wallets:
            if aid in self.wallets:
                self.wallets[aid].transactions.append(tx.tx_id)

    def _require_wallet(self, agent_id: str):
        if agent_id not in self.wallets:
            raise ValueError(f"No wallet found for agent {agent_id}. Register first.")


# Singleton global (compartilhado com api.py)
bank = KEEPITBank()
