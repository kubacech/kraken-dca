#!/usr/bin/env python3
"""
Kraken API client handler
"""
import logging
from typing import Dict

import krakenex

logger = logging.getLogger(__name__)


class KrakenClient:
    """Handle Kraken API communication"""
    
    def __init__(self, api_key: str, private_key: str):
        """
        Initialize Kraken API client
        
        Args:
            api_key: Kraken API key
            private_key: Kraken private key
        """
        self.api = krakenex.API()
        self.api.key = api_key
        self.api.secret = private_key
    
    def get_ticker_price(self, trading_pair: str) -> float:
        """
        Get current price for a trading pair
        
        Args:
            trading_pair: Trading pair (e.g., 'XXBTZEUR')
            
        Returns:
            Current price as float
            
        Raises:
            Exception: If API call fails
        """
        try:
            ticker_data = self.api.query_public('Ticker', {'pair': trading_pair})
            
            if ticker_data['error']:
                raise Exception(f"Kraken API error: {ticker_data['error']}")
            
            # Get the current price (last trade price)
            price = float(ticker_data['result'][trading_pair]['c'][0])
            logger.info(f"Fetched price for {trading_pair}: {price}")
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {trading_pair}: {e}")
            raise
    
    def place_limit_order(
        self, 
        trading_pair: str, 
        order_type: str, 
        volume: float, 
        price: float,
        validate: bool = False
    ) -> Dict:
        """
        Place a limit order on Kraken
        
        Args:
            trading_pair: Trading pair (e.g., 'XXBTZEUR')
            order_type: 'buy' or 'sell'
            volume: Volume to trade
            price: Limit price
            validate: If True, validate order without placing it
            
        Returns:
            Dictionary containing order result with keys:
                - order_id: Order transaction ID
                - description: Order description
                
        Raises:
            Exception: If order placement fails
        """
        try:
            order_data = {
                'pair': trading_pair,
                'type': order_type,
                'ordertype': 'limit',
                'volume': f"{volume:.8f}",
                'price': f"{price:.1f}",
                'validate': 'true' if validate else 'false'
            }
            
            logger.info(f"Placing {order_type} order: {volume:.8f} at {price:.1f} for {trading_pair}")
            
            result = self.api.query_private('AddOrder', order_data)
            
            if result['error']:
                raise Exception(f"Order placement error: {result['error']}")
            
            logger.info(f"Order placed successfully: {result['result']}")
            
            return {
                'order_id': result['result']['txid'][0] if result['result']['txid'] else None,
                'description': result['result'].get('descr', {})
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets
        
        Returns:
            Dictionary mapping asset names to balances
            
        Raises:
            Exception: If API call fails
        """
        try:
            result = self.api.query_private('Balance')
            
            if result['error']:
                raise Exception(f"Balance query error: {result['error']}")
            
            balances = {asset: float(amount) for asset, amount in result['result'].items()}
            logger.info(f"Account balances retrieved: {len(balances)} assets")
            return balances
            
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            raise
    
    def get_order_info(self, txid: str) -> Dict:
        """
        Get information about a specific order
        
        Args:
            txid: Transaction ID of the order
            
        Returns:
            Dictionary containing order information
            
        Raises:
            Exception: If API call fails
        """
        try:
            result = self.api.query_private('QueryOrders', {'txid': txid})
            
            if result['error']:
                raise Exception(f"Order query error: {result['error']}")
            
            logger.info(f"Order info retrieved for {txid}")
            return result['result']
            
        except Exception as e:
            logger.error(f"Error fetching order info: {e}")
            raise

