from structs import ULD, Package
from solver import Solver
import csv
import random
import math

# Constants
k = 5000
ulds = []
packages = []

# Function to load packages from a CSV file


def getPackages():
    with open("package.csv", mode="r") as f:
        packageCSV = csv.reader(f)
        for p in packageCSV:
            if p[5] == "Economy":
                package = Package(p[1], p[2], p[3], p[4], p[0], p[5], p[6])
                packages.append(package)
            else:
                package = Package(p[1], p[2], p[3], p[4], p[0], p[5])
                packages.append(package)

# Function to load ULDs from a CSV file


def getULD():
    with open("ULD.csv", mode="r") as f:
        uldCSV = csv.reader(f)
        for u in uldCSV:
            uld = ULD(u[1], u[2], u[3], u[4], u[0])
            ulds.append(uld)

# Metrics function to calculate the cost and utilization


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
        print(f"{uldfreeSpace / uldtotalSpace *
              100:.2f}% free space in ULD {uld.id}")
        print(f"{uldfreeWeight / uldtotalWeight *
              100:.2f}% free weight in ULD {uld.id}")
    print(f"{freeSpace / totalSpace * 100:.2f}% free ULD space")
    print(f"{freeWeight / totalWeight * 100:.2f}% free ULD weight")

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

    print(f"{packagesTotalTaken} out of {packagesTotal} packages taken")
    print(f"{packagesPriorityTaken} out of {
          packagesPriority} priority packages taken")
    print(f"{packagesEconomyTaken} out of {
          packagesEconomy} economy packages taken")

    for package in packages:
        if package.ULD == -1:
            cost += package.cost
    print("Cost without accounting for priority ULD (k) =", cost)
    for uld in ulds:
        if uld.isPriority:
            cost += k

    print("The cost is", cost)
    return cost

# Tabu Search Solver


class TabuSearchSolver:
    def __init__(self, packages, ulds, tabu_tenure, num_iterations):
        self.packages = packages
        self.ulds = ulds
        # Number of iterations a solution stays in the tabu list
        self.tabu_tenure = tabu_tenure
        self.num_iterations = num_iterations
        self.k = 5000  # Cost for each ULD containing priority packages
        self.tabu_list = []  # Stores recently visited solutions

    def generate_neighbor(self, current_ordering):
        """Generate a single neighbor solution."""
        neighbor = current_ordering[:]
        for _ in range(20):  # Perform 20 random swaps
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def solve(self):
        """Main Tabu Search optimization logic."""
        current_ordering = self.packages
        best_ordering = self.packages
        best_cost = float('inf')  # Set initial best cost to infinity
        current_cost = float('inf')  # Set initial current cost to infinity

        for iteration in range(self.num_iterations):
            # Generate a neighbor
            neighbor_ordering = self.generate_neighbor(current_ordering)

            # Solve and calculate metrics for the neighbor
            next_solver = Solver(neighbor_ordering, self.ulds)
            next_solver.solve()
            neighbor_cost = metrics(next_solver.ulds)

            # If the neighbor is better or meets aspiration criteria
            if neighbor_cost < current_cost or neighbor_ordering not in self.tabu_list:
                current_ordering = neighbor_ordering
                current_cost = neighbor_cost

                # Update best solution if the neighbor improves it
                if neighbor_cost < best_cost:
                    best_ordering = neighbor_ordering
                    best_cost = neighbor_cost

                # Add current solution to the tabu list
                self.tabu_list.append(neighbor_ordering)
                if len(self.tabu_list) > self.tabu_tenure:
                    self.tabu_list.pop(0)  # Maintain tabu tenure

            print(f"Iteration {
                  iteration + 1}, Current Cost: {current_cost}, Best Cost: {best_cost}")

        # Return the best solution and its cost
        return best_ordering, best_cost


# Main execution
getPackages()
getULD()

# Initialize parameters for Tabu Search
tabu_tenure = 20
num_iterations = 100

# Solve using Tabu Search
ts_solver = TabuSearchSolver(packages, ulds, tabu_tenure, num_iterations)
best_ordering, best_cost = ts_solver.solve()

# Final packing with the best ordering
solver = Solver(best_ordering, ulds)
solver.solve()
