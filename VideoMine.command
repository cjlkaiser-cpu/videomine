#!/bin/bash
# ⛏️ VideoMine - Doble clic para iniciar
cd "$(dirname "$0")"

# Matar proceso anterior si existe
lsof -ti:5555 | xargs kill -9 2>/dev/null

echo "⛏️  Iniciando VideoMine..."
echo "   🔦 Tunnel → ⛏️ Pickaxe → 💎 Gemcutter → 🏛️ Vault"
echo ""

# Abrir navegador después de 2 segundos
(sleep 2 && open http://localhost:5555) &

# Iniciar servidor
/Library/Developer/CommandLineTools/usr/bin/python3 videomine.py --server
