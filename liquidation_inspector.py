import json
from typing import Optional

from web3 import Web3

from typing import List, Optional

from mev_inspect import utils
from mev_inspect.config import load_config
from mev_inspect.schemas.blocks import NestedTrace, TraceType
from mev_inspect.schemas.classified_traces import Classification, ClassifiedTrace
from mev_inspect.schemas.strategy import StrategyType, Strategy, Liquidation
from mev_inspect.classifier_specs import CLASSIFIER_SPECS
from mev_inspect.trace_classifier import TraceClassifier
from mev_inspect import block

# poetry run inspect -b 12498502 -r 'http://162.55.96.141:8546/'
all_traces = []
result = []
# Inspect list of classified traces and identify liquidation
def liquidations(traces: List[ClassifiedTrace]):
	event = []
	# For each trace
	for k in range(1, len(traces)):
		trace = traces[k]
		try:
			next = traces[k+1]
		except IndexError:
			break
		# Liquidation condition
		if trace.classification == Classification.liquidate:
		# Collateral data from the liquidation.
		# The inputs will differ by DEX, this is AAVE
			all_traces.append(trace)
			liquidator = trace.from_address
			prev = traces[k-1]
			#print(f"Previous: {prev.classification} from {prev.from_address} to {prev.to_address}")
			print(f"Liquidation found: {liquidator}")
			print(f"Hash: {trace.transaction_hash}")
			for i in trace.inputs:
				if(i == '_purchaseAmount'):
					liquidation_amount = trace.inputs[i]
					print(f"\tAmount: {liquidation_amount}")
				elif (i == '_collateral'):
					collateral_type = trace.inputs[i]
					print(f"\tCollateral Address: {collateral_type}")
				elif (i == '_reserve'):
					reserve = trace.inputs[i]
					print(f"\tReserve Address: {reserve}")
				elif(i == '_user'):
					liquidated_usr = trace.inputs[i]
					print(f"\tLiquidated Account Address: {liquidated_usr}")
				# Define the address of the liquidator

				# Find a transfer before liquidation with a to_address corresponding to the liquidator
			for tx in traces[0:int(k)]:
				if ((tx.classification==Classification.transfer) and ('sender' in tx.inputs) and (tx.inputs['sender'] == liquidator)):
					amount_sent = tx.inputs['amount']
					all_traces.append(tx)
					print(f"Transfer from liquidator {liquidator}: \nAmount in received token: {tx.inputs['amount']} to \n{tx.inputs['recipient']} \nTransaction: {tx.transaction_hash}")
				elif ((tx.classification==Classification.transfer) and (tx.inputs['recipient']==liquidator)):
					amount_received = tx.inputs['amount']
					all_traces.append(tx)
					print(f"Transfer to liquidator {liquidator}: \nAmount in received token: {tx.inputs['amount']} from \n{tx.from_address} \nTransaction: {tx.transaction_hash}")

			try:
				profit = amount_received - amount_sent
			except UnboundLocalError:
				print("No match ;[")
				profit = 0
			# Tag liquidation
			result.append(Liquidation(strategy=StrategyType.liquidation,
									  traces=all_traces,
									  protocols=[trace.protocol],
									  collateral_type=collateral_type,
									  collateral_amount=liquidation_amount,
									  profit=profit,
									  reserve=reserve,
									  collateral_source="",))
	return result

rpc = 'http://162.55.96.141:8546/'
block_number = 12498502
base_provider = Web3.HTTPProvider(rpc)
block_data = block.create_from_block_number(block_number, base_provider)
trace_clasifier = TraceClassifier(CLASSIFIER_SPECS)
classified_traces = trace_clasifier.classify(block_data.traces)
print(liquidations(classified_traces)[2])
