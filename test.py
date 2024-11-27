from structs import ULD,Package
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
            package = Package(p[1],p[2],p[3],p[4],p[0],p[5],p[6])
            packages.append(package)
        else:
            package = Package(p[1],p[2],p[3],p[4],p[0],p[5])
            packages.append(package)

def getULD():
    f = open("ULD.csv", mode="r")
    uldCSV = csv.reader(f)
    for u in uldCSV:
        uld = ULD(u[1],u[2],u[3],u[4],u[0])
        ulds.append(uld)

getPackages()
getULD()

def metrics(ulds):
    freeSpace = 0
    totalSpace = 0
    freeWeight = 0
    totalWeight = 0
    for uld in ulds:
        uldfreeSpace = uld.getVolume()
        uldtotalSpace = uld.getVolume()
        totalSpace+=uld.getVolume()
        freeSpace+=uld.getVolume()
        totalWeight+=uld.weight_limit
        freeWeight+=uld.weight_limit
        uldfreeWeight = uld.weight_limit
        uldtotalWeight = uld.weight_limit
        for package in uld.packages:
            uldfreeSpace-=package.getVolume()
            freeSpace-=package.getVolume()
            uldfreeWeight-=package.weight
            freeWeight-=package.weight
        print(str(uldfreeSpace/uldtotalSpace*100)+"% free space in uld ",uld.id)
        print(str(uldfreeWeight/uldtotalWeight*100)+"% free weight in uld ",uld.id)
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
        packagesTotal+=1
        if package.ULD != -1: packagesTotalTaken+=1
        if package.priority == "Priority":
            packagesPriority+=1
            if package.ULD != -1: packagesPriorityTaken+=1
        else:
            packagesEconomy+=1
            if package.ULD != -1: packagesEconomyTaken+=1

    print("{0} out of {1} packages taken".format(packagesTotalTaken,packagesTotal))
    print("{0} out of {1} priority packages taken".format(packagesPriorityTaken,packagesPriority))
    print("{0} out of {1} economy packages taken".format(packagesEconomyTaken,packagesEconomy))

    for package in packages:
        if package.ULD == -1: cost+=package.cost
    print("Cost without accounting for priority uld (k) = ", cost)
    for uld in ulds:
        if uld.isPriority: cost+=k
    
    print("The cost is ",cost)
    return cost


class GeneticAlgorithmSolver:

    def __init__(self, packages, ulds, population_size, crossover_rate, mutation_rate, num_generations):
        self.packages = packages
        self.ulds = ulds
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.num_generations = num_generations
        self.k = 5000  # Cost for each ULD containing priority packages

    def initialize_population(self):
        """Generate a random initial population of permutations."""
        population = []
        for _ in range(self.population_size):
            individual = self.packages[:]
            random.shuffle(individual)
            population.append(individual)
        return population

    def fitness(self, ordering):
        """Evaluate the fitness (cost) of a given ordering."""
        solver = Solver(ordering, self.ulds)
        solver.solve()
        return metrics(solver.ulds)  # Lower cost = better fitness

    def selection(self, population, fitness_scores):
        """Select parents based on fitness using a roulette wheel approach."""
        total_fitness = sum(fitness_scores)
        probabilities = [score / total_fitness for score in fitness_scores]
        selected_index = random.choices(range(len(population)), probabilities, k=1)[0]
        return population[selected_index]

    def crossover(self, parent1, parent2):
        """Perform ordered crossover (OX) on two parents."""
        if random.uniform(0, 1) > self.crossover_rate:
            return parent1[:]  # No crossover; return parent1 as offspring

        start, end = sorted(random.sample(range(len(parent1)), 2))
        child = [None] * len(parent1)

        # Copy the crossover segment from parent1
        child[start:end] = parent1[start:end]

        # Fill the remaining positions with the order from parent2
        p2_elements = [item for item in parent2 if item not in child]
        current_idx = 0
        for i in range(len(child)):
            if child[i] is None:
                child[i] = p2_elements[current_idx]
                current_idx += 1

        return child

    def mutate(self, individual):
        """Perform swap mutation on an individual."""
        if random.uniform(0, 1) < self.mutation_rate:
            idx1, idx2 = random.sample(range(len(individual)), 2)
            individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
        return individual

    def solve(self):
        # Initialize population
        xy = sorted(self.packages,key=lambda x: (x.cost, x.getVolume()), reverse=True)
        population = []

        for _ in range(self.population_size):

            neighbor = xy[:]
            
            for j in range(10):
                idx1, idx2 = random.sample(range(len(neighbor)), 2)
                neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]

            population.append(neighbor)

        # Track the best solution
        best_individual = None
        best_fitness = float('inf')

        for generation in range(self.num_generations):
            # Evaluate fitness for each individual
            fitness_scores = [self.fitness(individual) for individual in population]

            # Update the best solution
            for i, score in enumerate(fitness_scores):
                if score < best_fitness:
                    best_fitness = score
                    best_individual = population[i]

            # Generate the next generation
            new_population = []

            for _ in range(self.population_size):

                # Selection
                parent1 = self.selection(population, fitness_scores)
                parent2 = self.selection(population, fitness_scores)

                # Crossover
                offspring = self.crossover(parent1, parent2)

                # Mutation
                offspring = self.mutate(offspring)

                new_population.append(offspring)

            population = new_population  # Replace old population

            print(f"Generation {generation}, Best Fitness: {best_fitness}")

        # Return the best solution and its fitness
        return best_individual, best_fitness

# Initialize parameters for GA
population_size = 10
crossover_rate = 0.8
mutation_rate = 0.2
num_generations = 10

# Instantiate the GA solver
ga_solver = GeneticAlgorithmSolver(packages, ulds, population_size, crossover_rate, mutation_rate, num_generations)
best_ordering, best_cost = ga_solver.solve()

# Final packing with the best ordering
solver = Solver(best_ordering, ulds)
solver.solve()
