"""Solves an instance.

Modify this file to implement your own solvers.

For usage, run `python3 solve.py --help`.
"""

import argparse
from pathlib import Path
from typing import Callable, Dict
from unittest import result

from instance import Instance
from point import Point
from solution import Solution
from file_wrappers import StdinFileWrapper, StdoutFileWrapper
from collections import defaultdict


def solve_naive(instance: Instance) -> Solution:
    return Solution(
        instance=instance,
        towers=instance.cities,
    )

def count_intrusions(penalty, towers_so_far, new_tower):
    count = 0
    for t in towers_so_far:
        if Point.distance_obj(t, new_tower) <= penalty:
            count += 1
    return count 

def set_cover(instance:Instance) -> Solution:
    set_to_points = defaultdict(list)
    sets = set()
    grid_len = instance.grid_side_length
    for i in range(grid_len):
        for j in range(grid_len):
            p = Point(i,j)
            lst = []
            for c in instance.cities:
                if Point.distance_obj(c, p) <= instance.coverage_radius:
                    lst.append(c)
            sets.add(tuple(lst))
            set_to_points[tuple(lst)].append(p)
    
    covered = set()
    cover = []
    towers = []

    while covered != set(instance.cities):
        list_of_subsets = list(sets)
        list_of_subsets.sort(key=lambda s: len(set(s) - covered), reverse=True)
        list_of_subsets = list_of_subsets[:5]

        list_of_towers = [min(set_to_points[subset], key=lambda t: count_intrusions(instance.penalty_radius, towers, t)) for subset in list_of_subsets]
        index = min(range(0, len(list_of_towers)), key = lambda i :count_intrusions(instance.penalty_radius, towers, list_of_towers[i]))

        cover.append(list_of_subsets[index])
        towers.append(list_of_towers[index])
        [covered.add(city) for city in list_of_subsets[index]]
        sets.remove(list_of_subsets[index])
    
    return Solution(
        instance = instance,
        towers = towers
    )

def max_min_overlap(instance: Instance) -> Solution:
    
    def service_radius(x, y):
        result = []
        for j in range(x-2, x+3):
            for k in range(y-2, y+3):
                result.append((j, k))
        result.append((x-3, y))
        result.append((x+3, y))
        result.append((x, y+3))
        result.append((x, y-3))
        return result

    def tower_mapping(cities, grid_length):
        result = {}

        for x in range(grid_length):
            for y in range(grid_length):
                result[(x, y)] = []

        for city in cities:
            for point in service_radius(city[0], city[1]):
                if point in result:
                    result[point].append((city[0], city[1]))

        copy = {}
        for key in result:
            if len(result[key]) != 0:
                copy[key] = result[key]
        
        return copy
    
    cities = [(city.x, city.y) for city in instance.cities]
    grid_length = instance.grid_side_length
    penalty_radius = instance.penalty_radius

    placed_towers = []

    while len(cities) != 0:
        towers = tower_mapping(cities, grid_length)
        intrusion_map = {}

        for tower in towers:
            instrusions = 0
            for placed_tower in placed_towers:
                dx = tower[0] - placed_tower[0]
                dy = tower[1] - placed_tower[1]
                dist = ((dx ** 2) + (dy ** 2))
                if dist <= penalty_radius ** 2:
                    instrusions += 1
            intrusion_map[tower] = instrusions
        
        min_intrusion = min(intrusion_map.values())
        min_instrusion_towers = [tower for tower in towers if intrusion_map[tower] == min_intrusion]

        chosen_tower = max(min_instrusion_towers, key = lambda x: len(towers[x]))

        placed_towers.append(chosen_tower)

        for city in towers[chosen_tower]:
            cities.remove(city)

    solution_towers = []
    for tower in placed_towers:
        solution_towers.append(Point(x=tower[0], y=tower[1]))
    
    return Solution(
        instance=instance,
        towers=solution_towers,
    )

SOLVERS: Dict[str, Callable[[Instance], Solution]] = {
    "naive": solve_naive,
    "max_min_overlap": max_min_overlap,
    "set-cover" : set_cover
}



# You shouldn't need to modify anything below this line.
def infile(args):
    if args.input == "-":
        return StdinFileWrapper()

    return Path(args.input).open("r")


def outfile(args):
    if args.output == "-":
        return StdoutFileWrapper()

    return Path(args.output).open("w")


def main(args):
    with infile(args) as f:
        instance = Instance.parse(f.readlines())
        solver = SOLVERS[args.solver]
        solution = solver(instance)
        assert solution.valid()
        with outfile(args) as g:
            print("# Penalty: ", solution.penalty(), file=g)
            solution.serialize(g)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve a problem instance.")
    parser.add_argument("input", type=str, help="The input instance file to "
                        "read an instance from. Use - for stdin.")
    parser.add_argument("--solver", required=True, type=str,
                        help="The solver type.", choices=SOLVERS.keys())
    parser.add_argument("output", type=str,
                        help="The output file. Use - for stdout.",
                        default="-")
    main(parser.parse_args())
