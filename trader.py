from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import statistics
import math
import pandas as pd
import numpy as np

class Trader:
    def __init__(self) -> None:
        self.data = []
        self.t = 0
        self.acceptable_prices = {}
        self.depth_imbalance = {}
        self.product_data = {
            'PEARLS': Queue(100, 10000),
            'BANANAS': Queue(50, 5000)
        }
    
    
    def update(self, order_depths, ):
        """
        Calls get_level_two_depth for dict: PRODUCT -> (max bid1, max bid2, max ask1, max ask2)
        """    
        level_two_depths = self.get_level_two_depth(order_depths)

        for product in order_depths:
            #Updating product data containing window of recent prices
            q = self.product_data[product]
            prices = level_two_depths[product]
            for price in prices:
                if price:
                    q.enque(price)
            #Updating depth imbalance - TODO
            
            
        

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


    def update_prices(self, order_depths):
        p = 0.7
        for product in order_depths:
            order_depth = order_depths[product]
            min_ask = min(order_depth.sell_orders.keys())
            max_bid = max(order_depth.buy_orders.keys())
            self.acceptable_prices[product] = p * self.acceptable_prices[product] + (1 - p) * 0.5 * (min_ask + max_bid)
    
    def update_depth_imbalance(self, order_depths):
        for product in order_depths:
            prev_DI, prev_BV, prev_AV = self.depth_imbalance[product]
            order_depth = order_depths[product]

            new_BV = prev_BV + TODO
            new_AV = prev_AV + TODO
            new_DI = (new_BV - new_AV) / (new_BV + new_AV)

            self.depth_imbalance[product] = new_DI, new_BV, new_AV
            
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
        self.t += 1
        self.update_depth_imbalance()

        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order dephts
        for product in state.order_depths:
            if product == 'PEARLS':







            # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
            order_depth: OrderDepth = state.order_depths[product]

            # Initialize the list of Orders to be sent as an empty list
            orders: list[Order] = []

            # Define a fair value for the PEARLS.
            # Note that this value of 1 is just a dummy value, you should likely change it!
            # acceptable_price = 10

            # If statement checks if there are any SELL orders in the PEARLS market
            if len(order_depth.sell_orders) > 0:

                # Sort all the available sell orders by their price,
                # and select only the sell order with the lowest price
                best_ask = min(order_depth.sell_orders.keys())
                best_ask_volume = order_depth.sell_orders[best_ask]

                # Check if the lowest ask (sell order) is lower than the above defined fair value
                if best_ask < acceptable_prices[product]:

                    # In case the lowest ask is lower than our fair value,
                    # This presents an opportunity for us to buy cheaply
                    # The code below therefore sends a BUY order at the price level of the ask,
                    # with the same quantity
                    # We expect this order to trade with the sell order
                    acceptable_prices[product] = 0.7 * acceptable_prices[product] + 0.3 * best_ask
                    print("BUY", str(-best_ask_volume) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_volume))

            # The below code block is similar to the one above,
            # the difference is that it find the highest bid (buy order)
            # If the price of the order is higher than the fair value
            # This is an opportunity to sell at a premium
            if len(order_depth.buy_orders) != 0:
                best_bid = max(order_depth.buy_orders.keys())
                best_bid_volume = order_depth.buy_orders[best_bid]
                if best_bid > acceptable_prices[product]:
                    acceptable_prices[product] = 0.55 * acceptable_prices[product] + 0.45 * best_bid
                    print("SELL", str(best_bid_volume) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_volume))

            # Add all the above the orders to the result dict
            result[product] = orders

                # Return the dict of orders
                # These possibly contain buy or sell orders for PEARLS
                # Depending on the logic above
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