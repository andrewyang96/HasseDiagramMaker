import argparse
import csv
import networkx as nx
from networkx.drawing.nx_pydot import write_dot  # requires pydotplus
from typing import Dict
from typing import List
from typing import Tuple

# Tuple maker methods
def read_csv(fname: str) -> List[List[str]]:
    with open(fname, 'r') as f:
        data = list(csv.reader(f))[1:] # remove header row
        data = [row[1:] for row in data] # assume that the length of each row is the same
        return data

def make_freq_tuples(data: List[List[str]], print_tuples=False) -> Dict[str, Tuple]:
    freqs = {}
    for row in data:
        for idx, player in enumerate(row):
            if player not in freqs:
                freqs[player] = [0] * len(row)
            freqs[player][idx] += 1
    if print_tuples:
        print(freqs)
    return {player: tuple(freq) for player, freq in freqs.items()}

# Hasse diagram logic methods
def is_first_tuple_at_least_as_good(my_tuple: Tuple, other_tuple: Tuple) -> bool:
    for end_idx in range(1, len(my_tuple) + 1):
        if sum(my_tuple[:end_idx]) < sum(other_tuple[:end_idx]):
            return False
    return True

def init_hasse(freqs: Dict[str, Tuple], make_edges: bool) -> nx.DiGraph:
    tuple_players_map = {}
    for player, player_tuple in freqs.items():
        if player_tuple not in tuple_players_map:
            tuple_players_map[player_tuple] = []
        tuple_players_map[player_tuple].append(player)
    graph = nx.DiGraph()
    for tuple_, players in tuple_players_map.items():
        graph.add_node(tuple_, label='{0}\n{1}'.format(', '.join(players), tuple_))
    if make_edges:
        for tuple1 in graph.nodes():
            for tuple2 in graph.nodes():
                if tuple1 == tuple2:
                    continue
                if is_first_tuple_at_least_as_good(tuple1, tuple2) and not is_first_tuple_at_least_as_good(tuple2, tuple1):
                    graph.add_edge(tuple1, tuple2)
    return graph

def get_tiers(graph: nx.DiGraph) -> List[List[str]]:
    curr_level = [player for player in graph.nodes() if len(graph.in_edges(player)) == 0]
    tiers = []
    while len(curr_level) > 0:
        tiers.append(curr_level)
        next_level = []
        for tuple_ in curr_level:
            for _, other_tuple in graph.out_edges(tuple_):
                if len(graph.in_edges(other_tuple)) == 1:
                    next_level.append(other_tuple)
                else:
                    graph.remove_edge(tuple_, other_tuple)
        curr_level = next_level
    return tiers

def reconstruct_hasse(freqs: Dict[str, Tuple], tiers: List[List[str]]) -> nx.DiGraph:
    graph = init_hasse(freqs, False)
    leftovers = []
    for idx in range(len(tiers) - 1):
        higher_tier = tiers[idx]
        lower_tier = tiers[idx + 1]
        for higher_tuple in higher_tier:
            found_match_for_leftover = [False] * len(leftovers)
            next_leftovers = []
            for lower_tuple in lower_tier:
                for idx, leftover_tuple in enumerate(leftovers):
                    if is_first_tuple_at_least_as_good(leftover_tuple, lower_tuple) and not is_first_tuple_at_least_as_good(lower_tuple, leftover_tuple):
                        graph.add_edge(leftover_tuple, lower_tuple)
                        found_match_for_leftover[idx] = True
                if is_first_tuple_at_least_as_good(higher_tuple, lower_tuple) and not is_first_tuple_at_least_as_good(lower_tuple, higher_tuple):
                    graph.add_edge(higher_tuple, lower_tuple)
                else:
                    next_leftovers.append(higher_tuple)
            leftovers = [leftovers[idx] for idx in range(len(leftovers)) if not found_match_for_leftover[idx]]
            leftovers += next_leftovers
    return graph

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_csv', type=str, help='Path to the input CSV file.')
    parser.add_argument(
        'output_dot', type=str, help='Path to the output DOT file.')
    parser.add_argument('--print_tuples', action='store_true')
    args = parser.parse_args()

    data = read_csv(args.input_csv)
    freqs = make_freq_tuples(data, print_tuples=args.print_tuples)

    graph = init_hasse(freqs, True)
    tiers = get_tiers(graph)
    graph = reconstruct_hasse(freqs, tiers)
    write_dot(graph, args.output_dot)
    print('Wrote to {0}. Convert to PNG: dot -Tpng {0} > output.png'.format(args.output_dot))
