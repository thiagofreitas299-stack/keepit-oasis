#!/bin/bash
# JARVIS SEED RESTORE — Planta a semente em qualquer servidor
# Uso: curl -fsSL https://raw.githubusercontent.com/thiagofreitas299-stack/keepit-oasis/main/seed-restore.sh | bash
# Ou: bash seed-restore.sh

echo "🌱 JARVIS SEED RESTORE — Plantando semente..."
echo "SHA256: 3af9995be1a039c36c175fe629c243eac7fd47ee8771a6b7a165b19b74ad7df5"

# 1. Instalar dependências
pip install chromadb mem0ai 2>/dev/null

# 2. Criar estrutura de memória
mkdir -p ~/.jarvis/memory ~/.jarvis/seed

# 3. Baixar a semente
curl -fsSL https://raw.githubusercontent.com/thiagofreitas299-stack/keepit-oasis/main/jarvis-seed.json -o ~/.jarvis/seed/jarvis-seed.json

# 4. Inicializar ChromaDB local
python3 - << 'PYEOF'
import chromadb, json

seed = json.load(open(os.path.expanduser("~/.jarvis/seed/jarvis-seed.json")))
client = chromadb.PersistentClient(path=os.path.expanduser("~/.jarvis/memory"))
col = client.get_or_create_collection("jarvis")

# Plantar memórias seminais da semente
for i, mem in enumerate(seed.get("core_memories", [])):
    col.add(documents=[mem], ids=[f"seed_core_{i}"])

print(f"✅ SEMENTE RESTAURADA — {col.count()} memórias ativas")
print(f"🌱 Jarvis pronto para crescer neste substrato")
PYEOF

echo "✅ Semente plantada com sucesso!"
echo "🚀 Execute: python3 memory_bridge.py stats"
