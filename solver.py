import math

class Solver:
    def __init__(self, packages, ulds):
        self.packages = packages
        self.ulds = ulds
        self.priorityDone = 0
        self.priority = []
        self.economy = []
        self.takenPackages = []

        for package in packages:
            if package.priority == "Priority":
                self.priority.append(package)
            else:
                self.economy.append(package)

    # Helper function: Calculate Euclidean distance from (0, 0, 0)
    #changed
    def calculateEuclideanDistance(self, point):
        return math.sqrt(point[0] ** 2 + point[1] ** 2 + point[2] ** 2)

    # Sort all taken packages
    def sortPackages(self, packages):
        packages.sort(key=lambda x: (x.cost, x.getVolume()), reverse=True)

    # Sort the intra-ULD packages
    def sortULDPackages(self, packages):
        packages.sort(key=lambda x: x.getVolume(), reverse=True)

    def sortULDs(self):
        self.ulds.sort(key=lambda x: x.getVolume(), reverse=True)

    # Select packages to even be considered for packing
    def selectPackages(self):
        # self.economy.sort(key=lambda x: (x.cost / (x.getVolume() + x.weight)), reverse=True)
        economyTaking = self.economy[:150]  # Limit number of economy packages
        self.takenPackages = self.priority + economyTaking

    # Fit the packages into the ULD
    def fitPackages(self, packages, uld, corners):# P : this is fitpackagePriority
        takenPackages = []

        for package in packages:
            if package.ULD == -1: 
                done = False
                # Sort corners by their Euclidean distance from (0, 0, 0)
                # P : we want to iterate through all corner and rotation and one which will give minimum distance of new corner is taken into account
                # here we will implement above thing

                corners.sort(key=lambda corner: self.calculateEuclideanDistance(corner)) #sort on basis of euclidian
                for corner in corners:
                    if uld.addBox(package, corner):
                        # Remove this corner and add the other 7 new corners
                        corners.remove(corner)
                        new_corners = uld.getNewCorners(package, corner)
                        corners.extend(new_corners)

                        # Re-sort corners by Euclidean distance for the next iteration
                        corners.sort(key=lambda x: self.calculateEuclideanDistance(x))
                        
                        takenPackages.append(package)
                        done = True
                        break
                if done and package.priority == "Priority":
                    self.priorityDone += 1
        return corners, takenPackages
    
    # P : we will define new fitpackageEconomy only difference will be we will iterate through uld,package,corner,rotation rest will be same

    def assignPackages(self):
        uldMapping = {}
        # Initial fit for figuring out the assignment of packages to ULDs
        for uld in self.ulds:
            print("Considering ULD: ", uld.id)
            [_, packagesInULD] = self.fitPackages(self.takenPackages, uld, [[0, 0, 0]])
            uldMapping[uld.id] = packagesInULD

        for uld in self.ulds:
            uld.clearBin()

        return uldMapping

    def solve(self):
        self.selectPackages()
        # self.sortPackages(self.takenPackages)
        self.sortULDs()

        uldMapping = self.assignPackages()

        cornermap = {}
        # Refit the packages into their respective ULD
        for uld in self.ulds:
            self.sortULDPackages(uldMapping[uld.id])
            [corners, _] = self.fitPackages(uldMapping[uld.id], uld, [[0, 0, 0]])
            cornermap[uld.id] = corners

        self.sortPackages(self.takenPackages)

        # See if we can fit the remaining packages into the ULDs
        for uld in self.ulds:
            [corners, _] = self.fitPackages(self.takenPackages, uld, cornermap[uld.id])
            cornermap[uld.id] = corners

