#!/usr/bin/env python

# This script is meant to be used with bitcoin_fork_claimer: https://github.com/ymgve/bitcoin_fork_claimer
# The outputs of this script are the inputs to that script.
# Python 2.x is required

import urllib2
import json
import sys


# Insert your BTC addresses, one per line 

addresses = """
17U7b8NdUcNoMPmKwKLS4rwhtJoRN8F3PV
17U7b8NdUcNoMPmKwKLS4rwhtJoRN8F3PV
17U7b8NdUcNoMPmKwKLS4rwhtJoRN8F3PV


"""


# Forks to check. No need to touch, unless you want to add or remove a fork
fork_list = {
"BCH": { "name": "Bitcoin Cash", "block": 478559 },
"BCL": { "name": "Bitcoin Clashic", "block": 478559 },
"BEC": { "name": "Bitcoin Eco", "block": 500000 },
"GOD": { "name": "Bitcoin God", "block": 501225 },
"FBTC": { "name": "Fast Bitcoin", "block": 501225 },
"BCP": { "name": "Bitcoin Cash Plus", "block": 501407 },
"BCI": { "name": "Bitcoin Interest", "block": 505083 },
"BCA": { "name": "Bitcoin Atom", "block": 505888 },
"BBC": { "name": "Big Bitcoin", "block": 508888 },
"BCD": { "name": "Bitcoin Diamond", "block": 495866 },
"SBTC": { "name": "Super Bitcoin", "block": 498888 },
"BTG": { "name": "Bitcoin Gold", "block": 491407 },
"B2X": { "name": "Segwit2x", "block": 501451 },
"BCX": { "name": "BitcoinX", "block": 498888 },
"BTP": { "name": "BitcoinPay", "block": 499345},
"BTF": { "name": "Bitcoin Faith", "block": 500000 },
"BPA": { "name": "Bitcoin Pizza", "block": 501888},
"BTH": { "name": "Bitcoin Hot", "block": 498848 },
"BTN": { "name": "Bitcoin New", "block": 501000 },
"BTW": { "name": "Bitcoin World", "block": 499777 },
"BTV": { "name": "Bitcoin Vote", "block": 505050 },
"BTT": { "name": "Bitcoin Top", "block": 501118 },
"WBTC": { "name": "World Bitcoin", "block": 503888 },
"BTSQ": { "name": "Bitcoin Community", "block": 506066 },
"BICC": { "name": "BitClassic Coin", "block": 498888 },
"UBTC": { "name": "United Bitcoin", "block": 498777 },
"BTCP": { "name": "Bitcoin Private", "block": 511346 },
"LBTC": { "name": "Lightning Bitcoin", "block": 499999 },
"BCB": { "name": "Bitcoin Boy", "block": 501888 },
"NANO": { "name": "Bitcoin Nano", "block": 501888 },
"BCO": { "name": "Bitcoin Ore", "block": 501949 },
#"BTA": { "name": "Bitcoin ALL", "block":  },
"BPP": { "name": "Bitcoin Payment Performance", "block": 501888 },
"QBTC": { "name": "Quantum Bitcoin", "block": 501368 },
"BIFI": { "name": "BitcoinFile", "block": 501225 },
"BTCS": { "name": "Bitcoin Smart", "block": 499999 },
"BCK": { "name": "Bitcoin King", "block": 499999 },
"OBTC": { "name": "OilBTC", "block": 498888 },
"BCS": { "name": "Bitcoin Smart", "block": 505050 }
}

desired_forks = {}

def main():
	addr_list = addresses.strip().split("\n")
	addr_list = [addr.strip() for addr in addr_list]

	global desired_forks
	desired_forks = get_desired_forks()
	if len(desired_forks) == 0:
		print "Retrieving all forks..."
		print
		desired_forks = fork_list

	# Add balance entry per fork
	for coincode, coindata in desired_forks.viewitems():
		coindata["balances"] = {}
		for addr in addr_list:
			coindata["balances"][addr] = 0

	for addr in addr_list:
		a = urllib2.urlopen("https://blockchain.info/rawaddr/" + addr).read()
		txs = json.loads(a)["txs"]

		for coincode, coindata in desired_forks.viewitems():
			valid = process_txs(addr, txs, coindata)

			for value in valid:
				if not coindata.has_key("commands"):
					coindata["commands"] = []
				coindata["commands"].append("python claimer_1.py " + coincode + " " + " ".join(value) + " " + coincode + "_ADDR --force")

			coindata["total_value"] = sum(coindata["balances"].values())


	if not "-balance" in sys.argv:
		print_commands()
	print_balances()


def process_txs(addr, txs, coin):
	txs_before_fork = [tx for tx in txs if tx.has_key("block_height") and tx["block_height"] <= coin["block"]]
	valid_txs = txs_before_fork[:]
	valid = []

	# Remove spent transactions
	for txid in valid_txs[:]:
		for tx in txs_before_fork:
			tx_from_mining = tx["vin_sz"] == 1 and not tx["inputs"][0].has_key("prev_out")
			if tx_from_mining:
				continue
			for input_tx in tx["inputs"]:
				if input_tx["prev_out"]["tx_index"] == txid["tx_index"] and input_tx["prev_out"]["addr"] == addr:
					try:
						valid_txs.remove(txid)
					except ValueError:
						pass # Was probably removed before. Skipping.

	for tx in valid_txs:
		for tx_out in tx["out"]:
			if addr == tx_out["addr"]:
				coin["balances"][addr] += tx_out["value"]
				valid.append([tx["hash"], "_" + addr, addr])
				break

	return valid

def print_commands():
	for coincode, coindata in desired_forks.viewitems():
		if coindata.has_key("commands"):
			print coindata["name"] + " (" + coincode + ")"
			print "\n".join(coindata["commands"])
			print

def print_balances():
	decimals = 100000000.0
	for coincode, coindata in desired_forks.viewitems():
		if coindata["total_value"] > 0:
			print
			coin_fmt = (coindata["name"] + " (" + coincode + ")").ljust(50, " ")
			total_fmt = format((coindata["total_value"] / decimals), ".8f")
			print coin_fmt + total_fmt.rjust(15, " ") + " BTC"

			for addr, balance in coindata["balances"].viewitems():
				if balance > 0:
					addr_fmt = addr.ljust(50, " ")
					balance_fmt = format((balance / decimals), ".8f")
					print addr_fmt + balance_fmt.rjust(15, " ") + " BTC "


def get_cli_args():
	if len(sys.argv) == 1:
		print "You can also specify which forks you want. Example: python " + sys.argv[0] + " btv bcx"
		return None

	return [arg.upper() for arg in sys.argv[1:]]

def get_desired_forks():
	cli_args = get_cli_args()
	if cli_args is None:
		return {}
	return { k : v for k, v in fork_list.iteritems() if k in cli_args }

main()