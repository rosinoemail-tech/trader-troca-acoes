# 🚀 README - Sistema de Múltiplos Agentes para Pairs Trading

## ✅ O Que Foi Criado

Você agora tem um **sistema profissional e modular de 4 agentes autônomos** que trabalham juntos para executar pairs trading com arbitragem estatística.

### Estrutura de Pastas Criada

```
pairs-trading-system/
├── 📚 DOCUMENTAÇÃO
│   ├── README.md                    # Documentação do sistema principal
│   ├── MULTI_AGENTS.md             # Documentação detalhada dos agentes
│   ├── GETTING_STARTED.md          # Guia de início rápido
│   └── este arquivo (README - MultiAgents)
│
├── 🤖 SISTEMA DE AGENTES
│   ├── core/
│   │   ├── agent_base.py           # Base class de todos os agentes
│   │   ├── event_bus.py            # EventBus central de comunicação
│   │   └── orchestrator.py         # Orquestrador que coordena tudo
│   │
│   └── agents/
│       ├── monitor_agent.py        # 1️⃣ Monitor - Busca oportunidades em tempo real
│       ├── executor_agent.py       # 2️⃣ Executor - Executa trades no broker
│       ├── reports_agent.py        # 3️⃣ Reports - Gera análises de performance
│       └── expert_agent.py         # 4️⃣ Expert - Valida e aprende com histórico
│
├── 🔌 INTEGRAÇÕES COM BROKERS
│   └── integrations/
│       └── broker_adapter_template.py
│           ├── InteractiveBrokersAPI  # Para Interactive Brokers
│           ├── AlpacaAPI              # Para Alpaca
│           ├── BinanceAPI             # Para Binance
│           └── CustomBrokerAPI        # Template para novo broker
│
├── 📊 CÓDIGO PRINCIPAL
│   ├── main.py                     # Demo do sistema original
│   ├── config.py                   # Configurações
│   ├── demo_multi_agents.py        # Demo completa dos 4 agentes
│   └── src/                        # Código original (spread, signals, etc)
│
├── 📁 DADOS E TESTES
│   ├── data/                       # Dados de exemplo
│   └── tests/                      # Testes unitários
│
└── 📦 SETUP
    └── requirements.txt            # Dependências
```

---

## 🎯 Quick Start em 2 Minutos

### 1. Instalar Dependências

```bash
cd pairs-trading-system
pip install -r requirements.txt
```

### 2. Rodar Demo Completa

```bash
python demo_multi_agents.py
```

**Esperado:** Verá fluxo completo dos 4 agentes trabalhando juntos!

---

## 🤖 Os 4 Agentes

### 1. **MONITOR AGENT** 🔍
- **O que faz:** Monitora mercado em tempo real, detecta oportunidades
- **Entrada:** Preços de mercado
- **Saída:** Sinais de trading quando Z-score extremo
- **Arquivo:** `agents/monitor_agent.py`

```python
monitor = MonitorAgent(check_interval=60)
monitor.add_pair_to_watch("AAPL", "MSFT", beta=0.95)
opportunities = await monitor.scan_for_opportunities()
```

### 2. **EXECUTOR AGENT** ⚙️
- **O que faz:** Executa compra/venda em broker, gerencia ordens
- **Entrada:** Sinais validados do Expert
- **Saída:** Confirmação de execução, status de ordens
- **Arquivo:** `agents/executor_agent.py`

```python
executor = ExecutorAgent(broker_api=broker)
orders = await executor.place_pair_orders(opportunity, position_size)
await executor.close_position(pair_key, price_a, price_b)
```

### 3. **REPORTS AGENT** 📊
- **O que faz:** Registra trades, gera estatísticas e relatórios
- **Entrada:** Trades executados
- **Saída:** Relatórios diários/semanais, métricas
- **Arquivo:** `agents/reports_agent.py`

```python
reports = ReportsAgent()
reports.add_trade(trade_data)
daily_report = reports.generate_daily_report()
```

### 4. **EXPERT AGENT** 🧠
- **O que faz:** Valida oportunidades, aprende com histórico
- **Entrada:** Oportunidades do Monitor
- **Saída:** Validação + confiança + recomendações
- **Arquivo:** `agents/expert_agent.py`

```python
expert = ExpertAgent()
is_valid, confidence, reasons = expert.validate_opportunity(opp, stats)
expert.record_outcome(pair_key, signal, entry_z, exit_z, pnl, duration)
```

---

## 🔄 Fluxo de Execução

```
MERCADO (tempo real)
    ↓
MONITOR AGENT detecta Z > 2.0
    ↓
Envia para EXPERT AGENT
    ↓
EXPERT valida com histórico
    ├── Verifica cointegração
    ├── Valida correlação
    └── Aprova com confiança 85%
    ↓
EXECUTOR calcula tamanho
    ├── Verifica margem
    └── Coloca COMPRA A + VENDA B
    ↓
REPORTS registra trade
    ├── Equity inicial
    └── Parâmetros de entrada
    ↓
MONITOR monitora convergência (Z → 0)
    ↓
EXECUTOR fecha posição
    ├── Venda A + Compra B
    └── Calcula P&L
    ↓
REPORTS atualiza dados
    ├── P&L realizado
    ├── Duração
    └── Métricas
    ↓
EXPERT aprende
    ├── Registra padrão bem-sucedido
    ├── Atualiza confiança no par
    └── Prepara para próximo trade
```

---

## 💻 Uso Programático

### Setup Básico

```python
from core.orchestrator import TradingOrchestrator

# Inicializar
orch = TradingOrchestrator(capital=100000, risk_per_trade=0.02)

# Adicionar pares
orch.add_pair_to_monitor("AAPL", "MSFT", beta=0.95)
orch.add_pair_to_monitor("GOOGL", "AMZN", beta=0.92)

# Ajustar parâmetros
orch.set_trading_parameters(
    entry_threshold=2.0,     # Z-score para entrada
    exit_threshold=0.5,      # Z-score para saída
    stop_loss=3.5           # Z-score para stop
)
```

### Monitorar Status

```python
# Status em tempo real
status = orch.get_system_status()
print(f"Agentes: {status['agent_statuses']}")
print(f"Trades: {status['trades_executed']}")

# Relatório completo
report = orch.generate_system_report()
print(json.dumps(report, indent=2))
```

### Com Broker Real

```python
from integrations.broker_adapter_template import AlpacaAPI

# Conectar broker
broker = AlpacaAPI(api_key="your_key", secret_key="your_secret")
await broker.connect()

# Passar ao Executor
orch.executor.broker_api = broker

# Sistema agora executa ORDENS REAIS
```

---

## 📈 Exemplo de Saída Esperada

```
================================================================================
 SISTEMA DE MÚLTIPLOS AGENTES PARA PAIRS TRADING
================================================================================

MONITOR AGENT:
   ✓ 500 dias de dados carregados
   ✓ Par AAPL_MSFT monitorado
   ✓ Correlação: 0.8234
   ✓ Cointegração: SIM

OPPORTUNITY DETECTED:
   Par: AAPL_MSFT
   Sinal: BUY_A_SELL_B
   Z-score: 2.45
   Confiança: 89.2%

EXPERT VALIDATION:
   ✓ Válida
   ✓ Confiança: 85%
   ✓ Padrões históricos similares: 5

EXECUTOR:
   ✓ Ordem BUY 100 AAPL @ $150.25
   ✓ Ordem SELL 125 MSFT @ $377.80
   ✓ Total Notional: $94,725

REPORTS:
   ✓ Trade registrado
   ✓ Equity: $5,275

[Aguardando convergência...]

CONVERGÊNCIA DETECTADA (Z = 0.32):

EXECUTOR:
   ✓ Ordem SELL 100 AAPL @ $149.10
   ✓ Ordem BUY 125 MSFT @ $379.50

FINAL:
   ✓ P&L: $1,250.75
   ✓ Duração: 4h 23min
   ✓ Taxa de Retorno: 1.25%

EXPERT LEARNING:
   ✓ Padrão registrado
   ✓ Sucesso confirmado
   ✓ Confiança do par aumentada
```

---

## 🔌 Integração com Brokers

### Interactive Brokers
```python
from integrations.broker_adapter_template import InteractiveBrokersAPI

broker = InteractiveBrokersAPI(account_id="DU123456")
await broker.connect()
```

### Alpaca
```python
from integrations.broker_adapter_template import AlpacaAPI

broker = AlpacaAPI(api_key="KEY", secret_key="SECRET")
await broker.connect()
```

### Binance (Cripto)
```python
from integrations.broker_adapter_template import BinanceAPI

broker = BinanceAPI(api_key="KEY", secret_key="SECRET", testnet=True)
await broker.connect()
```

### Novo Broker
```python
from integrations.broker_adapter_template import BrokerAPI

class MyBrokerAPI(BrokerAPI):
    async def connect(self):
        # Implementar
        pass
    
    async def get_price(self, symbol):
        # Implementar
        pass
    
    # ... outros métodos
```

---

## ⚙️ Configuração de Parâmetros

Editar `config.py`:

```python
# Z-Score
Z_SCORE_ENTRY_THRESHOLD = 2.0        # Entrada
Z_SCORE_EXIT_THRESHOLD = 0.5         # Saída
Z_SCORE_STOP_LOSS = 3.5              # Stop loss

# Janelas
LOOKBACK_WINDOW = 60                 # Dias para média
ROLLING_WINDOW = 20                  # Atualização móvel

# Risco
MAX_POSITION_SIZE = 100000           # Máximo por posição
TRANSACTION_COST = 0.001             # 0.1%
```

---

## 🧪 Testes

```bash
# Rodar testes
pytest tests/test_pairs_trading.py -v

# Com coverage
pytest tests/ --cov=src --cov=agents --cov=core
```

---

## 📊 Estrutura de Mensagens

Os agentes se comunicam via **mensagens estruturadas**:

```python
{
    'sender': 'MonitorAgent',
    'receiver': 'ExpertAgent',
    'message_type': 'trading_opportunity',
    'payload': {
        'pair_key': 'AAPL_MSFT',
        'signal': 'BUY_A_SELL_B',
        'zscore': 2.45,
        ...
    },
    'priority': 'HIGH',
    'timestamp': '2024-04-14T09:30:45Z',
    'status': 'delivered'
}
```

---

## 🎓 Arquitetura

### Event-Driven
```
EventBus Central
├── Subscribe/Publish model
├── Async/Await para operações
└── Message Queue com prioridades
```

### Multi-Agent
```
Cada agente:
├── Independente (roda autonomamente)
├── Especializado (foco em uma área)
├── Comunicativo (via EventBus)
└── Inteligente (aprende e decide)
```

### Modular
```
Fácil de:
├── Adicionar novo agente
├── Substituir broker
├── Estender funcionalidades
└── Integrar com sistemas externos
```

---

## 🚀 Próximos Passos

- [x] Arquitetura multi-agentes criada ✅
- [x] 4 agentes especializados ✅
- [x] EventBus de comunicação ✅
- [x] Orquestrador central ✅
- [x] Templates de broker ✅
- [ ] Conectar broker real
- [ ] Dashboard em tempo real
- [ ] ML para otimização
- [ ] Monitoramento 24h/5d
- [ ] Risk limits avançados
- [ ] Alerts (Email, Slack, SMS)

---

## 📚 Documentação Adicional

- [MULTI_AGENTS.md](MULTI_AGENTS.md) - Documentação detalhada dos agentes
- [README.md](README.md) - Documentação do sistema de pairs trading
- [GETTING_STARTED.md](GETTING_STARTED.md) - Guia de início rápido

---

## ⚠️ Avisos Importantes

1. **Validar Cointegração**: Sempre testar cointegração antes de colocar dinheiro real
2. **Custo de Transação**: P&L esperado deve ser > 0.5% para ser viável
3. **Backtest Forward**: Sempre testar com dados fora da amostra
4. **Risk Management**: Nunca desabilitar validações de risco
5. **Paper Trading**: Simular em ambiente de demo antes de live

---

## 💬 Suporte

Para dúvidas sobre:
- **Agentes**: Consulte `MULTI_AGENTS.md`
- **Configuração**: Veja `config.py`
- **Brokers**: Verifique `integrations/broker_adapter_template.py`
- **Conceitos**: Leia `README.md`

---

## 📄 Licença

MIT License - Livre para uso educacional e comercial

---

**Sistema de Múltiplos Agentes para Pairs Trading**
**Desenvolvido para arbitragem estatística profissional**
**Versão 1.0.0 - Abril 2024**
