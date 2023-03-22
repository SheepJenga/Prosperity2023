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
            'PEARLS': Queue(100, 10000),
            'BANANAS': Queue(50, 5000)
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
            bid1, bid2, ask1, ask2 = prices[0], prices[1], prices[2], prices[3]
            bid_vol, ask_vol = 0, 0
            if bid1: 
                bid_vol = (bid1 + bid2) if bid2 else bid1
            if ask1: 
                ask_vol = (ask1 + ask2) if ask2 else ask1
            self.depth_imbalance[product] = ((bid_vol - ask_vol) / (bid_vol + ask_vol)) if (bid_vol - ask_vol) else 0
        

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
                        min1, min2 = price, max1
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
        aggregate_buy = state.position[product]
        aggregate_sell = state.position[product]
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
        self.update()

        # Initialize the method output dict as an empty dict
        result = {}

        for product in state.order_depths:
            remaining_buy, remaining_sell = self.get_remaining_buy_sell(state, product)
            orders = []
            stats = self.product_data[product]
            order_depth = state.order_depths[product]

            if product == 'PEARLS':
                if remaining_buy:
                    price = stats.mean - math.sqrt(stats.get_var() / 2)
                    print("BUY", str(remaining_buy) + "x", price)
                    orders.append(Order(product, price, remaining_buy))
                if remaining_sell:
                    price = stats.mean + math.sqrt(stats.get_var() / 2)
                    print("SELL", str(remaining_sell) + "x", price)
                    orders.append(Order(product, price, remaining_sell))

                result[product] = orders

            elif product == 'BANANAS':
                if self.depth_imbalance[product] > 0.7 and remaining_buy: # high positive imbalance, large likelihood prices will increase, higher demand than supply, buy as much as possible as this is peak low, BUY LOW
                    price = self.product_data[product].mean # moving average: approximate the price at the current "dip" 
                    print("BUY", str(remaining_buy) + "x", price)
                    orders.append(Order(product, price, remaining_buy))
                elif self.depth_imbalance[product] < 0.3 and remaining_sell: # highly negative imbalance, likely prices will decrease, time to sell SELL HIGH
                    price = self.product_data[product].mean # moving average: approximate the price at the current "peak"
                    print("SELL", str(remaining_sell) + "x", price)
                    orders.append(Order(product, price, remaining_sell))
                
                result[product] = orders

            # # Initialize the list of Orders to be sent as an empty list
            # orders: list[Order] = []

            # # Define a fair value for the PEARLS.
            # # Note that this value of 1 is just a dummy value, you should likely change it!
            # # acceptable_price = 10

            # # If statement checks if there are any SELL orders in the PEARLS market
            # if len(order_depth.sell_orders) > 0:

            #     # Sort all the available sell orders by their price,
            #     # and select only the sell order with the lowest price
            #     best_ask = min(order_depth.sell_orders.keys())
            #     best_ask_volume = order_depth.sell_orders[best_ask]

            #     # Check if the lowest ask (sell order) is lower than the above defined fair value
            #     if best_ask < acceptable_prices[product]:

            #         # In case the lowest ask is lower than our fair value,
            #         # This presents an opportunity for us to buy cheaply
            #         # The code below therefore sends a BUY order at the price level of the ask,
            #         # with the same quantity
            #         # We expect this order to trade with the sell order
            #         acceptable_prices[product] = 0.7 * acceptable_prices[product] + 0.3 * best_ask
            #         print("BUY", str(-best_ask_volume) + "x", best_ask)
            #         orders.append(Order(product, best_ask, -best_ask_volume))

            # # The below code block is similar to the one above,
            # # the difference is that it find the highest bid (buy order)
            # # If the price of the order is higher than the fair value
            # # This is an opportunity to sell at a premium
            # if len(order_depth.buy_orders) != 0:
            #     best_bid = max(order_depth.buy_orders.keys())
            #     best_bid_volume = order_depth.buy_orders[best_bid]
            #     if best_bid > acceptable_prices[product]:
            #         acceptable_prices[product] = 0.55 * acceptable_prices[product] + 0.45 * best_bid
            #         print("SELL", str(best_bid_volume) + "x", best_bid)
            #         orders.append(Order(product, best_bid, -best_bid_volume))

            # # Add all the above the orders to the result dict
            # result[product] = orders

            #     # Return the dict of orders
            #     # These possibly contain buy or sell orders for PEARLS
            #     # Depending on the logic above
        return result

class Queue:
    def __init__(self, size, init_val):
        self.n = size
        self.head = 0
        self.data = [init_val for _ in range(size)]
        self.mean = init_val
        self.var = 0

    def enque(self, val):
        self.head = (self.head + 1) % self.size
        prev_mean = self.mean
        old_val = self.data[self.head]
        self.mean += (val - old_val) / self.n
        self.var += ((val - prev_mean) * (val - self.mean) - (old_val - prev_mean) * (old_val - self.mean)) / self.n
        self.data[self.head] = val 

    def get_mean(self):
        return self.mean
    
    def get_var(self):
        return self.var