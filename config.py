# ============================================================================
# CONFIGURAÇÕES DO SISTEMA DE PAIRS TRADING
# ============================================================================

# JANELAS DE CÁLCULO
LOOKBACK_WINDOW = 60  # Dias para calcular média e desvio padrão
ROLLING_WINDOW = 20   # Dias para atualização móvel

# Z-SCORE THRESHOLDS
Z_SCORE_ENTRY_THRESHOLD = 2.0    # Limiar para entrada (compra/venda)
Z_SCORE_EXIT_THRESHOLD = 0.5     # Limiar para saída (convergência)
Z_SCORE_STOP_LOSS = 3.5          # Stop loss em extremo

# COINTEGRAÇÃO
MIN_COINTEGRATION_PVALUE = 0.05  # P-value máximo aceitável para cointegração

# RISCO E POSIÇÃO
MAX_POSITION_SIZE = 100000        # Tamanho máximo da posição
TRANSACTION_COST = 0.001          # 0.1% de custo de transação

# LOGGING
DEBUG_MODE = True
