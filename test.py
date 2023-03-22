from datamodel import Listing, OrderDepth, Trade, TradingState, Order
from trader import Trader

timestamp = 1000

listings = {
	"PEARLS": Listing(
		"PEARLS", 
		"PEARLS", 
		"SEASHELLS"
	),
	"BANANAS": Listing(
		"BANANAS", 
		"BANANAS", 
		"SEASHELLS"
	),
}

order_depths = {
	"PEARLS": OrderDepth(),
	"BANANAS": OrderDepth(),	
}

order_depths["PEARLS"].buy_orders = {9998: 7, 9997: 5}
order_depths["PEARLS"].sell_orders = {10001: -4, 10002: -8}
order_depths["BANANAS"].buy_orders = {5000: 10, 4999: 5}
order_depths["BANANAS"].sell_orders = {5007: -5, 5008: -8}
	

own_trades = {
	"PEARLS": [],
	"BANANAS": []
}

market_trades = {
	"PEARLS": [
		Trade(
			symbol="PEARLS",
			price=11,
			quantity=4,
			buyer="",
			seller="",
			timestamp=900
		)
	],
	"BANANAS": []
}

position = {
	"PEARLS": 18,
	"BANANAS": -5
}

observations = {}

state = TradingState(
	timestamp,
    listings,
	order_depths,
	own_trades,
	market_trades,
    position,
    observations
)

print(Trader().run(state))