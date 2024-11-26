from structs import ULD, Package
from solver import Solver
import csv
import copy
import random
import math

k = 5000
ulds = []
packages = []


def getPackages():
    f = open("package.csv", mode="r")
    packageCSV = csv.reader(f)
    for p in packageCSV:
        if p[5] == "Economy":
            package = Package(p[1], p[2], p[3], p[4], p[0], p[5], p[6])
            packages.append(package)
        else:
            package = Package(p[1], p[2], p[3], p[4], p[0], p[5])
            packages.append(package)


def getULD():
    f = open("ULD.csv", mode="r")
    uldCSV = csv.reader(f)
    for u in uldCSV:
        uld = ULD(u[1], u[2], u[3], u[4], u[0])
        ulds.append(uld)


def metrics(ulds):
    freeSpace = 0
    totalSpace = 0
    freeWeight = 0
    totalWeight = 0
    for uld in ulds:
        uldfreeSpace = uld.getVolume()
        uldtotalSpace = uld.getVolume()
        totalSpace += uld.getVolume()
        freeSpace += uld.getVolume()
        totalWeight += uld.weight_limit
        freeWeight += uld.weight_limit
        uldfreeWeight = uld.weight_limit
        uldtotalWeight = uld.weight_limit
        for package in uld.packages:
            uldfreeSpace -= package.getVolume()
            freeSpace -= package.getVolume()
            uldfreeWeight -= package.weight
            freeWeight -= package.weight
        print(str(uldfreeSpace/uldtotalSpace*100) +
              "% free space in uld ", uld.id)
        print(str(uldfreeWeight/uldtotalWeight*100) +
              "% free weight in uld ", uld.id)
    print(str(freeSpace/totalSpace*100)+"% free uld space")
    print(str(freeWeight/totalWeight*100)+"% free uld weight")
    cost = 0

    packagesTotal = 0
    packagesPriority = 0
    packagesEconomy = 0
    packagesTotalTaken = 0
    packagesPriorityTaken = 0
    packagesEconomyTaken = 0

    for package in packages:
        packagesTotal += 1
        if package.ULD != -1:
            packagesTotalTaken += 1
        if package.priority == "Priority":
            packagesPriority += 1
            if package.ULD != -1:
                packagesPriorityTaken += 1
        else:
            packagesEconomy += 1
            if package.ULD != -1:
                packagesEconomyTaken += 1

    print("{0} out of {1} packages taken".format(
        packagesTotalTaken, packagesTotal))
    print("{0} out of {1} priority packages taken".format(
        packagesPriorityTaken, packagesPriority))
    print("{0} out of {1} economy packages taken".format(
        packagesEconomyTaken, packagesEconomy))

    for package in packages:
        if package.ULD == -1:
            cost += package.cost
    print("Cost without accounting for priority uld (k) = ", cost)
    for uld in ulds:
        if uld.isPriority:
            cost += k

    print("The cost is ", cost)
    return cost


class SimulatedAnnealingSolver:
    def __init__(self, packages, ulds, initial_temp, cooling_rate, num_iterations):
        self.packages = packages
        self.ulds = ulds
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.num_iterations = num_iterations
        self.k = 5000  # Cost for each ULD containing priority packages
        priority = []

    def generate_neighbor(self, current_ordering):
        # random.seed()
        neighbor = current_ordering[:]
        for i in range(20):
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def solve(self):

        temperature = self.initial_temp
        current_ordering = packages
        best_ordering = packages
        best_cost = 100000000
        current_cost = 100000000

        for iteration in range(self.num_iterations):

            neighbor_ordering = self.generate_neighbor(current_ordering)
            next_solver = Solver(neighbor_ordering, ulds)
            next_solver.solve()
            neighbor_cost = metrics(next_solver.ulds)
            delta_cost = neighbor_cost - current_cost

            if delta_cost < 0 or random.uniform(0, 1) < math.exp(-delta_cost / temperature):
                current_ordering = neighbor_ordering
                current_cost = neighbor_cost

                if neighbor_cost < best_cost:
                    best_ordering = neighbor_ordering
                    best_cost = neighbor_cost

            temperature *= self.cooling_rate  # Update temperature

            print(f"Iteration {iteration}, Current Cost: {
                  current_cost}, Best Cost: {best_cost}")

        # Return the best ordering and cost found
        return best_ordering, best_cost


getPackages()
getULD()

# Initialize parameters
initial_temp = 10000
cooling_rate = 0.995
num_iterations = 50

sa_solver = SimulatedAnnealingSolver(
    packages, ulds, initial_temp, cooling_rate, num_iterations)
best_ordering, best_cost = sa_solver.solve()

# Final packing with the best ordering
solver = Solver(best_ordering, ulds)
solver.solve()
# metrics(ulds, packages, sa_solver.k)

# solver = Solver(packages,ulds)
# solver.solve()
# metrics(ulds)
