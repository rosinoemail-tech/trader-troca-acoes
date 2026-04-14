# 📊 Sistema de Pairs Trading - Arbitragem Estatística

Um sistema profissional de trading automatizado baseado em **pairs trading** e **cointegração estatística**. Detecta quando dois ativos correlacionados se desviam temporariamente um do outro e aproveita a reversão à média.

## 🎯 Conceito

**Pairs Trading** é uma estratégia de arbitragem estatística que:

1. Identifica dois ativos altamente correlacionados
2. Calcula o **spread** entre seus preços logarítmicos
3. Mede desvios usando **Z-score**
4. Compra o ativo desvalorizado e vende o sobrevalorizado
5. Lucra quando os preços convergem novamente

```
Exemplo:
Stock A = $100  |  Stock B = $50
Correlação histórica: forte

Dia 1: Stock A = $105 (↑)  |  Stock B = $50 (=)
      → Spread aumenta, Z-score = +2.5
      → SINAL: Vender A, Comprar B (aposta em convergência)

Dia 2: Stock A = $102 (↓)  |  Stock B = $52 (↑)
      → Spread diminui, Z-score = +0.8
      → SINAL: Fechar posição (lucro!)
```

## 📦 Arquitetura do Sistema

```
pairs-trading-system/
├── main.py                 # Orquestrador principal com exemplo completo
├── config.py               # Configurações e thresholds
├── requirements.txt        # Dependências Python
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # Carregamento de dados
│   ├── statistical_tests.py    # Testes de cointegração e correlação
│   ├── spread_calculator.py    # Cálculo do spread e Z-score
│   ├── trading_signals.py      # Geração de sinais (compra/venda)
│   ├── risk_management.py      # Tamanho de posição e risco
│   └── backtester.py           # Simulação de trading
├── tests/
│   └── test_pairs_trading.py   # Testes unitários
└── data/
    └── historical_data.csv     # Dados históricos (exemplo)
```

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar Demonstração

```bash
python main.py
```

Isso irá:
- Gerar dados de exemplo
- Analisar correlação entre ativos
- Calcular hedge ratio
- Testar cointegração
- Executar backtest completo
- Mostrar resultados e detalle de trades

## 📐 Formulação Matemática

### Spread (S)
```
S(t) = ln(P_A(t)) - β × ln(P_B(t))
```
Onde:
- P_A, P_B = preços dos ativos
- β = hedge ratio (coeficiente de regressão)

### Z-Score
```
Z(t) = (S(t) - μ) / σ
```
Onde:
- μ = média móvel do spread (janela lookback)
- σ = desvio padrão móvel do spread

### Sinais de Entrada
```
Z < -2.0  →  Ativo A está desvalorizado  →  COMPRA A, VENDE B
Z > +2.0  →  Ativo A está sobrevalorizado →  VENDA A, COMPRA B
```

### Sinais de Saída
```
|Z| < 0.5  →  Convergência, FECHAR posição
|Z| > 3.5  →  Extremo, STOP LOSS
```

## 🔧 Configuração

Edite [config.py](config.py):

```python
LOOKBACK_WINDOW = 60              # Dias para calcular média
Z_SCORE_ENTRY_THRESHOLD = 2.0     # Limiar de entrada
Z_SCORE_EXIT_THRESHOLD = 0.5      # Limiar de saída
Z_SCORE_STOP_LOSS = 3.5           # Stop loss em Z extremo
MIN_COINTEGRATION_PVALUE = 0.05   # Validação estatística
MAX_POSITION_SIZE = 100000        # Tamanho máx de posição
```

## 📊 Módulos Principais

### `data_loader.py`
Carrega dados históricos de preços:
```python
from src.data_loader import DataLoader

df_a, df_b = DataLoader.load_from_csv("stock_a.csv", "stock_b.csv")
# ou
df_a, df_b = DataLoader.load_from_dict(dates, prices_a, prices_b)
```

### `statistical_tests.py`
Valida cointegração antes de operar:
```python
from src.statistical_tests import StatisticalTests

# Teste de Johansen (cointegração)
result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
if result['is_cointegrated']:
    print("✓ Ativos são cointegrados - válido para pairs trading")

# Hedge ratio (regressão)
beta, alpha = StatisticalTests.calculate_hedge_ratio(log_a, log_b)

# Correlação
corr, pvalue = StatisticalTests.calculate_correlation(price_a, price_b)
```

### `spread_calculator.py`
Calcula spread e Z-score:
```python
from src.spread_calculator import SpreadCalculator

calc = SpreadCalculator(log_price_a, log_price_b, beta=0.95)
metrics = calc.calculate_all_metrics(lookback=60)
# Returns: spread, spread_mean, spread_std, zscore
```

### `trading_signals.py`
Gera sinais de entrada/saída:
```python
from src.trading_signals import TradingSignals

gen = TradingSignals(entry_threshold=2.0, exit_threshold=0.5)
signals, counts = gen.generate_signals(zscore_series)
```

### `risk_management.py`
Calcula tamanho de posição:
```python
from src.risk_management import RiskManager

rm = RiskManager(account_size=100000, max_risk_per_trade=0.02)
pos = rm.calculate_position_size(price_a, price_b, zscore, beta)
# Returns: position_a, position_b, notional_a, notional_b
```

### `backtester.py`
Executa simulação completa:
```python
from src.backtester import Backtest

backtest = Backtest(price_a, price_b, beta, capital=100000)
results = backtest.run(lookback=60)
# Returns: total_trades, win_rate, sharpe_ratio, max_drawdown, etc.
```

## 📈 Saída Esperada

```
======================================================================
 SISTEMA DE PAIRS TRADING - ARBITRAGEM ESTATÍSTICA
======================================================================

ETAPA 1: Carregamento de Dados
✓ Ativo A: 500 períodos | Preço: 96.52 → 104.23
✓ Ativo B: 500 períodos | Preço: 47.18 → 52.64

ETAPA 2: Análise Estatística
📊 Correlação de Pearson: 0.8234
   P-value: 0.000000
   Status: ✓ ALTAMENTE CORRELACIONADO

🎯 Hedge Ratio (β): 0.9534
   Interpretação: Para cada $1 de B, vende $0.9534 de A

🔍 Teste de Cointegração (Johansen)...
   Estatística de Traço: 42.5234
   Valor Crítico (95%): 15.4072
   Status: ✓ COINTEGRADOS (válido para pairs trading)

ETAPA 6: Backtesting da Estratégia
[INFO] Executando backtest...

[2023-04-10] ENTRADA LONG | Z=-2.15 | Custo: $1,234.56
[2023-04-25] SAÍDA NORMAL | LONG | Z=-2.15→0.32 | P&L: $2,456.78
[2023-06-15] ENTRADA SHORT | Z=+2.45 | Custo: $1,156.23
[2023-07-02] SAÍDA NORMAL | SHORT | Z=+2.45→0.18 | P&L: $1,893.45

ETAPA 7: Resultados do Backtest
📊 PERFORMANCE GERAL:
   Capital Inicial: $100,000.00
   Capital Final: $105,350.23
   P&L Total: $5,350.23
   P&L %: 5.35%

📈 ESTATÍSTICAS DE TRADES:
   Total de Trades: 12
   Trades Vencedores: 9
   Trades Perdedores: 3
   Taxa de Acerto: 75.00%
   P&L Médio por Trade: $445.85

⚠️  MÉTRICAS DE RISCO:
   Drawdown Máximo: -3.45%
   Sharpe Ratio: 1.2434
```

## ⚙️ Usar Com Dados Reais

### Exemplo com Yahoo Finance:

```python
import yfinance as yf
from src.data_loader import DataLoader

# Download de dados reais
data_a = yf.download('AAPL', start='2023-01-01', end='2024-01-01')
data_b = yf.download('MSFT', start='2023-01-01', end='2024-01-01')

df_a = data_a[['Adj Close']].rename(columns={'Adj Close': 'price'})
df_b = data_b[['Adj Close']].rename(columns={'Adj Close': 'price'})

# Validar cointegração
from src.statistical_tests import StatisticalTests
import numpy as np

log_a = np.log(df_a['price'])
log_b = np.log(df_b['price'])

result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
if result['is_cointegrated']:
    print("✓ AAPL e MSFT são cointegrados!")
    # Executar pairs trading...
```

## 📚 Tópicos Avançados

### Validação de Cointegração

A cointegração é **crítica** para pairs trading funcionar:

```python
# Teste inadequado: correlação alta não garante pares válidos
corr = 0.95  # Correlação forte

# Teste correto: validar cointegração com Johansen
coint = johansen_cointegration_test(log_a, log_b)
if coint['is_cointegrated']:  # Trace stat > Critical value
    print("✓ Par válido para pairs trading")
```

### Janela Móvel (Rolling Window)

O sistema recalcula continuamente a média e desvio padrão:

```python
LOOKBACK_WINDOW = 60  # Recalcula a cada período com últimos 60 dias
```

Isso permite adaptação a mudanças de regime do mercado.

### Gestão de Risco

- **Position Sizing**: Redimensiona baseado no Z-score atual
- **Stop Loss**: Ativa ao atingir Z extremo (3.5)
- **Margem**: Verifica requisitos antes de entrar
- **Custos**: Considera custos de transação

## 🔗 Referências

- Gaurriot, C. et al. (2012) - "Statistical Arbitrage with Vine-Copulas"
- Do, B., Faff, R., & Hamza, K. (2006) - "A new approach to modeling and estimation for pairs trading"
- Engle, R. F., & Granger, C. W. (1987) - "Co-integration and error correction"

## ⚠️ Disclaimer

Este é um **sistema educacional** para fins de aprendizado. Não é aconselhável usar em produção sem validação adicional, backtesting extensivo e gestão de risco profissional.

## 📝 Licença

MIT License - Livre para uso e distribuição

---

**Desenvolvido para arbitragem estatística e pesquisa em mercados financeiros.**
