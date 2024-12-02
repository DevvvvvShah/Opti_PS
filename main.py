import csv
from heuristics.solver2_withSpaceDefrag import Solver2
from utils.inputGetter import getPackages, getULD
from utils.cartons import cartons
from LPP.carton_to_package import sol_to_package
from utils.containers import containers
from LPP.model import all_swaps as solver
from LPP.package_to_carton import get_from_greedy
from binsearch.binsearch import binsearch
from utils.lpp_utils import are_cubes_intersecting, is_box_inside_container, plot
from utils.metrics import metrics






k = 5000
ulds = []
packages = []



def generateOutput(packages):
    f = open("output.csv", mode="w")
    outputCSV = csv.writer(f)
    packages.sort(key=lambda x: (str(x.ULD),list(x.position)))
    for package in packages:
        outputCSV.writerow([package.id,package.ULD,package.position,package.getDimensions(),package.weight,package.cost,package.rotation,package.priority])

mincost=100000000000000000000

best29556perms = [13,17,19,23]

for i in range(0,4):
    perm=best29556perms[i]
    packages = []
    ulds = []
    getPackages(packages)
    getULD(ulds)
    solver2 = Solver2(packages,ulds,perm)
    solver2.solve(perm)
    generateOutput(packages)
    mincost=min(mincost,metrics(packages,ulds,k))
    print(mincost)
    print(perm)

    cartons = cartons()
    containers = containers()


    binsearchSolution = binsearch(packageArray=packages, uldArray=ulds)
    newPackages = sol_to_package(binsearchSolution)


    generateOutput(newPackages)

    init = get_from_greedy(packageArray=newPackages)
    solution = solver(cartons=cartons, containers=containers, init=init)

    generateOutput(sol_to_package(solution))


    for i in range(len(solution)):
        for j in range(i + 1, len(solution)):
            if (solution[i]["container_id"] != solution[j]["container_id"]):
                continue
            if (solution[i]["container_id"] == -1):
                continue
            if are_cubes_intersecting(solution[i], solution[j]):
                print("Cubes intersecting:", solution[i]["carton_id"], solution[j]["carton_id"])
    for i in range(len(solution)):
        for j in range(len(containers)):
            if solution[i]['container_id'] == containers[j]['id']:
                if is_box_inside_container(solution[i], containers[j]) == 0:
                    print(f"out of range ! carton : {solution[i]['carton_id']}")

    plot(solution)
    print(solution)