from structs import ULD, Package
from solver import Solver
import csv
from collections import defaultdict


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

    print(" Total Cost = ", cost)


# def generateOutput():
#     f = open("output.csv", mode="w")
#     outputCSV = csv.writer(f)
#     packages.sort(key=lambda x: (str(x.ULD), list(x.position)))
#     for package in packages:
#         outputCSV.writerow(
#             [package.id, package.ULD, package.position, package.getDimensions()])


def generateOutput():
    f = open("output.csv", mode="w", newline='')
    outputCSV = csv.writer(f)

    # Sort packages for ordered output
    packages.sort(key=lambda x: (str(x.ULD), list(x.position)))

    # Write package details
    for package in packages:
        outputCSV.writerow([
            package.id,
            package.ULD,
            package.position,
            package.weight,
            package.getDimensions()
        ])

    # Group packages by ULD
    uld_packages = defaultdict(list)
    for package in packages:
        if package.ULD != -1:  # Ignore unallocated packages
            uld_packages[package.ULD].append(package)

    # Calculate and write COM for each ULD
    for uld_id, uld_pkg_list in uld_packages.items():
        # Get the ULD object and its dimensions
        uld = next((uld for uld in ulds if uld.id == uld_id), None)
        if not uld:
            continue

        total_weight = sum(pkg.weight for pkg in uld_pkg_list)
        if total_weight == 0:  # Avoid division by zero
            continue

        # Calculate weighted sum of positions
        weighted_sum = [0, 0, 0]
        for pkg in uld_pkg_list:
            # Package center position = package position + half dimensions
            center_position = [
                pkg.position[i] + pkg.getDimensions()[i] / 2 for i in range(3)
            ]
            weighted_sum = [
                weighted_sum[i] + center_position[i] * pkg.weight
                for i in range(3)
            ]

        # Calculate COM
        com = [weighted_sum[i] / total_weight for i in range(3)]

        # Write COM and dimensions of the ULD to the output CSV
        outputCSV.writerow([
            f"ULD-{uld_id}",
            "COM",
            com,
            "Dimensions",
            [uld.length, uld.width, uld.height]
        ])

    f.close()


getPackages()
getULD()


solver = Solver(packages, ulds)
solver.solve()
metrics(ulds)
generateOutput()
