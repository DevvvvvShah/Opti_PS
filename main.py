from structs import ULD,Package
from solver import Solver
import csv








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
    
    print(" Total Cost = ", cost)


def writeOutput(ulds,packages):
    
    f = open("output.csv",mode="w")
    writer = csv.writer(f)
    for uld in ulds:
        uld.packages.sort(key=lambda x: x.position)
        for package in uld.packages:
            writer.writerow([package.id,uld.id,package.position,package.position+package.getDimensions()])
    cost = 0
    for package in packages:
        if package.ULD == -1: cost+=package.cost
    for uld in ulds:
        if uld.isPriority: cost+=k
    writer.writerow(["Cost",cost])
    f.close()

getPackages()
getULD()


solver = Solver(packages,ulds)
solver.solve()
metrics(ulds)
writeOutput(ulds,packages)