from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import statistics
import math
import pandas as pd
import numpy as np

class Trader:
    def __init__(self) -> None:
        self.depth_imbalance = {}
        self.product_data = {
            'PEARLS': Queue(160, 10000),
            'BANANAS': Queue(60, 5000)
        }
    
    
    def update(self, order_depths):
        """
        updates state of Trader (depth imbalance, moving average, moving variance)
        """
        level_two_depths = self.get_level_two_depth(order_depths)

        for product in order_depths:
            #Updating product data containing window of recent prices
            q = self.product_data[product]
            prices = level_two_depths[product]
            for price in prices:
                if price: 
                    q.enque(price)
            #Updating depth imbalance
            order_depth = order_depths[product]
            bid1, bid2, ask1, ask2 = prices[0], prices[1], prices[2], prices[3]
            bid_vol, ask_vol = 0, 0
            if bid1: 
                bid_vol = (order_depth.buy_orders[bid1] + order_depth.buy_orders[bid2]) if bid2 else order_depth.buy_orders[bid1]
            if ask1: 
                ask_vol = (-order_depth.sell_orders[ask1] - order_depth.sell_orders[ask2]) if ask2 else -order_depth.sell_orders[ask1]
            self.depth_imbalance[product] = ((bid_vol - ask_vol) / (bid_vol + ask_vol)) if (bid_vol + ask_vol) else 0
        

    def get_level_two_depth(self, order_depths):
        """
        Gets 2 min asks and 2 max bids, returns in format dict: PRODUCT -> (max bid1, max bid2, max ask1, max ask2)
        """
        #best_ask = min(order_depth.sell_orders.keys())
        min_and_max = {}
        for product in order_depths:
            order_depth = order_depths[product]
            
            max1, max2 = 0, 0
            for price in order_depth.buy_orders:
                if price > max2:
                    if price > max1:
                        max1, max2 = price, max1
                    else:
                        max2 = price

            min1, min2 = float('inf'), float('inf')
            for price in order_depth.sell_orders:
                if price < min2:
                    if price < min1:
                        min1, min2 = price, min1
                    else:
                        min2 = price
        
            if min2 == float('inf'):
                if min1 == float('inf'):
                    min1, min2 = None, None
                min2 = None

            if max2 == 0:
                if max1 == 0:
                    max1, max2 = None, None
                max2 = None

            min_and_max[product] = (max1, max2, min1, min2)
        return min_and_max


    def get_remaining_buy_sell(self, state, product):
        """
        returns the remaining buy sell available based on a trading state for a given product
        as (remaining_buy, remaining_sell)
        """
        if product not in state.position:
            return (20, -20) 
        
        aggregate_buy = aggregate_sell = state.position[product]
        if product in state.own_trades:
            for trade in state.own_trades[product]:
                if trade.quantity >= 0:
                    aggregate_buy += trade.quantity
                else:
                    aggregate_sell += trade.quantity
        return (20 - aggregate_buy, -aggregate_sell - 20)
            

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """

        """
        Strategy:

        1) get fair value
            bananas: moving average? = fair value
            pearls: trade around (average +/- variance)
        2) send trade orders:
            sell order: if exists buy order > fair value
            buy order: if exists sell order < fair value
        """
        self.update(state.order_depths)

        # Initialize the method output dict as an empty dict
        result = {}

        for product in state.order_depths:
            remaining_buy, remaining_sell = self.get_remaining_buy_sell(state, product)
            orders = []
            stats = self.product_data[product]

            if product == 'PEARLS':
                if remaining_buy:
                    price = stats.mean - math.sqrt(stats.get_var() / 3)
                    print(price)
                    print("BUY", str(remaining_buy) + "x", price)
                    orders.append(Order(product, price, remaining_buy))

                if remaining_sell:
                    price = stats.mean + math.sqrt(stats.get_var() / 3)
                    print(price)
                    print("SELL", str(remaining_sell) + "x", price)
                    orders.append(Order(product, price, remaining_sell))

            elif product == 'BANANAS':
                #### STRATEGY: USE RATE OF CHANGE OF MOVING AVG TO ESTIMATE INCREASE/DECREASE OF PRICE ####
                # if remaining_buy and stats.avg_change > 0: # price start to increase: buy
                #     price = stats.mean
                #     print("BUY", str(remaining_buy) + "x", price)
                #     orders.append(Order(product, price, remaining_buy))
                # if remaining_sell and stats.avg_change < 0: # price start to decrease: sell
                #     price = stats.mean
                #     print("SELL", str(remaining_sell) + "x", price)
                #     orders.append(Order(product, price, remaining_sell))

                #### STRATEGY: LARGER DI LARGER THRESHOLD ####
                # scaling_factor = 1
                # DI = self.depth_imbalance[product]
                # if DI > 0.4:
                #     scaling_factor = 1 + 0.2 * (DI - 0.4)
                # elif DI < -0.4:
                #     scaling_factor = 1 + 0.2 * (DI + 0.4)
                
                # if remaining_buy:
                #     price =  - scaling_factor * math.sqrt(stats.get_var() / 2)
                #     print("BUY", str(remaining_buy) + "x", price)
                #     orders.append(Order(product, price, remaining_buy))

                # if remaining_sell:
                #     price = stats.mean + 1 / scaling_factor * math.sqrt(stats.get_var() / 2)
                #     print("SELL", str(remaining_sell) + "x", price)
                #     orders.append(Order(product, price, remaining_sell))

                #### STRATEGY: DI IS INDICATOR FOR RATE OF CHANGE ####
                if self.depth_imbalance[product] >= 0.5 and remaining_buy: # high positive imbalance, large likelihood prices will increase, higher demand than supply, buy as much as possible as this is peak low, BUY LOW
                    price = self.product_data[product].mean - stats.get_var() * 0.15# moving average: approximate the price at the current "dip" 
                    print("BUY", str(remaining_buy) + "x", price)
                    orders.append(Order(product, price, remaining_buy))
                elif self.depth_imbalance[product] <= -0.5 and remaining_sell: # highly negative imbalance, likely prices will decrease, time to sell SELL HIGH
                    price = self.product_data[product].mean + stats.get_var() * 0.15 # moving average: approximate the price at the current "peak"
                    print("SELL", str(remaining_sell) + "x", price)
                    orders.append(Order(product, price, remaining_sell))
                
            result[product] = orders

        return result

class Queue:
    def __init__(self, size, init_val):
        self.n = size
        self.head = 0
        self.data = [init_val for _ in range(size)]
        self.mean = init_val
        self.var = 2

        self.avg_change = 0
        self.prev_change = 0

    def enque(self, val):
        self.head = (self.head + 1) % self.n
        prev_mean = self.mean
        old_val = self.data[self.head]
        self.mean += (val - old_val) / self.n
        self.var += ((val - prev_mean) * (val - self.mean) - (old_val - prev_mean) * (old_val - self.mean)) / self.n
        self.data[self.head] = val 

        new_change = self.avg_change + ((self.mean - prev_mean) - self.prev_change) / self.n
        self.prev_change = (self.mean - prev_mean)
        self.avg_change = new_change

    def get_mean(self):
        return self.mean
    
    def get_var(self):
        return self.var