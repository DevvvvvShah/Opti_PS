from structs import ULD, Package
from solver import Solver
import csv
import copy
import random
import math

k = 5000  # Cost for each ULD containing priority packages


def getPackages():
    packages = []
    with open("package.csv", mode="r") as f:
        packageCSV = csv.reader(f)
        for p in packageCSV:
            if p[5] == "Economy":
                package = Package(p[1], p[2], p[3], p[4], p[0], p[5], p[6])
            else:
                package = Package(p[1], p[2], p[3], p[4], p[0], p[5])
            packages.append(package)
    return packages


def getULD():
    ulds = []
    with open("ULD.csv", mode="r") as f:
        uldCSV = csv.reader(f)
        for u in uldCSV:
            uld = ULD(u[1], u[2], u[3], u[4], u[0])
            ulds.append(uld)
    return ulds


def metrics(ulds, packages):
    freeSpace = totalSpace = freeWeight = totalWeight = 0
    for uld in ulds:
        uld_free_space = uld.getVolume()
        uld_total_space = uld.getVolume()
        totalSpace += uld_total_space
        freeSpace += uld_free_space
        totalWeight += uld.weight_limit
        freeWeight += uld.weight_limit
        uld_free_weight = uld.weight_limit
        uld_total_weight = uld.weight_limit
        for package in uld.packages:
            uld_free_space -= package.getVolume()
            freeSpace -= package.getVolume()
            uld_free_weight -= package.weight
            freeWeight -= package.weight
        print(f"{(uld_free_space/uld_total_space)
              * 100}% free space in ULD {uld.id}")
        print(f"{(uld_free_weight/uld_total_weight)
              * 100}% free weight in ULD {uld.id}")
    print(f"{(freeSpace/totalSpace)*100}% free ULD space")
    print(f"{(freeWeight/totalWeight)*100}% free ULD weight")

    cost = 0

    packages_total = len(packages)
    packages_taken = sum(1 for pkg in packages if pkg.ULD != -1)
    packages_priority = sum(
        1 for pkg in packages if pkg.priority == "Priority")
    packages_priority_taken = sum(
        1 for pkg in packages if pkg.priority == "Priority" and pkg.ULD != -1)
    packages_economy = packages_total - packages_priority
    packages_economy_taken = packages_taken - packages_priority_taken

    print(f"{packages_taken} out of {packages_total} packages taken")
    print(f"{packages_priority_taken} out of {
          packages_priority} priority packages taken")
    print(f"{packages_economy_taken} out of {
          packages_economy} economy packages taken")

    for package in packages:
        if package.ULD == -1:
            cost += package.cost
    print("Cost without accounting for priority ULD (k) =", cost)
    for uld in ulds:
        if uld.isPriority:
            cost += k

    print("The cost is", cost)
    return cost


def writeOutput(ulds, packages):
    with open("output.csv", mode="w", newline='') as f:
        writer = csv.writer(f)
        for uld in ulds:
            uld.packages.sort(key=lambda x: x.position)
            for package in uld.packages:
                writer.writerow([package.id, uld.id, package.position, [
                                p + d for p, d in zip(package.position, package.getDimensions())]])
        cost = sum(pkg.cost for pkg in packages if pkg.ULD == -1) + \
            k * sum(1 for uld in ulds if uld.isPriority)
        writer.writerow(["Cost", cost])


class SimulatedAnnealingSolver:
    def __init__(self, packages, ulds, initial_temp, cooling_rate, num_iterations):
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.num_iterations = num_iterations
        self.k = 5000  # Cost for each ULD containing priority packages
        self.packages = packages[:]
        self.ulds = ulds[:]

    def generate_neighbor(self, current_ordering):
        neighbor = current_ordering[:]
        idx1, idx2 = random.sample(range(len(neighbor)), 2)
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def calculate_cost(self, ulds, packages):
        cost = sum(pkg.cost for pkg in packages if pkg.ULD == -1)
        cost += self.k * sum(1 for uld in ulds if uld.isPriority)
        return cost

    def solve(self):
        # Initial ordering based on the given sorts
        self.packages.sort(key=lambda x: x.getVolume(), reverse=True)
        self.packages.sort(key=lambda x: (x.cost, x.getVolume()), reverse=True)
        self.ulds.sort(key=lambda x: x.getVolume(), reverse=True)
        initial_ordering = self.packages[:]

        # Calculate the cost from the initial ordering
        current_ordering = initial_ordering[:]
        # Deep copy ULDs to avoid modifying the original ULDs
        ulds_copy = [copy.deepcopy(uld) for uld in self.ulds]
        # Reset package positions and ULD assignments
        for pkg in current_ordering:
            pkg.position = [-1, -1, -1]
            pkg.ULD = -1

        # Solve with the initial ordering
        solver = Solver(current_ordering, ulds_copy)
        solver.solve()
        current_cost = self.calculate_cost(ulds_copy, current_ordering)
        best_ordering = current_ordering[:]
        best_cost = current_cost

        temperature = self.initial_temp

        for iteration in range(self.num_iterations):
            neighbor_ordering = self.generate_neighbor(current_ordering)
            # Need to deep copy ULDs again
            ulds_copy = [copy.deepcopy(uld) for uld in self.ulds]
            # Reset package positions and ULD assignments
            for pkg in neighbor_ordering:
                pkg.position = [-1, -1, -1]
                pkg.ULD = -1

            # Solve with neighbor ordering
            solver = Solver(neighbor_ordering, ulds_copy)
            solver.solve()
            neighbor_cost = self.calculate_cost(ulds_copy, neighbor_ordering)

            delta_cost = neighbor_cost - current_cost

            acceptance_probability = math.exp(-delta_cost /
                                              temperature) if temperature > 1e-6 else 0

            if delta_cost < 0 or random.uniform(0, 1) < acceptance_probability:
                current_ordering = neighbor_ordering[:]
                current_cost = neighbor_cost

                if neighbor_cost < best_cost:
                    best_ordering = neighbor_ordering[:]
                    best_cost = neighbor_cost

            temperature *= self.cooling_rate  # Update temperature

            print(f"Iteration {
                  iteration + 1}, Current Cost: {current_cost}, Best Cost: {best_cost}")

        # After the loop, best_ordering is the best found ordering
        # Solve with the best ordering and update ULDs and packages
        ulds_copy = [copy.deepcopy(uld) for uld in self.ulds]
        for pkg in best_ordering:
            pkg.position = [-1, -1, -1]
            pkg.ULD = -1

        solver = Solver(best_ordering, ulds_copy)
        solver.solve()
        # Update the ULDs and packages
        self.ulds = ulds_copy
        self.packages = best_ordering
        return best_ordering, best_cost


if __name__ == "__main__":
    packages = getPackages()
    ulds = getULD()

    # Initialize parameters
    initial_temp = 10000
    cooling_rate = 0.95
    num_iterations = 50

    sa_solver = SimulatedAnnealingSolver(
        packages, ulds, initial_temp, cooling_rate, num_iterations)
    best_ordering, best_cost = sa_solver.solve()

    # After solving, sa_solver.ulds and sa_solver.packages are updated
    # So we can use them to calculate the metrics and write output
    metrics(sa_solver.ulds, sa_solver.packages)
    writeOutput(sa_solver.ulds, sa_solver.packages)
