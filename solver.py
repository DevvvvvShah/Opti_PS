

# Strategy:
# greedily pack the boxes into the ULDs
# sort the ULDs by volume
# sort the boxes by volume
# sort the boxes by priority
# pack the boxes in the ULDs

class Solver:
    
    def __init__(self,packages,ulds):
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

    #sorting all the taken packages
    def sortPackages(self,packages):
        packages.sort(key=lambda x:
                        (x.cost,x.getVolume())
                                 ,reverse=True)
        
    #sorting the intra-uld packages
    def sortULDPackages(self,packages):
        packages.sort(key=lambda x:
                        (x.getVolume())
                                 ,reverse=True)

    def sortULDs(self):
        self.ulds.sort(key=lambda x:  x.getVolume(),reverse=True)

    #select packages to even be considered for packing
    def selectPackages(self):
        self.economy.sort(key=lambda x: (x.cost/(x.getVolume()+x.weight)),reverse=True)
        # economyTaking = self.economy
        economyTaking = self.economy[0:150]
        self.takenPackages = self.priority + economyTaking

    #fit the packages into the uld
    def fitPackages(self,packages,uld,corners):
        takenPackages = []
        for package in packages:
            if package.ULD == -1: 
                done = False
                corners.sort(key=lambda x: (x[1]*x[1] + x[2]*x[2] + x[0]*x[0]))
                for corner in corners:
                    flag = uld.addBox(package,corner)
                    if flag:
                        #remove this corner and add the other 7 corner 
                        corners.remove(corner)
                        new_corners = uld.getNewCorners(package, corner)
                        corners.extend(new_corners)
                        # corners.sort(key=lambda x: x[0])
                        # corners.sort(key=lambda x: x[1])
                        corners.sort(key=lambda x: (x[1]*x[1] + x[2]*x[2] + x[0]*x[0]))
                        takenPackages.append(package)
                        done = True
                        break
                if done and package.priority == "Priority":
                    self.priorityDone+=1
        return corners, takenPackages
    

    def assignPackages(self):
        uldMapping = {}
        #initial fit for figuring out the assignment of packages to ulds
        for uld in self.ulds:
            print("Considering ULD: ",uld.id)
            [_, packagesInULD] = self.fitPackages(self.takenPackages,uld,[[0,0,0]])
            uldMapping[uld.id] = packagesInULD
        
        for uld in self.ulds:
            uld.clearBin()
        
        return uldMapping
    def solve(self):
        self.selectPackages()
        self.sortPackages(self.takenPackages)
        self.sortULDs()

        uldMapping = self.assignPackages()

        cornermap = {}
        for uld in self.ulds:
            print("start new uld !!")
            
            print(f"id: {uld.id}, length: {uld.length}, width: {uld.width}, height: {uld.height}, weight: {uld.weight_limit}")
            for package in uldMapping[uld.id]:
                print(f"id: {package.id}, length: {package.length}, width: {package.width}, height: {package.height}, weight: {package.weight}")
        #refit the packages into its uld
        
        # for uld in self.ulds:
        #     [corners, _] = self.fitPackages(self.takenPackages,uld,[[0,0,0]])
        for uld in self.ulds:
            self.sortULDPackages(uldMapping[uld.id])
            [corners, _] = self.fitPackages(uldMapping[uld.id],uld,[[0,0,0]])
            cornermap[uld.id] = corners
        
        self.sortPackages(self.takenPackages)

        #see if we can fit the remaining packages into the ulds
        for uld in self.ulds:
            [corners, _] = self.fitPackages(self.takenPackages,uld,cornermap[uld.id])
            cornermap[uld.id] = corners
   
    def calculateRemainingVolume(self, uld, package, corner):
        remaining_volume = uld.getVolume() - sum(p.getVolume() for p in uld.packages) - package.getVolume()
        return remaining_volume
        
    def bestFitPackage(self,package,corners):
        if package.priority == "Priority":
            priorityULDs = ["U5", "U6", "U3","U4"]
            bestULD = None
            bestCorner = None
            bestDiff = 1
            for uld in self.ulds:
                if uld.id in priorityULDs:
                    for corner in corners[uld.id]:
                        # print(corner, uld.id)
                        if uld.checkBox(package,corner):
                            f=1
                        else:
                            # print("not possible")
                            continue
                        # print(self.calculateRemainingVolume(uld, package, corner))
                        if bestDiff > self.calculateRemainingVolume(uld, package, corner) / uld.getVolume():
                            bestDiff = self.calculateRemainingVolume(uld, package, corner) / uld.getVolume()
                            bestULD = uld
                            bestCorner = corner
            # if(bestULD != None):
                # print("priority : " ,bestULD.id)
            if bestULD != None:
                print(package.priority, bestULD.id)
            return [bestULD, bestCorner]
    
        else:
            bestULD = None
            bestCorner = None
            bestDiff = 1
            for uld in self.ulds:
                for corner in corners[uld.id]:
                    if uld.checkBox(package,corner):
                            f=1
                    else:
                        continue
                    if bestDiff > self.calculateRemainingVolume(uld, package, corner) / uld.getVolume():
                        bestDiff = self.calculateRemainingVolume(uld, package, corner) / uld.getVolume()
                        bestULD = uld
                        bestCorner = corner
            # print(bestULD.id, bestCorner)
            return [bestULD, bestCorner]
    def findResidualDimensions(self, uld, corner): 
        rx = uld.length - corner[0]
        ry = uld.width - corner[1]
        rz = uld.height - corner[2]
        # find residual dimensions from the corner 
        for package in uld.packages:
            if(package.position[0] - corner[0] >= 0):
                rx = min(rx, package.position[0] - corner[0])
            if(package.position[1] - corner[1] >= 0):
                ry = min(ry, package.position[1] - corner[1])
            if(package.position[2] - corner[2] >= 0):
                rz = min(rz, package.position[2] - corner[2])
        return (rx)*ry*rz
    def bestFitSolveFV(self):
        #choose the best corner out of all ulds for the package
        corners = {}
        for uld in self.ulds:
            corners[uld.id] = [[0,0,0]]
        
        self.selectPackages()
        # self.sortPackages(self.takenPackages)
        self.sortULDs()
        for package in self.priority:
            # for uld in self.ulds:
            [uld, corner] = self.bestFitPackage(package,corners)
            if uld != None:
                uld.addBox(package,corner)
                new_corners = uld.getNewCorners(package, corner)
                corners[uld.id].remove(corner)
                corners[uld.id].extend(new_corners)
                if package.priority == "Priority":
                    self.priorityDone+=1
        for package in self.economy:
            # for uld in self.ulds:
            [uld, corner] = self.bestFitPackage(package,corners)
            if uld != None:
                uld.addBox(package,corner)
                new_corners = uld.getNewCorners(package, corner)
                corners[uld.id].remove(corner)
                corners[uld.id].extend(new_corners)
                if package.priority == "Priority":
                    self.priorityDone+=1
    def bestFitSolveRS(self):
        self.selectPackages()
        # self.sortPackages(self.takenPackages)
        self.sortULDs()
        for uld in self.ulds:
            print("Considering ULD: ",uld.id)
            corners = [[0,0,0]]
            for package in self.takenPackages:
                if package.ULD == -1: 
                    print("Considering package: ",package.id, package.priority, "for this ULD ",uld.id)
                    done = False
                    possibleCorners = [] 
                    for corner in corners:
                        if(uld.checkBox(package,corner)):
                            possibleCorners.append(corner)
                    # print("Possible corners: ",possibleCorners)
                    if(len(possibleCorners) == 0):
                        print("Cant fit the package")
                        continue
                    bestCorner = possibleCorners[0]
                    bestResidual = self.findResidualDimensions(uld, bestCorner)
                    for corner in possibleCorners:
                        residual = self.findResidualDimensions(uld, corner)
                        if residual > bestResidual:
                            bestCorner = corner
                            bestResidual = residual
                    if(uld.addBox(package,bestCorner)):
                            corners.remove(bestCorner)
                            new_corners = uld.getNewCorners(package, bestCorner)
                            corners.extend(new_corners)
                            done = True
                            # break
                    if done and package.priority == "Priority":
                        self.priorityDone+=1
          
        