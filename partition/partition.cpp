#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <limits>
#include <cmath>
#include <unordered_set>
#include <algorithm>

#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graph_traits.hpp"
#include "nlohmann/json.hpp"

#define TMP_FILE "/tmp/hahaha_im_a_temp_file.json"
#define AND_COST 8.0
#define XOR_COST 2.0
#define INV_COST 1.0

using json = nlohmann::json;

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::bidirectionalS> DirectedGraph;
typedef std::pair<int, int> Edge;
typedef boost::graph_traits<DirectedGraph>::vertex_iterator vertex_iter;
typedef boost::graph_traits<DirectedGraph>::out_edge_iterator out_edge_iter;
typedef boost::graph_traits<DirectedGraph>::in_edge_iterator in_edge_iter;

static float cost_gamma = 1.5;

float partition_cost(DirectedGraph &g, std::vector<std::unordered_set<int>> &partitions, float p_size, float g_size) {
    float alpha = boost::num_edges(g) * (powf(partitions.size(), cost_gamma-1) / (powf(g_size, cost_gamma)));
    return alpha * powf(p_size, cost_gamma);
}

int num_edges_in_partition(DirectedGraph &g, std::unordered_set<int> &partition) {

    int n_edges = 0;
    std::unordered_set<int> partition_set(partition.begin(), partition.end());

    for (auto n : partition) {
        std::pair<out_edge_iter, out_edge_iter> op;
        for (op = boost::out_edges(n, g); op.first != op.second; op.first++) { 
            int source = boost::source(*op.first, g);
            int target = boost::target(*op.first, g);
            if (partition_set.find(source) != partition_set.end() && partition_set.find(target) != partition_set.end()) {
                n_edges++;
            }
        }
    }

    return n_edges;
}

float weighted_gate_size(std::string name) {
    if (name.find("AND") != std::string::npos) {
        return AND_COST;
    } else if (name.find("XOR") != std::string::npos) {
        return XOR_COST;
    } else if (name.find("INV") != std::string::npos) {
        return INV_COST;
    }
    return 0;
}

float weighted_graph_size(std::map<int, std::string> &rev_node_map, DirectedGraph &g) {
    float size = 0.0; 
    std::pair<vertex_iter, vertex_iter> vp;
    for(vp = boost::vertices(g); vp.first != vp.second; vp.first++) {
        size += weighted_gate_size(rev_node_map[*vp.first]);
    }
    return size;
}

float weighted_partition_size(std::map<int, std::string> &rev_node_map, std::unordered_set<int> &p) {
    float size = 0.0;
    for (auto n : p) {
        size += weighted_gate_size(rev_node_map[n]);
    }
    return size;
}

float g(DirectedGraph &g, std::map<int, std::string> &rev_node_map, std::vector<std::unordered_set<int>> &partitions) {
    float result = 0.0;
    for (int i = 0; i < partitions.size(); i++) {
        result += (num_edges_in_partition(g, partitions[i]) -
                  partition_cost(g, partitions,
                                 weighted_partition_size(rev_node_map, partitions[i]),
                                 weighted_graph_size(rev_node_map, g)));
    }
    return result;
}

float delta_g(DirectedGraph &graph, std::map<int, std::string> &rev_node_map, int vertex, int partition_idx, std::vector<std::unordered_set<int>> &partitions, float g_without_v) {

    partitions[partition_idx].insert(vertex);
    float g_with_v = g(graph, rev_node_map, partitions);
    partitions[partition_idx].erase(vertex);

    return g_with_v - g_without_v;
}

int vertex_assignment(DirectedGraph &graph, std::map<int, std::string> &rev_node_map, int vertex, std::vector<std::unordered_set<int>> &partitions) {
    
    int max_partition = 0;
    float max_dg = -std::numeric_limits<float>::max();

    for (int i = 0; i < partitions.size(); i++) {
        float g_without_v = g(graph, rev_node_map, partitions);
        float dg = delta_g(graph, rev_node_map, vertex, i, partitions, g_without_v);
        if (dg > max_dg) {
            max_dg = dg;
            max_partition = i;
        }
    }

    return max_partition;
}

void fennel(DirectedGraph &g, std::map<int, std::string> &rev_node_map, std::vector<std::unordered_set<int>> &partitions) {

    // Iterate through each vertex
    std::pair<vertex_iter, vertex_iter> vp;
    for(vp = boost::vertices(g); vp.first != vp.second; vp.first++) {
        int vertex = *vp.first;
        std::string node_name = rev_node_map[vertex];

        // Skip the partition assignment if it's just an input or output bit
        if (node_name.find("INPUT") != std::string::npos || node_name.find("OUTPUT") != std::string::npos) {
            continue;
        }

        int assignment = vertex_assignment(g, rev_node_map, vertex, partitions);
        partitions[assignment].insert(vertex);

        // Append any input bits to the same partition assignment
        std::pair<in_edge_iter, in_edge_iter> ip;
        for (ip = boost::in_edges(vertex, g); ip.first != ip.second; ip.first++) { 
            int pre = boost::source(*ip.first, g);
            std::string pre_name = rev_node_map[pre];
            if (pre_name.find("INPUT") != std::string::npos) {
                partitions[assignment].insert(pre);
            }
        }

        // Append any output bits to the same partition assignment
        std::pair<out_edge_iter, out_edge_iter> op;
        for (op = boost::out_edges(vertex, g); op.first != op.second; op.first++) { 
            int post = boost::target(*op.first, g);
            std::string post_name = rev_node_map[post];
            if (post_name.find("OUTPUT") != std::string::npos) {
                partitions[assignment].insert(post);
            }
        }
    }
}

void generate_output_files(std::string input_mpc_file, std::string output_directory, DirectedGraph &g,
                           std::map<std::string, int> &node_map, std::vector<std::unordered_set<int>> &partitions) {
    
    std::size_t found = input_mpc_file.find_last_of("/");
    std::string file = input_mpc_file.substr(found+1);
    found = file.find_last_of(".");
    std::string circuit_name = file.substr(0, found);

    std::string output_path = output_directory + "/" + circuit_name;
    
    // Open input files
    std::ifstream in(input_mpc_file);

    // Open output files
    std::ofstream full_out(output_path + ".txt");
    std::vector<std::ofstream> outs;
    std::vector<std::ofstream> meta_outs;
    for (int i = 0; i < partitions.size(); i++) {
        outs.push_back(std::ofstream(output_path + "-" + std::to_string(i) + ".txt"));
        meta_outs.push_back(std::ofstream(output_path + "-" + std::to_string(i) + "-meta.txt"));
    }

    int num_gates, num_wires, num_a_inputs, num_b_inputs, num_outputs;
    in >> num_gates >> num_wires >> num_a_inputs >> num_b_inputs >> num_outputs;

    // Set circuit header
    std::string header = std::to_string(num_gates) + " " + std::to_string(num_wires) + "\n" +
                         std::to_string(num_a_inputs) + " " + std::to_string(num_b_inputs) + " " + std::to_string(num_outputs) + "\n\n";
    full_out << header;
    for (auto& o : outs) o << header;

    // Track partition input/output wire numbers
    std::vector<std::set<int>> partition_input_wires(partitions.size());
    std::vector<std::set<int>> partition_output_wires(partitions.size());

    // Iterate through gates
    int num_gate_inputs, num_gate_outputs;
    int gate_line_number = 4;
    while(in >> num_gate_inputs >> num_gate_outputs) {
        if (num_gate_inputs > 2 || num_gate_outputs > 1) {
            std::cerr << "ERROR: bad gate | inputs: " << num_gate_inputs << " outputs: " << num_gate_outputs << std::endl;
            continue;
        }

        std::string gate_string = std::to_string(num_gate_inputs) + " " + std::to_string(num_gate_outputs) + " ";
        int input_wires[2];
        for(int i = 0; i < num_gate_inputs; i++) {
            in >> input_wires[i];
            gate_string += std::to_string(input_wires[i]) + " ";
        }

        int output_wire;
        in >> output_wire;
        gate_string += std::to_string(output_wire) + " ";

        std::string gate_type;
        in >> gate_type;
        gate_string += gate_type + "\n";

        // Write out gate to full circuit file
        full_out << gate_string;

        // Figure out which partition the gate belongs to and write it to that file
        std::string gate_name = "GATE_" + gate_type + "_" + std::to_string(gate_line_number);
        int gate_id = node_map[gate_name];
        for (int i = 0; i < partitions.size(); i++) {
            if (partitions[i].find(gate_id) != partitions[i].end()) {
                for (int j = 0; j < num_gate_inputs; j++) {
                    // Ignore actual input bits
                    if (input_wires[j] >= num_a_inputs + num_b_inputs) {
                        partition_input_wires[i].insert(input_wires[j]);   
                    }
                }
                // Ignore actual output bits
                if (output_wire < num_wires - num_outputs) {
                    partition_output_wires[i].insert(output_wire);
                }
                outs[i] << gate_string;
            }
        }

        gate_line_number++;
    }

    // Track partition input/output wire numbers
    // Write metadata files
    std::vector<std::vector<int>> incoming_wires(partitions.size());
    std::vector<std::vector<int>> outgoing_wires(partitions.size());
    for (int i = 0; i < partitions.size(); i++) {
        // Node number
        meta_outs[i] << i << " ";

        std::vector<int> p_inputs(partition_input_wires[i].begin(), partition_input_wires[i].end());
        std::vector<int> p_outputs(partition_output_wires[i].begin(), partition_output_wires[i].end());
        std::set_difference(p_inputs.begin(), p_inputs.end(),
                            p_outputs.begin(), p_outputs.end(),
                            std::inserter(incoming_wires[i], incoming_wires[i].begin()));

        std::set_difference(p_outputs.begin(), p_outputs.end(),
                            p_inputs.begin(), p_inputs.end(),
                            std::inserter(outgoing_wires[i], outgoing_wires[i].begin()));

        // Write info on number of incoming and outgoing wires
        meta_outs[i] << incoming_wires[i].size() << " " << outgoing_wires[i].size() << "\n";
    }

    for(int i = 0; i < partitions.size(); i++) {
        std::cout << "partition " << i << " incoming wires (from other nodes): ";
        for (auto x : incoming_wires[i]) std::cout << x << " ";
        std::cout << std::endl << "partition " << i << " outgoing wires (to other nodes): ";
        for (auto x : outgoing_wires[i]) std::cout << x << " ";
        std::cout << std::endl;
    }

    // Figure out where the wires are coming from / going to and write those to metadata
    for (int i = 0; i < partitions.size(); i++) {
        // Do all the inputs first
        for (int iw : incoming_wires[i]) {
            for (int j = 0; j < partitions.size(); j++) {
                for (int ow : partition_output_wires[j]) {
                    if (ow == iw) {
                        // <wire> <source>
                        meta_outs[i] << iw << " " << j << "\n";
                    }
                }
            }
        }

        // Now do the outputs
        for (int ow : outgoing_wires[i]) {
            for (int j = 0; j < partitions.size(); j++) {
                for (int iw : partition_input_wires[j]) {
                    if (iw == ow) {
                        // <wire> <source>
                        meta_outs[i] << ow << " " << j << "\n";
                    }
                }
            }
        }
    }
}

/*
 * Usage: ./partition <input raw MPC circuit> <directory for output circuit files> <num partitions> <gamma (optional)>
 */
int main(int argc, char *argv[]) {

    if (argc < 4) {
        std::cout << "Usage: ./partition <input raw MPC circuit> <output directory> <num partitions> [gamma]" << std::endl;
        return 1;
    }

    // Arg 1: input MPC file, representing circuit, need to parse to JSON
    std::string input_mpc_file(argv[1]);
    std::string convert_command = "python3 mpc2graph.py ";
    convert_command += input_mpc_file + " " + TMP_FILE;

    std::cout << "Converting raw circuit file: " << convert_command << std::endl;
    system(convert_command.c_str());

    std::ifstream i(TMP_FILE);
    json graph_json;
    i >> graph_json;

    // Arg 2: output directory
    std::string output_directory(argv[2]);
    std::cout << "Output directory: " << output_directory << std::endl;

    // Arg 3: number of partitions
    int n_partitions = atoi(argv[3]);
    std::cout << "Number of partitions: " << n_partitions << std::endl;

    // Arg 4: optional gamma parameter
    if (argc >= 5) {
        cost_gamma = atof(argv[4]);
        std::cout << "Fennel gamma specified: " << cost_gamma << std::endl;
    }
    
    // Assign unique node ID to each input/gate/output
    std::cout << "Generating node maps." << std::endl;
    std::map<std::string, int> node_map;
    std::map<int, std::string> reverse_node_map;

    int id = 0;
    for (auto& node : graph_json["nodes"]) {
        node_map[node["id"]] = id;
        reverse_node_map[id] = node["id"];
        id++;
    }

    // Create graph
    std::cout << "Generating graph." << std::endl;
    std::vector<Edge> edgeVec;
    for (auto& link : graph_json["links"]) {
        edgeVec.push_back(Edge(node_map[link["source"]], node_map[link["target"]]));
    }
    DirectedGraph g(edgeVec.begin(), edgeVec.end(), graph_json["nodes"].size());

    std::cout << "Partitioning...";
    std::vector<std::unordered_set<int>> partitions(n_partitions);
    fennel(g, reverse_node_map, partitions);
    std::cout << " done." << std::endl;

    // Output circuit files
    std::cout << "Generating output files." << std::endl;
    generate_output_files(input_mpc_file, output_directory, g, node_map, partitions);

    return 0;
}
