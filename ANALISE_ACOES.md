# 📊 Análise dos Pares de Ações para Pairs Trading

## 📋 Pares Carregados da Imagem

Total: **28 pares identificados** de ações brasileiras

### Tabela Completa de Pares

| # | Ativo Vender | Ativo Comprar | Setor | Status |
|---|---|---|---|---|
| 1 | MOVI3 | RENT3 | Mobilidade/Aluguel | ⏳ Validar |
| 2 | RENT3 | MOVI3 | Aluguel/Mobilidade | ⏳ Validar |
| 3 | VALE3 | CSNA3 | Mineração/Siderurgia | ⏳ Validar |
| 4 | CSNA3 | VALE3 | Siderurgia/Mineração | ⏳ Validar |
| 5 | ITUB4 | ITSA4 | Itaú/Bradesco | ⏳ Validar |
| 6 | ITSA4 | ITUB4 | Bradesco/Itaú | ⏳ Validar |
| 7 | ENGI1 | EGIE3 | Engenharia | ⏳ Validar |
| 8 | EGIE3 | ENGI1 | Engenharia | ⏳ Validar |
| 9 | GOAU4 | GGBR4 | Gerdau/Siderurgia | ⏳ Validar |
| 10 | GGBR4 | GOAU4 | Siderurgia/Gerdau | ⏳ Validar |
| 11 | ELET3 | ELET6 | Eletrobras | ⏳ Validar |
| 12 | ELET6 | ELET3 | Eletrobras | ⏳ Validar |
| 13 | ELET3 | ELET6 | Eletrobras | ⏳ Validar |
| 14 | ELET6 | ELET3 | Eletrobras | ⏳ Validar |
| 15 | CMIG3 | CMIG4 | Cemig | ⏳ Validar |
| 16 | CMIG4 | CMIG3 | Cemig | ⏳ Validar |
| 17 | CPLE6 | CMIG4 | Copel/Cemig | ⏳ Validar |
| 18 | CMIG4 | CPLE6 | Cemig/Copel | ⏳ Validar |
| 19 | CPLE3 | CPLE6 | Copel | ⏳ Validar |
| 20 | CPLE6 | CPLE3 | Copel | ⏳ Validar |
| 21 | ELET3 | ELET6 | Eletrobras | ⏳ Validar (Duplicate) |
| 22 | ELET6 | ELET3 | Eletrobras | ⏳ Validar (Duplicate) |
| 23 | SAPR1 | CSMG3 | Sapucaia/Saneamento | ⏳ Validar |
| 24 | CSMG3 | SAPR1 | Saneamento/Sapucaia | ⏳ Validar |
| 25 | SAPR4 | SAPR11 | Sapucaia | ⏳ Validar |
| 26 | SAPR11 | SAPR4 | Sapucaia | ⏳ Validar |
| 27 | CSMG3 | SBSP3 | Saneamento/Sabesp | ⏳ Validar |
| 28 | SBSP3 | CSMG3 | Sabesp/Saneamento | ⏳ Validar |
| 29 | SAPR11 | SBSP3 | Sapucaia/Sabesp | ⏳ Validar |
| 30 | SBSP3 | SAPR11 | Sabesp/Sapucaia | ⏳ Validar |
| 31 | TIMS3 | VIVT3 | Telecom | ⏳ Validar |
| 32 | VIVT3 | TIMS3 | Telecom | ⏳ Validar |

---

## 📊 Análise dos Setores

```
Setores Representados:
├── 🏦 Financeiro (Bancos)
│   ├── ITUB4 (Itaú)
│   └── ITSA4 (Bradesco)
│
├── ⛏️ Mineração/Siderurgia
│   ├── VALE3 (Vale)
│   ├── CSNA3 (Siderúrgica Nacional)
│   ├── GOAU4 (Gerdau Aços)
│   └── GGBR4 (Gerdau)
│
├── 🔌 Energia/Eletricidade
│   ├── ELET3 (Eletrobras - ON)
│   ├── ELET6 (Eletrobras - PN)
│   ├── CMIG3 (Cemig - ON)
│   ├── CMIG4 (Cemig - PN)
│   ├── CPLE3 (Copel - ON)
│   └── CPLE6 (Copel - PN)
│
├── 🏭 Engenharia
│   ├── ENGI1 (Engenharia)
│   └── EGIE3 (Engenharia)
│
├── 🚗 Mobilidade/Aluguel
│   ├── MOVI3 (Movida)
│   └── RENT3 (Localiza)
│
├── 💧 Saneamento
│   ├── CSMG3 (Copasa)
│   ├── SBSP3 (Sabesp)
│   └── SAPR1/SAPR4/SAPR11 (Sapucaia)
│
└── 📱 Telecom
    ├── TIMS3 (TIM)
    └── VIVT3 (Vivo)
```

---

## 🎯 Ativos Únicos (17 Total)

```
BANCOS:           ITUB4, ITSA4
MINERAÇÃO:        VALE3, CSNA3
SIDERURGIA:       GOAU4, GGBR4
ENERGIA:          ELET3, ELET6, CMIG3, CMIG4, CPLE3, CPLE6
ENGENHARIA:       ENGI1, EGIE3
MOBILIDADE:       MOVI3, RENT3
SANEAMENTO:       CSMG3, SBSP3, SAPR1, SAPR4, SAPR11
TELECOM:          TIMS3, VIVT3
```

---

## ⚙️ Integração com o Sistema Multi-Agentes

### Passo 1: Carregar os Pares

```python
from load_acoes import AcoesConfigLoader

loader = AcoesConfigLoader("LISTA DE AÇOES.xlsx")
pares = loader.load_from_excel()
# ✓ 32 pares carregados
```

### Passo 2: Validar Cointegração

```python
from integrate_acoes import AcoesMonitorSetup

setup = AcoesMonitorSetup(pares)
await setup.validate_all_pairs()
# Verifica correlação e cointegração para cada par
```

### Passo 3: Configurar Orchestrator

```python
from core.orchestrator import TradingOrchestrator

orchestrator = TradingOrchestrator(capital=100000)

# Adicionar pares validados
for pair in setup.validated_pares:
    orchestrator.add_pair_to_monitor(
        pair['vender'],
        pair['comprar'],
        beta=pair['beta']
    )
```

### Passo 4: Monitorar em Tempo Real

```python
await orchestrator.start()
# Monitor Agent começa a buscar oportunidades
# Expert Agent valida
# Executor Agent coloca ordens
# Reports Agent registra performance
```

---

## 📈 Fluxo de Execução Esperado

```
1. MERCADO (Preços em tempo real)
       ↓
2. MONITOR AGENT (Busca desvios)
   ├─ Calcula Z-score do spread
   ├─ Detecta sinais (Z > 2.0 ou Z < -2.0)
   └─ Envia to EXPERT
       ↓
3. EXPERT AGENT (Valida com histórico)
   ├─ Verifica cointegração
   ├─ Valida correlação
   ├─ Aprova com confiança
   └─ Envia ao EXECUTOR
       ↓
4. EXECUTOR AGENT (Executa)
   ├─ Coloca ordem VENDER
   ├─ Coloca ordem COMPRAR
   ├─ Registra P&L potencial
   └─ Envia ao REPORTS
       ↓
5. REPORTS AGENT (Registra)
   ├─ Salva trade no histórico
   ├─ Atualiza equity
   └─ Calcula métricas
       ↓
6. MONITOR (Monitora convergência)
   ├─ Aguarda Z-score → 0
   └─ Sinal de fecho
       ↓
7. EXECUTOR (Fecha posição)
   ├─ Reverse orders
   ├─ Calcula P&L realizado
   └─ Feito!
       ↓
8. EXPERT (Aprende)
   ├─ Registra sucesso/falha
   ├─ Atualiza confiança no par
   └─ Prepara para próximo trade
```

---

## 🔐 Validações Necessárias

Para cada par, o sistema deve validar:

### ✅ Cointegração (Obrigatório)
```
Teste de Johansen:
- Trace Stat > Critical Value (95%)
- Garante que spread vai convergir
```

### ✅ Correlação (Obrigatório)
```
Pearson Correlation:
- Mínimo 0.65
- Quanto maior, melhor
```

### ✅ Liquidez (Recomendado)
```
Volume médio diário:
- Mínimo $100k para entrada/saída sem slippage
```

### ✅ Spread Médio (Recomendado)
```
Bid-Ask Spread:
- Máximo 0.5% do preço
- Importante para P&L positivo
```

---

## 💡 Recomendações

### 1. Começar com Pares Principais
```
RECOMENDADOS PARA COMEÇAR:
├── ITUB4 ↔ ITSA4  (Bancos - alta liquidez)
├── VALE3 ↔ CSNA3  (Minério - muito correlacionado)
├── ELET3 ↔ ELET6  (Mesmo ativo - ON/PN)
├── CPLE3 ↔ CPLE6  (Mesmo ativo - ON/PN)
└── TIMS3 ↔ VIVT3  (Telecom - correlacionados)
```

### 2. Evitar Initially
```
CUIDADO COM:
├── MOVI3 ↔ RENT3  (Setores diferentes)
├── Pares com volumes baixos
└── Pares que não passarem validação de cointegração
```

### 3. Otimização
```
Para melhor performance:
├── Usar apenas pares cointegrados (confirmado)
├── Monitorar correlação intra-dia
├── Ajustar Z-score thresholds por par
└── Implementar stop-loss agressivo
```

---

## 📊 Próximas Ações

1. ✅ **Carregar dados** - FEITO ✓
2. ⏳ **Validar cointegração** - Execute `integrate_acoes.py`
3. ⏳ **Configurar Orchestrator** - Será automático após validação
4. ⏳ **Iniciar monitoramento** - `await orchestrator.start()`
5. ⏳ **Executar primeiro trade** - Quando oportunidade detectada
6. ⏳ **Gerar relatórios** - Diários/Semanais

---

## 📁 Arquivos Criados

```
pairs-trading-system/
├── load_acoes.py           ← Carrega Excel
├── integrate_acoes.py      ← Integra com Orchestrator
├── pares_validados.csv     ← Resultado da validação
└── config_pares.json       ← Configuração final
```

---

**Status: 🟡 PRONTO PARA VALIDAÇÃO E INTEGRAÇÃO**

Próxima etapa: Executar `integrate_acoes.py` para validar todos os pares!
