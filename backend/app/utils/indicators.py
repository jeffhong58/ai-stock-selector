"""
技術指標計算模組
實現各種技術分析指標的計算
"""

import numpy as np
import pandas as pd
import talib
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技術指標計算器"""
    
    def __init__(self):
        self.indicators_cache = {}
    
    def calculate_ma(self, prices: List[float], period: int) -> List[float]:
        """計算移動平均線 (MA)"""
        if len(prices) < period:
            return [None] * len(prices)
        
        try:
            prices_array = np.array(prices, dtype=float)
            ma = talib.SMA(prices_array, timeperiod=period)
            return ma.tolist()
        except Exception as e:
            logger.error(f"計算MA失敗: {e}")
            return [None] * len(prices)
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """計算指數移動平均線 (EMA)"""
        if len(prices) < period:
            return [None] * len(prices)
        
        try:
            prices_array = np.array(prices, dtype=float)
            ema = talib.EMA(prices_array, timeperiod=period)
            return ema.tolist()
        except Exception as e:
            logger.error(f"計算EMA失敗: {e}")
            return [None] * len(prices)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """計算相對強弱指標 (RSI)"""
        if len(prices) < period:
            return [None] * len(prices)
        
        try:
            prices_array = np.array(prices, dtype=float)
            rsi = talib.RSI(prices_array, timeperiod=period)
            return rsi.tolist()
        except Exception as e:
            logger.error(f"計算RSI失敗: {e}")
            return [None] * len(prices)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """計算MACD指標"""
        if len(prices) < slow:
            return {
                'macd': [None] * len(prices),
                'signal': [None] * len(prices),
                'histogram': [None] * len(prices)
            }
        
        try:
            prices_array = np.array(prices, dtype=float)
            macd, signal_line, histogram = talib.MACD(
                prices_array, 
                fastperiod=fast, 
                slowperiod=slow, 
                signalperiod=signal
            )
            
            return {
                'macd': macd.tolist(),
                'signal': signal_line.tolist(),
                'histogram': histogram.tolist()
            }
        except Exception as e:
            logger.error(f"計算MACD失敗: {e}")
            return {
                'macd': [None] * len(prices),
                'signal': [None] * len(prices),
                'histogram': [None] * len(prices)
            }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std: float = 2.0) -> Dict:
        """計算布林帶 (Bollinger Bands)"""
        if len(prices) < period:
            return {
                'upper': [None] * len(prices),
                'middle': [None] * len(prices),
                'lower': [None] * len(prices)
            }
        
        try:
            prices_array = np.array(prices, dtype=float)
            upper, middle, lower = talib.BBANDS(
                prices_array, 
                timeperiod=period, 
                nbdevup=std, 
                nbdevdn=std
            )
            
            return {
                'upper': upper.tolist(),
                'middle': middle.tolist(),
                'lower': lower.tolist()
            }
        except Exception as e:
            logger.error(f"計算布林帶失敗: {e}")
            return {
                'upper': [None] * len(prices),
                'middle': [None] * len(prices),
                'lower': [None] * len(prices)
            }
    
    def calculate_stochastic(self, high_prices: List[float], low_prices: List[float], 
                           close_prices: List[float], k_period: int = 14, d_period: int = 3) -> Dict:
        """計算KD隨機指標"""
        if len(high_prices) < k_period:
            return {
                'k': [None] * len(close_prices),
                'd': [None] * len(close_prices)
            }
        
        try:
            high_array = np.array(high_prices, dtype=float)
            low_array = np.array(low_prices, dtype=float)
            close_array = np.array(close_prices, dtype=float)
            
            k, d = talib.STOCH(
                high_array, low_array, close_array,
                fastk_period=k_period,
                slowk_period=d_period,
                slowd_period=d_period
            )
            
            return {
                'k': k.tolist(),
                'd': d.tolist()
            }
        except Exception as e:
            logger.error(f"計算KD指標失敗: {e}")
            return {
                'k': [None] * len(close_prices),
                'd': [None] * len(close_prices)
            }
    
    def calculate_volume_ma(self, volumes: List[int], period: int) -> List[float]:
        """計算成交量移動平均"""
        if len(volumes) < period:
            return [None] * len(volumes)
        
        try:
            volumes_array = np.array(volumes, dtype=float)
            volume_ma = talib.SMA(volumes_array, timeperiod=period)
            return volume_ma.tolist()
        except Exception as e:
            logger.error(f"計算成交量MA失敗: {e}")
            return [None] * len(volumes)
    
    def calculate_support_resistance(self, high_prices: List[float], low_prices: List[float], 
                                   close_prices: List[float], period: int = 20) -> Dict:
        """計算支撐壓力位"""
        if len(close_prices) < period:
            return {
                'support': [None] * len(close_prices),
                'resistance': [None] * len(close_prices)
            }
        
        try:
            support_levels = []
            resistance_levels = []
            
            for i in range(len(close_prices)):
                if i < period - 1:
                    support_levels.append(None)
                    resistance_levels.append(None)
                    continue
                
                # 取最近period天的資料
                recent_highs = high_prices[i-period+1:i+1]
                recent_lows = low_prices[i-period+1:i+1]
                
                # 支撐位：最近期間的最低點
                support = min(recent_lows)
                
                # 壓力位：最近期間的最高點
                resistance = max(recent_highs)
                
                support_levels.append(support)
                resistance_levels.append(resistance)
            
            return {
                'support': support_levels,
                'resistance': resistance_levels
            }
        except Exception as e:
            logger.error(f"計算支撐壓力位失敗: {e}")
            return {
                'support': [None] * len(close_prices),
                'resistance': [None] * len(close_prices)
            }
    
    def calculate_price_momentum(self, prices: List[float], period: int = 10) -> List[float]:
        """計算價格動能"""
        if len(prices) < period:
            return [None] * len(prices)
        
        try:
            momentum = []
            for i in range(len(prices)):
                if i < period:
                    momentum.append(None)
                else:
                    current_price = prices[i]
                    past_price = prices[i - period]
                    if past_price != 0:
                        momentum_value = ((current_price - past_price) / past_price) * 100
                        momentum.append(momentum_value)
                    else:
                        momentum.append(None)
            
            return momentum
        except Exception as e:
            logger.error(f"計算價格動能失敗: {e}")
            return [None] * len(prices)
    
    def calculate_volume_ratio(self, volumes: List[int], period: int = 5) -> List[float]:
        """計算量比"""
        try:
            volume_ma = self.calculate_volume_ma(volumes, period)
            volume_ratio = []
            
            for i, current_volume in enumerate(volumes):
                if volume_ma[i] is not None and volume_ma[i] != 0:
                    ratio = current_volume / volume_ma[i]
                    volume_ratio.append(ratio)
                else:
                    volume_ratio.append(None)
            
            return volume_ratio
        except Exception as e:
            logger.error(f"計算量比失敗: {e}")
            return [None] * len(volumes)
    
    def calculate_williams_r(self, high_prices: List[float], low_prices: List[float], 
                           close_prices: List[float], period: int = 14) -> List[float]:
        """計算威廉指標 (%R)"""
        if len(close_prices) < period:
            return [None] * len(close_prices)
        
        try:
            high_array = np.array(high_prices, dtype=float)
            low_array = np.array(low_prices, dtype=float)
            close_array = np.array(close_prices, dtype=float)
            
            willr = talib.WILLR(high_array, low_array, close_array, timeperiod=period)
            return willr.tolist()
        except Exception as e:
            logger.error(f"計算威廉指標失敗: {e}")
            return [None] * len(close_prices)
    
    def calculate_all_indicators(self, stock_data: Dict) -> Dict:
        """計算所有技術指標"""
        try:
            # 提取價格和成交量資料
            dates = stock_data.get('dates', [])
            open_prices = stock_data.get('open', [])
            high_prices = stock_data.get('high', [])
            low_prices = stock_data.get('low', [])
            close_prices = stock_data.get('close', [])
            volumes = stock_data.get('volume', [])
            
            if not close_prices:
                logger.error("無效的股票資料：缺少收盤價")
                return {}
            
            indicators = {}
            
            # 移動平均線
            indicators['ma_5'] = self.calculate_ma(close_prices, 5)
            indicators['ma_10'] = self.calculate_ma(close_prices, 10)
            indicators['ma_20'] = self.calculate_ma(close_prices, 20)
            indicators['ma_60'] = self.calculate_ma(close_prices, 60)
            indicators['ma_120'] = self.calculate_ma(close_prices, 120)
            indicators['ma_240'] = self.calculate_ma(close_prices, 240)
            
            # 指數移動平均線
            indicators['ema_12'] = self.calculate_ema(close_prices, 12)
            indicators['ema_26'] = self.calculate_ema(close_prices, 26)
            
            # RSI
            indicators['rsi_14'] = self.calculate_rsi(close_prices, 14)
            
            # MACD
            macd_data = self.calculate_macd(close_prices)
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']
            indicators['macd_histogram'] = macd_data['histogram']
            
            # 布林帶
            bb_data = self.calculate_bollinger_bands(close_prices)
            indicators['bb_upper'] = bb_data['upper']
            indicators['bb_middle'] = bb_data['middle']
            indicators['bb_lower'] = bb_data['lower']
            
            # KD指標
            if high_prices and low_prices:
                kd_data = self.calculate_stochastic(high_prices, low_prices, close_prices)
                indicators['k_value'] = kd_data['k']
                indicators['d_value'] = kd_data['d']
            
            # 成交量指標
            if volumes:
                indicators['volume_ma_5'] = self.calculate_volume_ma(volumes, 5)
                indicators['volume_ma_20'] = self.calculate_volume_ma(volumes, 20)
                indicators['volume_ratio'] = self.calculate_volume_ratio(volumes)
            
            # 支撐壓力位
            if high_prices and low_prices:
                sr_data = self.calculate_support_resistance(high_prices, low_prices, close_prices)
                indicators['support_level'] = sr_data['support']
                indicators['resistance_level'] = sr_data['resistance']
            
            # 價格動能
            indicators['price_momentum'] = self.calculate_price_momentum(close_prices)
            
            # 威廉指標
            if high_prices and low_prices:
                indicators['williams_r'] = self.calculate_williams_r(high_prices, low_prices, close_prices)
            
            # 添加日期資訊
            indicators['dates'] = dates
            
            return indicators
            
        except Exception as e:
            logger.error(f"計算技術指標失敗: {e}")
            return {}
    
    def get_latest_signals(self, indicators: Dict) -> Dict:
        """取得最新的技術信號"""
        try:
            signals = {
                'buy_signals': [],
                'sell_signals': [],
                'neutral_signals': [],
                'overall_signal': 'neutral'
            }
            
            # 檢查最新指標值
            latest_idx = -1
            
            # RSI信號
            rsi = indicators.get('rsi_14', [])
            if rsi and rsi[latest_idx] is not None:
                if rsi[latest_idx] < 30:
                    signals['buy_signals'].append('RSI超賣')
                elif rsi[latest_idx] > 70:
                    signals['sell_signals'].append('RSI超買')
                else:
                    signals['neutral_signals'].append('RSI中性')
            
            # MACD信號
            macd = indicators.get('macd', [])
            macd_signal = indicators.get('macd_signal', [])
            if macd and macd_signal and macd[latest_idx] is not None and macd_signal[latest_idx] is not None:
                if macd[latest_idx] > macd_signal[latest_idx]:
                    signals['buy_signals'].append('MACD黃金交叉')
                else:
                    signals['sell_signals'].append('MACD死亡交叉')
            
            # 移動平均線信號
            close_prices = indicators.get('close', [])
            ma_20 = indicators.get('ma_20', [])
            ma_60 = indicators.get('ma_60', [])
            
            if (close_prices and ma_20 and ma_60 and 
                ma_20[latest_idx] is not None and ma_60[latest_idx] is not None):
                
                current_price = close_prices[latest_idx]
                
                if current_price > ma_20[latest_idx] > ma_60[latest_idx]:
                    signals['buy_signals'].append('多頭排列')
                elif current_price < ma_20[latest_idx] < ma_60[latest_idx]:
                    signals['sell_signals'].append('空頭排列')
                else:
                    signals['neutral_signals'].append('均線糾結')
            
            # KD指標信號
            k_value = indicators.get('k_value', [])
            d_value = indicators.get('d_value', [])
            if k_value and d_value and k_value[latest_idx] is not None and d_value[latest_idx] is not None:
                if k_value[latest_idx] < 20 and d_value[latest_idx] < 20:
                    signals['buy_signals'].append('KD超賣')
                elif k_value[latest_idx] > 80 and d_value[latest_idx] > 80:
                    signals['sell_signals'].append('KD超買')
                else:
                    signals['neutral_signals'].append('KD中性')
            
            # 布林帶信號
            bb_upper = indicators.get('bb_upper', [])
            bb_lower = indicators.get('bb_lower', [])
            if (close_prices and bb_upper and bb_lower and 
                bb_upper[latest_idx] is not None and bb_lower[latest_idx] is not None):
                
                current_price = close_prices[latest_idx]
                
                if current_price <= bb_lower[latest_idx]:
                    signals['buy_signals'].append('價格觸及布林帶下軌')
                elif current_price >= bb_upper[latest_idx]:
                    signals['sell_signals'].append('價格觸及布林帶上軌')
                else:
                    signals['neutral_signals'].append('價格在布林帶內')
            
            # 判斷整體信號
            buy_count = len(signals['buy_signals'])
            sell_count = len(signals['sell_signals'])
            
            if buy_count > sell_count:
                signals['overall_signal'] = 'buy'
            elif sell_count > buy_count:
                signals['overall_signal'] = 'sell'
            else:
                signals['overall_signal'] = 'neutral'
            
            signals['signal_strength'] = abs(buy_count - sell_count)
            
            return signals
            
        except Exception as e:
            logger.error(f"取得技術信號失敗: {e}")
            return {
                'buy_signals': [],
                'sell_signals': [],
                'neutral_signals': [],
                'overall_signal': 'neutral',
                'signal_strength': 0
            }
    
    def calculate_indicator_for_date(self, stock_data: Dict, target_date: date) -> Dict:
        """計算指定日期的技術指標"""
        try:
            # 找到目標日期的索引
            dates = stock_data.get('dates', [])
            if target_date not in dates:
                return {}
            
            target_idx = dates.index(target_date)
            
            # 計算所有指標
            all_indicators = self.calculate_all_indicators(stock_data)
            
            # 提取目標日期的指標值
            indicators_for_date = {
                'trade_date': target_date
            }
            
            for key, values in all_indicators.items():
                if key != 'dates' and isinstance(values, list) and target_idx < len(values):
                    indicators_for_date[key] = values[target_idx]
            
            return indicators_for_date
            
        except Exception as e:
            logger.error(f"計算指定日期技術指標失敗: {e}")
            return {}


# 工具函數
def prepare_stock_data_for_indicators(price_records: List) -> Dict:
    """準備股票資料用於指標計算"""
    try:
        if not price_records:
            return {}
        
        # 按日期排序
        sorted_records = sorted(price_records, key=lambda x: x.trade_date)
        
        data = {
            'dates': [record.trade_date for record in sorted_records],
            'open': [float(record.open_price) for record in sorted_records],
            'high': [float(record.high_price) for record in sorted_records],
            'low': [float(record.low_price) for record in sorted_records],
            'close': [float(record.close_price) for record in sorted_records],
            'volume': [int(record.volume) for record in sorted_records]
        }
        
        return data
        
    except Exception as e:
        logger.error(f"準備股票資料失敗: {e}")
        return {}


def validate_indicator_data(data: Dict) -> bool:
    """驗證指標計算所需資料"""
    required_fields = ['close']
    optional_fields = ['open', 'high', 'low', 'volume', 'dates']
    
    # 檢查必要欄位
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    
    # 檢查資料長度一致性
    base_length = len(data['close'])
    for field in optional_fields:
        if field in data and data[field]:
            if len(data[field]) != base_length:
                return False
    
    return True


# 預設技術指標計算器實例
default_calculator = TechnicalIndicators()