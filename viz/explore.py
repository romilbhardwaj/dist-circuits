import argparse
import os
import random

parser = argparse.ArgumentParser(description="Turn all the knobs as much as possible")
parser.add_argument("in_circuit_file", help="Path to input circuit json file")
parser.add_argument("out_data_file", help="Path to output file for circuit sim results")
parser.add_argument("--and_cost", type=int, help="AND cost", required=True)
parser.add_argument("--xor_cost", type=int, help="XOR cost", required=True)
parser.add_argument("--inv_cost", type=int, help="INV cost", required=True)
parser.add_argument("--n_iter", type=int, help="Number of interations", required=True)

args = parser.parse_args()

def get_knobs():
    return (random.uniform(1.0, 8.0), random.randint(3, 32), random.choice(['fennel', 'fennel-weighted', 'fennel-output']))

tried = []
for i in range(args.n_iter):
    k = get_knobs()
    while k in tried:
        k = get_knobs()

    command_str = "python3 eval.py " + args.in_circuit_file + " --out_file " + args.out_data_file + " --clusters " + str(k[1]) + " --gamma " + str(k[0]) + " --and_cost " + str(args.and_cost) + " --xor_cost " + str(args.xor_cost) + " --inv_cost " + str(args.inv_cost) + " --algorithm " + k[2]

    ret = os.system(command_str)
    if ret != 0:
        print("ERROR - return val:", ret)

