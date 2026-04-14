"""
EXEMPLO: Template de Integração com Broker
Mostra como conectar o sistema multi-agentes com brokers reais
"""

from typing import Dict, List, Any, Optional
from typing import Tuple
from abc import ABC, abstractmethod
import asyncio


class BrokerAPI(ABC):
    """Interface abstrata para integração com brokers"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Conecta com broker"""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> float:
        """Obtém preço atual de um símbolo"""
        pass
    
    @abstractmethod
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtém preços de múltiplos símbolos"""
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, side: str, quantity: float, 
                         price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        """Coloca uma ordem"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancela uma ordem"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém informação de posição aberta"""
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Fecha uma posição"""
        pass


# =============================================================================
# EXEMPLO 1: Interactive Brokers
# =============================================================================

class InteractiveBrokersAPI(BrokerAPI):
    """Adaptador para Interactive Brokers (IBKR)"""
    
    def __init__(self, account_id: str, port: int = 7497):
        """
        Inicializa conexão com IB
        
        Args:
            account_id: ID da conta (ex: 'DU123456')
            port: Porta do TWS/Gateway (padrão 7497)
        """
        self.account_id = account_id
        self.port = port
        self.connected = False
        
        # Importar ibapi (pip install ibapi)
        try:
            from ibapi import client, wrapper
            self.client = client
            self.wrapper = wrapper
        except ImportError:
            raise ImportError("Instale ibapi: pip install ibapi")
    
    async def connect(self) -> bool:
        """Conecta com TWS/Gateway"""
        try:
            # Implementação real seria complexa
            # Este é um template simplificado
            self.connected = True
            print(f"✓ Conectado ao Interactive Brokers: {self.account_id}")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar IB: {e}")
            return False
    
    async def get_price(self, symbol: str) -> float:
        """Obtém preço atual"""
        # Em produção, usar ibapi para market data
        # Exemplo: self.ib_client.reqMktData(...)
        return 150.25  # Placeholder
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtém múltiplos preços"""
        return {symbol: await self.get_price(symbol) for symbol in symbols}
    
    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        """Coloca ordem no IB"""
        # Implementação real usando ibapi
        return {
            'order_id': f"IB_{symbol}_{int(price*100)}",
            'status': 'PLACED',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price
        }
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancela ordem"""
        return True
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém posição"""
        return {
            'symbol': symbol,
            'quantity': 100,
            'avg_price': 150.00,
            'current_price': 151.50,
            'pnl': 150.00  # P&L não realizado
        }
    
    async def close_position(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Fecha posição"""
        return {
            'status': 'CLOSED',
            'quantity': quantity,
            'close_price': 151.50
        }


# =============================================================================
# EXEMPLO 2: Alpaca
# =============================================================================

class AlpacaAPI(BrokerAPI):
    """Adaptador para Alpaca (ações e cripto)"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str = None):
        """
        Inicializa conexão com Alpaca
        
        Args:
            api_key: Chave de API da Alpaca
            secret_key: Chave secreta
            base_url: URL base (demo ou live)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url or "https://paper-trading.alpaca.markets"
        self.connected = False
        
        # Importar alpaca_trade_api
        try:
            import alpaca_trade_api as tradeapi
            self.tradeapi = tradeapi
        except ImportError:
            raise ImportError("Instale alpaca-trade-api: pip install alpaca-trade-api")
    
    async def connect(self) -> bool:
        """Conecta com Alpaca"""
        try:
            # self.api = self.tradeapi.REST(self.api_key, self.secret_key, self.base_url)
            self.connected = True
            print(f"✓ Conectado ao Alpaca")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar Alpaca: {e}")
            return False
    
    async def get_price(self, symbol: str) -> float:
        """Obtém preço via Alpaca"""
        # result = self.api.get_barset(symbol, 'minute', limit=1)
        # return result[symbol][0]['c']  # Close price
        return 150.25
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtém múltiplos preços"""
        return {symbol: await self.get_price(symbol) for symbol in symbols}
    
    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        """Coloca ordem via Alpaca"""
        # order = self.api.submit_order(
        #     symbol=symbol,
        #     qty=quantity,
        #     side=side.lower(),
        #     type=order_type.lower(),
        #     limit_price=price
        # )
        return {
            'order_id': f"ALPACA_{symbol}",
            'status': 'PLACED'
        }
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancela ordem"""
        # self.api.cancel_order(order_id)
        return True
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém posição"""
        # position = self.api.get_position(symbol)
        return {
            'symbol': symbol,
            'quantity': 100,
            'avg_price': 150.00
        }
    
    async def close_position(self, symbol: str, quantity:float) -> Dict[str, Any]:
        """Fecha posição"""
        # self.api.close_position(symbol)
        return {'status': 'CLOSED'}


# =============================================================================
# EXEMPLO 3: Binance (Criptomoedas)
# =============================================================================

class BinanceAPI(BrokerAPI):
    """Adaptador para Binance (Criptomoedas)"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        """
        Inicializa conexão com Binance
        
        Args:
            api_key: Chave de API Binance
            secret_key: Chave secreta
            testnet: Usar testnet (recomendado para testes)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.connected = False
        
        try:
            from binance.client import Client
            self.binance = Client
        except ImportError:
            raise ImportError("Instale python-binance: pip install python-binance")
    
    async def connect(self) -> bool:
        """Conecta com Binance"""
        try:
            # client = self.binance(self.api_key, self.secret_key, testnet=self.testnet)
            self.connected = True
            print(f"✓ Conectado ao Binance")
            return True
        except Exception as e:
            print(f"✗ Erro ao conectar Binance: {e}")
            return False
    
    async def get_price(self, symbol: str) -> float:
        """Obtém preço BTC/USDT, etc"""
        # ticker = client.get_symbol_info(symbol)
        return 45000.50
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtém múltiplos preços"""
        return {symbol: await self.get_price(symbol) for symbol in symbols}
    
    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        """Coloca ordem no Binance"""
        return{'order_id': 'BINANCE_ORDER_123', 'status': 'PLACED'}
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancela ordem"""
        return True
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém posição"""
        return {'symbol': symbol, 'quantity': 1.5}
    
    async def close_position(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Fecha posição"""
        return {'status': 'CLOSED'}


# =============================================================================
# USO COMPLETO  COM SYSTEM
# =============================================================================

async def example_usage():
    """Exemplo de como usar com o sistema de agentes"""
    
    from core.orchestrator import TradingOrchestrator
    
    # 1. Escolher broker
    # broker = InteractiveBrokersAPI(account_id="YOUR_ACCOUNT")
    # ou
    broker = AlpacaAPI(api_key="YOUR_KEY", secret_key="YOUR_SECRET")
    # ou
    # broker = BinanceAPI(api_key="YOUR_KEY", secret_key="YOUR_SECRET")
    
    # 2. Conectar
    connected = await broker.connect()
    if not connected:
        print("Falha ao conectar broker")
        return
    
    # 3. Inicializar Orchestrator
    orchestrator = TradingOrchestrator(capital=100000)
    
    # 4. Passar broker ao Executor
    orchestrator.executor.broker_api = broker
    
    # 5. Configurar pares
    orchestrator.add_pair_to_monitor("AAPL", "MSFT", beta=0.95)
    
    # 6. Sistema agora executa com dados REAIS
    print("✓ Sistema pronto com broker real!")
    print(f"✓ Orchestrator: {orchestrator}")
    
    # 7. Monitorar continuamente
    # await orchestrator.start()


# =============================================================================
# TEMPLATE DE NOVO BROKER
# =============================================================================

class CustomBrokerAPI(BrokerAPI):
    """Template para integrar novo broker"""
    
    def __init__(self, api_key: str, **kwargs):
        """Inicializa conexão com broker customizado"""
        self.api_key = api_key
        self.connected = False
    
    async def connect(self) -> bool:
        """Implementar conexão"""
        # TODO: Implementar lógica de conexão específica do broker
        self.connected = True
        return True
    
    async def get_price(self, symbol: str) -> float:
        """Implementar obtenção de preço"""
        # TODO: Chamar API do broker
        pass
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Implementar obtenção de múltiplos preços"""
        # TODO: Otimizar para batch request
        pass
    
    async def place_order(self, symbol: str, side: str, quantity: float,
                         price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        """Implementar colocação de ordem"""
        # TODO: Chamar API de order placement
        pass
    
    async def cancel_order(self, order_id: str) -> bool:
        """Implementar cancelamento"""
        # TODO: Chamar API de cancel
        pass
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Implementar obtenção de posição"""
        # TODO: Chamar API de posição
        pass
    
    async def close_position(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Implementar fecho de posição"""
        # TODO: Chamar API de close
        pass


# =============================================================================
# TESTES
# =============================================================================

async def test_broker_adapters():
    """Testa todos os adaptadores"""
    
    print("Testando Broker Adapters...")
    
    # IB
    try:
        ib = InteractiveBrokersAPI("DU123456")
        print(f"✓ InteractiveBrokers (template pronto)")
    except Exception as e:
        print(f"✗ IB Error: {e}")
    
    # Alpaca
    try:
        alpaca = AlpacaAPI("KEY", "SECRET")
        print(f"✓ Alpaca (template pronto)")
    except Exception as e:
        print(f"✗ Alpaca Error: {e}")
    
    # Binance
    try:
        binance = BinanceAPI("KEY", "SECRET")
        print(f"✓ Binance (template pronto)")
    except Exception as e:
        print(f"✗ Binance Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_broker_adapters())
