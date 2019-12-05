import argparse
import os

TEMP_PATH = "/tmp/temp_circuit"

parser = argparse.ArgumentParser(description="Run test")
parser.add_argument("in_circuit_file", help="Path to input circuit json file")
parser.add_argument("--out_file", help="Path to output data file (append)")
parser.add_argument("--and_cost", type=int, help="AND cost", required=True)
parser.add_argument("--xor_cost", type=int, help="XOR cost", required=True)
parser.add_argument("--inv_cost", type=int, help="INV cost", required=True)
parser.add_argument("--gamma", type=float, help="Fennel gamma value", required=True)
parser.add_argument("--clusters", type=int, help="Number of clusters", required=True)
parser.add_argument("--algorithm", choices=["fennel", "fennel-weighted", "fennel-output"], help="Clustering algorithm", required=True)

args = parser.parse_args()

command_str = "python3 fennel.py --partitions " + str(args.clusters) + " --gamma " + str(args.gamma) + " --and_cost " + str(args.and_cost) + " --xor_cost " + str(args.xor_cost) + " --inv_cost " + str(args.inv_cost)

if args.algorithm == "fennel-weighted":
    command_str += " --weighted_size"
elif args.algorithm == "fennel-output":
    command_str += " --output_influence"
elif args.algorithm == "fennel":
    pass

command_str += " " + args.in_circuit_file + " " + TEMP_PATH + ".json"

# Cluster graph
print("\t", command_str)
ret = os.system(command_str)
if ret != 0:
    print("return:", ret)

sim_command_str = "python3 stats.py " + TEMP_PATH + ".json --out " + TEMP_PATH + ".txt"
print("\t", sim_command_str)
ret = os.system(sim_command_str)
if ret != 0:
    print("return:", ret)

with open(TEMP_PATH+".txt", "r") as f:
    lines = [l.strip() for l in f.readlines()]

    if args.out_file:
        with open(args.out_file, 'a') as f:
            print(os.path.splitext(os.path.basename(args.in_circuit_file))[0], lines[2], args.algorithm, args.clusters, lines[0], lines[1], args.gamma, args.and_cost, args.xor_cost, args.inv_cost, sep=",", file = f)
    else:
        print(os.path.splitext(os.path.basename(args.in_circuit_file))[0], lines[2], args.algorithm, args.clusters, lines[0], lines[1], args.gamma, args.and_cost, args.xor_cost, args.inv_cost, sep=",")

