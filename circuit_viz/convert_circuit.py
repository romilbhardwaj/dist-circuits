import argparse
import json

parser = argparse.ArgumentParser(description="Convert AGMPC circuits to visualizable format.")
parser.add_argument("in_file", help="Input file location")
parser.add_argument("output_file", help="Output file location")

args = parser.parse_args()

with open(args.in_file, 'r') as f:
    in_lines = [x.strip().split() for x in f]

nodes = []
links = []

num_gates, num_wires = [int(x) for x in in_lines[0]]
num_a_inputs, num_b_inputs, num_outputs = [int(x) for x in in_lines[1]]

for i in range(num_a_inputs):
    nodes.append({
        "id": "INPUT_A_"+str(i),
        "group": "INPUT_A"
    })

for i in range(num_b_inputs):
    nodes.append({
        "id": "INPUT_B_"+str(i),
        "group": "INPUT_B"
    })

for i in range(num_outputs):
    nodes.append({
        "id": "OUTPUT_"+str(i),
        "group": "OUTPUT"
    })

input_wire_map = {}
for i in range(num_wires):
    input_wire_map[i] = []

for i, l in enumerate(in_lines[3:]):
    if not l:
        continue

    input_num, output_num = int(l[0]), int(l[1])

    input_wires = [int(x) for x in l[2:2+input_num]]
    output_wires = [int(x) for x in l[2+input_num:2+input_num+output_num]]

    gate_type = l[-1]

    nodes.append({
        "id": "GATE_"+gate_type+"_"+str(i+4),
        "group": gate_type
    })

    for iw in input_wires:
        print(iw)
        if iw < num_a_inputs:
            links.append({
                "source": "INPUT_A_"+str(iw),
                "target": "GATE_"+gate_type+"_"+str(i+4),
                "value": 1
            })
        elif iw < num_a_inputs + num_b_inputs:
            links.append({
                "source": "INPUT_B_"+str(iw - num_a_inputs),
                "target": "GATE_"+gate_type+"_"+str(i+4),
                "value": 1
            })
        else:
            input_wire_map[iw].append("GATE_"+gate_type+"_"+str(i+4))

    for ow in output_wires:
        if ow >= num_wires - num_outputs:
            links.append({
                "source": "GATE_"+gate_type+"_"+str(i+4),
                "target": "OUTPUT_"+str(ow - (num_wires - num_outputs)),
                "value": 1
            })

for i, l in enumerate(in_lines[3:]):
    if not l:
        continue

    input_num, output_num = int(l[0]), int(l[1])

    input_wires = [int(x) for x in l[2:2+input_num]]
    output_wires = [int(x) for x in l[2+input_num:2+input_num+output_num]]

    gate_type = l[-1]

    for ow in output_wires:
        for gate in input_wire_map[ow]:
            links.append({
                "source": "GATE_"+gate_type+"_"+str(i+4),
                "target": gate,
                "value": 1
            })

graph = {
    "nodes": nodes,
    "links": links
}

with open(args.output_file, 'w') as outfile:
    json.dump(graph, outfile)

