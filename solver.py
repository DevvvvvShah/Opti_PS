

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
        self.ulds.sort(key=lambda x: x.getVolume(),reverse=True)

    #select packages to even be considered for packing
    def selectPackages(self):
        # self.economy.sort(key=lambda x: (x.cost/(x.getVolume()+x.weight)),reverse=True)
        # economyTaking = self.economy
        # economyTaking = self.economy[0:150]
        self.takenPackages = self.packages

    #fit the packages into the uld
    def fitPackages(self,packages,uld,corners):
        takenPackages = []
        for package in packages:
            if package.ULD == -1: 
                done = False
                for corner in corners:
                    if(uld.addBox(package,corner)):
                        #remove this corner and add the other 7 corner 
                        corners.remove(corner)
                        new_corners = uld.getNewCorners(package, corner)
                        corners.extend(new_corners)
                        # corners.sort(key=lambda x: x[0])
                        # corners.sort(key=lambda x: x[1])
                        corners.sort(key=lambda x: x[2])
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
        # self.sortPackages(self.takenPackages)
        self.sortULDs()

        uldMapping = self.assignPackages()

        cornermap = {}
        #refit the packages into it's uld
        for uld in self.ulds:
            self.sortULDPackages(uldMapping[uld.id])
            [corners, _] = self.fitPackages(uldMapping[uld.id],uld,[[0,0,0]])
            cornermap[uld.id] = corners
        
        # self.sortPackages(self.takenPackages)

        #see if we can fit the remaining packages into the ulds
        for uld in self.ulds:
            [corners, _] = self.fitPackages(self.takenPackages,uld,cornermap[uld.id])
            cornermap[uld.id] = corners

