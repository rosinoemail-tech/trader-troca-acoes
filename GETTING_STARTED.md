# 🚀 Guia de Início Rápido - Pairs Trading System

## Instalação (5 minutos)

### 1. Clonar/Extrair o Projeto
```bash
cd pairs-trading-system
```

### 2. Criar Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

## Primeiro Uso (2 minutos)

### Executar Demo Completa
```bash
python main.py
```

Isso irá:
1. ✓ Gerar dados de exemplo
2. ✓ Analisar correlação
3. ✓ Testar cointegração
4. ✓ Executar backtest
5. ✓ Mostrar resultados

**Saída esperada**: Relatório completo com P&L, trades executados e métricas de risco.

## Usar Com Seus Dados

### Opção 1: Arquivos CSV

```python
from src.data_loader import DataLoader
from src.statistical_tests import StatisticalTests
from src.backtester import Backtest
import numpy as np

# Carregar dados
df_a, df_b = DataLoader.load_from_csv('seu_ativo_a.csv', 'seu_ativo_b.csv')

# Validar cointegração
log_a = np.log(df_a['price'])
log_b = np.log(df_b['price'])

result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
if result['is_cointegrated']:
    print("✓ Ativos são cointegrados!")
    
    # Obter hedge ratio
    beta, _ = StatisticalTests.calculate_hedge_ratio(log_a, log_b)
    
    # Executar backtest
    backtest = Backtest(df_a['price'], df_b['price'], beta, capital=100000)
    results = backtest.run()
    
    print(f"P&L: ${results['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.4f}")
else:
    print("✗ Ativos não são cointegrados")
```

**Formato CSV esperado**:
```
date,price
2023-01-01,100.50
2023-01-02,101.30
```

### Opção 2: Yahoo Finance (Dados Reais)

Primeiro instale:
```bash
pip install yfinance
```

Depois:
```python
import yfinance as yf
import numpy as np
from src.statistical_tests import StatisticalTests
from src.backtester import Backtest

# Download de dados reais
data_a = yf.download('AAPL', start='2022-01-01', end='2024-01-01')
data_b = yf.download('MSFT', start='2022-01-01', end='2024-01-01')

# Preparar formato
import pandas as pd
df_a = data_a[['Adj Close']].rename(columns={'Adj Close': 'price'})
df_b = data_b[['Adj Close']].rename(columns={'Adj Close': 'price'})

# Validar cointegração
log_a = np.log(df_a['price'])
log_b = np.log(df_b['price'])

result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
if result['is_cointegrated']:
    beta, _ = StatisticalTests.calculate_hedge_ratio(log_a, log_b)
    
    backtest = Backtest(df_a['price'], df_b['price'], beta)
    results = backtest.run()
    
    print(results)
```

## Estrutura Modular

### Use Módulos Individualmente

#### 1. Apenas Análise de Cointegração
```python
from src.statistical_tests import StatisticalTests
import numpy as np

log_a = np.log([100, 101, 102, 103])
log_b = np.log([50, 50.5, 51, 51.5])

result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
print(f"Cointegrado: {result['is_cointegrated']}")
```

#### 2. Apenas Cálculo de Spread
```python
from src.spread_calculator import SpreadCalculator
import pandas as pd
import numpy as np

log_a = pd.Series([4.605, 4.615, 4.625])
log_b = pd.Series([3.912, 3.922, 3.932])
beta = 0.95

calc = SpreadCalculator(log_a, log_b, beta)
metrics = calc.calculate_all_metrics()
print(metrics)
```

#### 3. Apenas Geração de Sinais
```python
from src.trading_signals import TradingSignals
import pandas as pd

zscore = pd.Series([0, -1, -2.5, -1.5, 0.2, 2.8, 1.2, 0])
signals_gen = TradingSignals()
signals, counts = signals_gen.generate_signals(zscore)
print(f"Sinais: {counts}")
```

#### 4. Apenas Cálculo de Risco
```python
from src.risk_management import RiskManager

rm = RiskManager(account_size=100000, max_risk_per_trade=0.02)

pos_size = rm.calculate_position_size(
    current_price_a=100,
    current_price_b=50,
    zscore=-2.5,
    beta=0.95
)

print(f"Ativo A: ${pos_size['notional_a']:.2f}")
print(f"Ativo B: ${pos_size['notional_b']:.2f}")
```

## Executar Testes

```bash
pytest tests/test_pairs_trading.py -v
```

Resultados esperados: Todos os testes passem ✓

## Configurar Parâmetros

Edite `config.py`:

```python
# Para estratégia mais agressiva (mais trades)
Z_SCORE_ENTRY_THRESHOLD = 1.5  # Antes era 2.0

# Para reduzir stop loss
Z_SCORE_STOP_LOSS = 3.0  # Antes era 3.5

# Para follow-up mais apertado
Z_SCORE_EXIT_THRESHOLD = 0.2  # Antes era 0.5

# Para risco maior
max_risk_per_trade = 0.05  # 5% ao invés de 2%
```

## Exemplos de Casos de Uso

### Caso 1: Stocks Correlacionados
```python
# Apple vs Microsoft
# Ambas tech companies, altamente correlacionadas
from yfinance...

# Espera-se cointegração ✓
```

### Caso 2: Futuros e Spot
```python
# ETF SPY vs Futuro ES
# Mesmos ativos, diferentes mercados
# Espera-se cointegração ✓
```

### Caso 3: Pares Internacionais
```python
# USD/BRL vs USD/ARS
# Ambas moedas emergentes
# Pode ter cointegração dependendo período
```

## Debugar Problemas

### Problema: "Ativos não são cointegrados"
```
Solução:
1. Verifique período de dados (precisa mínimo 60 dias)
2. Verifique correlação (deve ser > 0.7)
3. Tente outro par de ativos
4. Aumente LOOKBACK_WINDOW em config.py
```

### Problema: "Nenhum trade foi executado"
```
Solução:
1. Reduza Z_SCORE_ENTRY_THRESHOLD em config.py (ex: 1.5 ao invés de 2.0)
2. Verifique se há suficientes desvios no spread
3. Aumente período de dados
4. Verifique Z-score com: print(metrics['zscore'])
```

### Problema: "Trazido Negativo"
```
Solução:
1. Aumentar Z_SCORE_ENTRY_THRESHOLD (ser mais seletivo)
2. Aumentar Z_SCORE_EXIT_THRESHOLD (sair mais cedo)
3. Reduzir MAX_RISK_PER_TRADE
4. Validar que cointegração é genuína
```

## Próximos Passos

1. **Entender o conceito**: Leia a seção "Conceito" no README.md
2. **Estudar a matemática**: Ver formulação em README.md
3. **Testar com dados reais**: Use Yahoo Finance ou seu broker
4. **Ajustar parâmetros**: Otimizar para seu estilo de risco
5. **Validar backtest**: Testar forward testing com dados fora da amostra
6. **Deploy**: Integrar com API de broker para trading real

## Recursos Adicionais

- **Documentação Completa**: [README.md](README.md)
- **Exemplos de Código**: [main.py](main.py)
- **Testes Automáticos**: [tests/test_pairs_trading.py](tests/test_pairs_trading.py)
- **Configurações**: [config.py](config.py)

## Suporte

Para dúvidas ou problemas:
1. Consulte o README.md
2. Verifique os testes em `tests/`
3. Assim os exemplos em `main.py`

---

**Bom trading! 📈**
