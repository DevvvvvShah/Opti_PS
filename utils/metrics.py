
def metrics(packages, ulds,k):


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

    # print("{0} out of {1} packages taken".format(packagesTotalTaken,packagesTotal))
    # print("{0} out of {1} priority packages taken".format(packagesPriorityTaken,packagesPriority))
    # print("{0} out of {1} economy packages taken".format(packagesEconomyTaken,packagesEconomy))
    cost=0

    for package in packages:
        if package.ULD == -1: cost+=package.cost
    print("Cost without accounting for priority uld (k) = ", cost)
    
    for uld in ulds:
        if uld.isPriority: cost+=k
    
    print(" Total Cost = ", cost)
    return cost
