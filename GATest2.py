from structs import ULD, Package
from solver import Solver
import csv
import random
import math
import numpy as np

k = 5000  # Cost for each ULD containing priority packages
ulds = []
packages = []

# Read packages from CSV


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

# Read ULDs from CSV


def getULD():
    f = open("ULD.csv", mode="r")
    uldCSV = csv.reader(f)
    for u in uldCSV:
        uld = ULD(u[1], u[2], u[3], u[4], u[0])
        ulds.append(uld)


getPackages()
getULD()


# Metrics function
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
        print(f"{(uldfreeSpace / uldtotalSpace) * 100}% free space in ULD {uld.id}")
        print(f"{(uldfreeWeight / uldtotalWeight) * 100}% free weight in ULD {uld.id}")
    print(f"{(freeSpace / totalSpace) * 100}% free ULD space")
    print(f"{(freeWeight / totalWeight) * 100}% free ULD weight")
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
    print(f"{packagesPriorityTaken} out of {packagesPriority} priority packages taken")
    print(f"{packagesEconomyTaken} out of {packagesEconomy} economy packages taken")

    for package in packages:
        if package.ULD == -1:
            cost += package.cost
    print("Cost without accounting for priority ULD (k) = ", cost)
    for uld in ulds:
        if uld.isPriority:
            cost += k

    print("The cost is ", cost)
    return cost


# Biased Random-Key Genetic Algorithm (BRKGA)
class BRKGA:
    def __init__(self, packages, ulds, population_size, elite_size, crossover_rate, mutation_rate, num_generations, max_stagnation=5):
        self.packages = packages
        self.ulds = ulds
        self.population_size = population_size
        self.elite_size = elite_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.num_generations = num_generations
        self.k = 5000  # Cost for each ULD containing priority packages
        # Early stop if no improvement after this many generations
        self.max_stagnation = max_stagnation

    def initialize_population(self):
        """Generate a random initial population of solutions."""
        population = []
        for _ in range(self.population_size):
            individual = np.random.uniform(
                0.0, 1.0, size=2 * len(self.packages))  # Random vector of size 2*n
            population.append(individual)
        return population

    def fitness(self, individual):
        """Evaluate the fitness (cost) of a given individual."""
        # Decode the solution
        # Decoding Box Packing Sequence (BPS)
        bps = np.argsort(individual[:len(self.packages)])
        # Vector of Box Orientations (VBO)
        vbo = individual[len(self.packages):]
        # Create the Solver with the decoded solution
        solver = Solver([self.packages[i] for i in bps], self.ulds)
        solver.solve()
        # Return the fitness value (lower cost = better)
        return metrics(solver.ulds)

    def partition(self, population, fitness_scores):
        """Partition the population into elite and non-elite groups."""
        sorted_indices = np.argsort(fitness_scores)
        elite = [population[i] for i in sorted_indices[:self.elite_size]]
        non_elite = [population[i] for i in sorted_indices[self.elite_size:]]
        return elite, non_elite

    def selection(self, population, fitness_scores):
        """Select a parent using roulette wheel selection."""
        total_fitness = sum(fitness_scores)
        probabilities = [score / total_fitness for score in fitness_scores]
        selected_index = random.choices(
            range(len(population)), probabilities, k=1)[0]
        return population[selected_index]

    def crossover(self, parent1, parent2):
        """Perform crossover between two parents."""
        if random.uniform(0, 1) > self.crossover_rate:
            return parent1[:]  # No crossover, return parent1 as offspring
        crossover_point = random.randint(1, len(parent1) // 2)
        offspring = np.concatenate(
            [parent1[:crossover_point], parent2[crossover_point:]])
        return offspring

    def mutate(self, individual):
        """Perform mutation by swapping two random elements."""
        if random.uniform(0, 1) < self.mutation_rate:
            idx1, idx2 = random.sample(range(len(individual)), 2)
            individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
        return individual

    def solve(self):
        # Initialize population
        population = self.initialize_population()

        # Track the best solution
        best_individual = None
        best_fitness = float('inf')

        stagnation_counter = 0  # Counter for no improvement

        for generation in range(self.num_generations):
            # Evaluate fitness for each individual
            fitness_scores = [self.fitness(individual)
                              for individual in population]

            # Update the best solution
            for i, score in enumerate(fitness_scores):
                if score < best_fitness:
                    best_fitness = score
                    best_individual = population[i]
                    stagnation_counter = 0  # Reset stagnation counter when improvement happens
                else:
                    stagnation_counter += 1  # Increment stagnation counter when no improvement

            # Prevent premature early stopping
            if stagnation_counter >= self.max_stagnation and generation > 5:
                print(
                    f"Stopping due to stagnation after {generation} generations.")
                break

            # Generate the next generation
            elite, non_elite = self.partition(population, fitness_scores)

            # Generate offspring using crossover
            new_population = elite[:]  # Keep the elite individuals
            while len(new_population) < self.population_size:
                parent1 = self.selection(population, fitness_scores)
                parent2 = self.selection(population, fitness_scores)
                offspring = self.crossover(parent1, parent2)
                offspring = self.mutate(offspring)
                new_population.append(offspring)

            population = new_population  # Replace old population with new one

            print(f"Generation {generation}, Best Fitness: {best_fitness}")

        return best_individual, best_fitness


# Initialize parameters for BRKGA
population_size = 10
elite_size = 2
crossover_rate = 0.8
mutation_rate = 0.2
num_generations = 20  # Set to a reasonable number of generations
max_stagnation = 5  # Early stop if no improvement for 5 generations

# Instantiate the BRKGA solver
brkga_solver = BRKGA(packages, ulds, population_size,
                     elite_size, crossover_rate, mutation_rate, num_generations, max_stagnation)
best_ordering, best_cost = brkga_solver.solve()

# Decode the best ordering (random key vector) to get the correct order of packages
# Decoding Box Packing Sequence (BPS)
bps = np.argsort(best_ordering[:len(packages)])
ordered_packages = [packages[i]
                    for i in bps]  # Reorganize packages according to BPS

# Now, pass the ordered list of packages to the Solver
solver = Solver(ordered_packages, ulds)
solver.solve()
