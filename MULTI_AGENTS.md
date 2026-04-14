# 🤖 Sistema Multi-Agentes para Pairs Trading

Um sistema sofisticado de 4 **agentes de IA autônomos** que trabalham juntos para executar pairs trading (arbitragem estatística) com total coordenação e supervisão mútua.

## 🎯 Visão Geral

O sistema utiliza **múltiplos agentes especializados** que se comunicam via **event bus central**, permitindo uma arquitetura modular, escalável e que simula decisões coletivas sobre trading.

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVENT BUS CENTRAL                           │
│              (Orquestrador de Comunicação)                       │
└─────────────────────────────────────────────────────────────────┘
  ↑                ↑                  ↑                 ↑
  │                │                  │                 │
  ↓                ↓                  ↓                 ↓
┌──────────┐  ┌──────────┐     ┌──────────┐     ┌──────────┐
│ MONITOR  │  │ EXECUTOR │     │ REPORTS  │     │ EXPERT   │
│          │  │          │     │          │     │          │
│ Busca    │  │ Executa  │     │ Gera     │     │ Valida & │
│ oportunid│  │ trades   │     │ análises │     │ aprende  │
│ em tempo │  │ em broker│     │ de perf. │     │ histórico│
│ real     │  │          │     │          │     │          │
└──────────┘  └──────────┘     └──────────┘     └──────────┘
```

## 📋 Os 4 Agentes

### 1️⃣ **MONITOR AGENT** 🔍
**Responsabilidade:** Monitorar mercado em tempo real e detectar oportunidades

**O que faz:**
- Conecta com feeds de dados em tempo real (quoteapi, broker APIs, etc)
- Monitora pares de ativos configurados continuamente
- Calcula Z-score do spread em tempo real
- Gera sinais quando Z-score cruza limiar (entrada)
- Busca convergência para sinais de saída

**Entrada:** Preços de mercado em tempo real
**Saída:** Mensagem `trading_opportunity` quando oportunidade detectada

**Exemplo de Oportunidade Detectada:**
```json
{
  "pair_key": "AAPL_MSFT",
  "pair_a": "AAPL",
  "pair_b": "MSFT",
  "signal": "BUY_A_SELL_B",
  "zscore": 2.45,
  "spread": 0.0452,
  "confidence": 89.2,
  "detected_at": "2024-04-14T09:30:45.123Z"
}
```

---

### 2️⃣ **EXECUTOR AGENT** ⚙️
**Responsabilidade:** Executar operações de compra/venda em plataforma broker

**O que faz:**
- Valida tamanho e riscos antes de executar
- Coloca ordens de compra E venda simultaneamente (par)
- Verifica requisitos de margem
- Acompanha status das ordens
- Fecha posições quando recebe sinal
- Calcula P&L realizado

**Entrada:** Mensagem de oportunidade validada + parâmetros de execução
**Saída:** Confirmação de ordens executadas

**Regras de Risco Integradas:**
- Máximo $500k de exposição total
- Máximo 2% de risco por trade
- Validação de margem obrigatória
- Check de preço mínimo > 0

---

### 3️⃣ **REPORTS AGENT** 📊
**Responsabilidade:** Análise de performance e geração de relatórios

**O que faz:**
- Registra cada trade executado
- Calcula estatísticas de performance
- Gera relatórios diários, semanais e mensais
- Calcula Sharpe Ratio, Drawdown, Win Rate
- Cria análise de lucro por símbolo
- Exporta HTML formatado

**Relatórios Gerados:**
- Daily Report: Performance do dia
- Weekly Report: Agregado semanal
- Performance Summary: Resumo geral
- Trade Analysis: Detalhes de cada trade

---

### 4️⃣ **EXPERT AGENT** 🧠
**Responsabilidade:** Validar oportunidades com conhecimento histórico

**O que faz:**
- **Valida** cada oportunidade detectada contra regras arbitragem
- **Aprende** dos resultados de cada trade (sucesso/falha)
- **Mantém** base de conhecimento com padrões históricos
- **Encontra** padrões similares para decisões futuras
- **Recomenda** parâmetros ótimos de execução

**Regras de Validação:**
- Mínimo 70% correlação entre ativos
- Z-score entre 1.5 e 3.5 para entrada
- Teste de cointegração obrigatório
- Máximo 3 falhas recentes no pair

**Decisões Inteligentes:**
```
IF histórico_sucesso > 70% THEN aumenta_posição = 110%
IF volatilidade_alta THEN reduz_posição = 70%
IF padrão_similar_histórico THEN confiança += 20%
IF múltiplas_falhas_recentes THEN bloqueia_par
```

---

## 🔄 Fluxo de Execução Completo

```
    MERCADO
       │
       │ Preços tempo real
       ↓
    MONITOR AGENT
       │
       │ Detecta oportunidade (Z > 2.0)
       ↓
    ┌──────────────────┐
    │ Mensagem enviada │
    │ "opportunity"    │
    └──────────────────┘
       │
       ├──→ EXPERT AGENT ←──────┐
       │    │                   │
       │    │ Valida            │ Aprova/Rejeita
       │    │ - correlação      │
       │    │ - cointegração    │
       │    │ - histórico       │
       │    └──────────────────→
       │                         │
       │ ◄─ OK & Confiança 85% ◄─┘
       │
       ↓
    ┌──────────────────────┐
    │ Calcula tamanho pos. │
    └──────────────────────┘
       │
       ↓
    EXECUTOR AGENT
       │
       │ - Valida margem
       │ - Coloca buy A
       │ - Coloca sell B
       │ - Confirma execução
       │
       ↓
    REPORTS AGENT
       │
       │ Registra trade
       │ Atualiza equity
       │
       ↓
    ┌──────────────────────┐
    │ POSIÇÃO ABERTA       │
    │ Aguardando regressão │
    └──────────────────────┘
       │
       │ Monitora pelo Monitor Agent
       │
       │ Se Z → 0 (convergência)
       │
       ↓
    EXECUTOR AGENT
       │
       │ - Vende A
       │ - Compra B
       │ - Fecha posição
       │
       ↓
    REPORTS AGENT
       │
       │ - Calcula P&L
       │ - Registra outcome
       │
       ↓
    EXPERT AGENT
       │
       │ - Aprende do resultado
       │ - Atualiza confiança no par
       │ - Ajusta regras futuras
       │
       ↓
    ┌──────────────────────┐
    │ CICLO COMPLETO       │
    │ Pronto para próximo  │
    └──────────────────────┘
```

---

##  💻 Como Usar

### Instalação

```bash
pip install -r requirements.txt
python demo_multi_agents.py
```

### Uso Programático

```python
from core.orchestrator import TradingOrchestrator

# Inicializar sistema
orchestrator = TradingOrchestrator(capital=100000, risk_per_trade=0.02)

# Adicionar pares ao monitoramento
orchestrator.add_pair_to_monitor("AAPL", "MSFT", beta=0.95)
orchestrator.add_pair_to_monitor("GOOGL", "AMZN", beta=0.92)

# Ajustar parâmetros se necessário
orchestrator.set_trading_parameters(
    entry_threshold=2.0,      # Z-score para entrada
    exit_threshold=0.5,       # Z-score para saída
    stop_loss=3.5            # Stop loss em Z extremo
)

# Status em tempo real
status = orchestrator.get_system_status()
print(f"Agentes rodando: {status['agent_statuses']}")

# Gerar relatório
report = orchestrator.generate_system_report()
```

### Integração com Broker Real

```python
from integrations.broker_adapter import BrokerAdapter
from core.orchestrator import TradingOrchestrator

# Conectar com broker
broker = BrokerAdapter(
    broker_type="interactive_brokers",
    account_id="your_account",
    api_key="your_key"
)

# Passar broker ao executor
orchestrator.executor.broker_api = broker

# Sistema agora executa com DADOS E ORDENS REAIS
orchestrator.add_pair_to_monitor("AAPL", "MSFT", beta=0.95)
```

---

## 🔌 Integrações com Brokers

### Template de Adaptador de Broker

```python
# integrations/broker_adapter.py
class BrokerAdapter:
    def __init__(self, broker_type, account_id, api_key):
        self.broker_type = broker_type
        self.account_id = account_id
        self.api_key = api_key
    
    async def get_prices(self, symbols):
        """Retorna preços atuais"""
        # Implementar para cada broker
        pass
    
    async def place_order(self, symbol, side, quantity, price, order_type):
        """Coloca uma ordem"""
        # Implementar para cada broker
        pass
    
    async def get_position(self, symbol):
        """Obtém posição aberta"""
        # Implementar para cada broker
        pass
    
    async def close_position(self, symbol):
        """Fecha uma posição"""
        # Implementar para cada broker
        pass
```

### Brokers Recomendados

| Broker | API | Latência | Custo | Documentação |
|--------|-----|----------|-------|--------------|
| Interactive Brokers | Python | Baixa (<100ms) | $1/trade | Excelente |
| Alpaca | REST/WebSocket | Média (100-500ms) | Grátis | Ótima |
| TD Ameritrade | REST | Média | $0-7 | Ótima |
| Binance (Crypto) | REST/WS | Baixa | 0.1% | Excelente |

---

## 📊 Exemplo de Saída Completa

```
================================================================================
 SISTEMA DE MÚLTIPLOS AGENTES PARA PAIRS TRADING
================================================================================

MONITOR AGENT:
  Status: RUNNING
  Pares Monitorando: 2
  Oportunidades Encontradas: 5
  Últimas:
    - AAPL_MSFT: BUY_A_SELL_B (Z=2.45) | Confiança: 89.2%
    - GOOGL_AMZN: SELL_A_BUY_B (Z=2.12) | Confiança: 78.5%

EXECUTOR AGENT:
  Status: RUNNING
  Ordens Executadas: 10
  Posições Abertas: 2
  Exposição Total: $47,350
  P&L Realizado: $2,450.75

REPORTS AGENT:
  Status: RUNNING
  Trades Registrados: 10
  Total P&L: $2,450.75
  Win Rate: 70.0% (7/10)
  Sharpe Ratio: 1.23
  Max Drawdown: -3.2%

EXPERT AGENT:
  Status: RUNNING
  Padrões Aprendidos: 247
  Pares Bem-Sucedidos: 8
  Pares Falhados: 2
  Confiança Média: 84.3%
  Decisões Tomadas: 10
```

---

## ⚠️ Considerações Críticas

### 1. **Validação de Cointegração**
```python
# OBRIGATÓRIO antes de operar com qualquer par
result = StatisticalTests.johansen_cointegration_test(log_prices_a, log_prices_b)
assert result['is_cointegrated'], "Ativos NÃO são cointegrados!"
```

Pares sem cointegração real resultarão em **perdas persistentes**.

### 2. **Custo de Transação**
```
Cada operação custa: spreads + comissão
Exemplo: 0.1% entrada + 0.1% saída = 0.2% por ciclo
Se P&L esperado < 0.5%, operação não é viável
```

### 3. **Riscos de Modelo**
- Cointegração pode **quebrar** sob stress de mercado
- Diferenças de liquidez podem impedir execução simultânea
- Gaps de preço podem causar P&L piores que esperado

### 4. **Testes Forward**
```python
# Sempre validar com dados fora da amostra!
backtest_period = "2023-01-01 a 2023-06-30"
forward_test_period = "2023-07-01 a 2023-08-31"
# Se performance cai >30%, modelo pode ter overfitt
```

---

## 🚀 Próximos Passos de Desenvolvimento

- [ ] Conectar com API de broker real
- [ ] Implementar monitoramento 24h/5 dias
- [ ] Adicionar mais agentes especializados
- [ ] ML para otimizar parâmetros dinamicamente
- [ ] Dashboard em tempo real
- [ ] Alert system (Email, SMS, Slack)
- [ ] Risk limits por pair/sector/portfolio
- [ ] Análise de correlação dinâmica intra-dia

---

## 📚 Referências

- Gatev, E., Goetzmann, W. N., & Rouwenhorst, K. G. (1999). "Pairs Trading: Performance of a Relative-Value Arbitrage Rule"
- Huck, N. (2010). "Pairs trading using Cointegration"
- Engle, R. F., & Granger, C. W. J. (1987). "Co-integration and error correction representation"

---

**Sistema Multi-Agentes de Pairs Trading © 2024**
