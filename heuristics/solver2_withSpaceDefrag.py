import math

from utils.structs import Axis

class Solver2:
    def __init__(self, packages, ulds, permutation):
        self.packages = packages
        self.ulds = ulds
        self.priority = []
        self.economy = []
        self.takenPackages = []

        for package in packages:
            if package.priority == "Priority":
                self.priority.append(package)
            else:
                self.economy.append(package)

    def calculateEuclideanDistance(self, point):
        return math.sqrt(point[0] ** 2 + point[1] ** 2 + point[2] ** 2)
    
    def sortPackagesAssignment(self, packages):

        k=4
        k2=3

        priority_packages = [p for p in packages if p.priority == "Priority"]
        non_priority_packages = [p for p in packages if p.priority != "Priority"]
        
        priority_packages.sort(key=lambda x: x.getVolume(), reverse=True)
        non_priority_packages.sort(key=lambda x: x.cost**3/(x.getVolume()**2 + x.weight**2), reverse=True)
        
        packages[:] = priority_packages + non_priority_packages
   
    
    def sortULDPackages(self, packages):
        packages.sort(key=lambda x: (math.floor(x.getDimensions()[2]/10),(x.getVolume())/(x.getDimensions()[2])), reverse=True)
    
    permuationsAll = [[4,5,6,1,2,3],[4,5,6,2,3,1],[4,5,6,3,1,2],[4,5,6,1,3,2],[4,5,6,2,1,3],[4,5,6,3,2,1],
                      [4,6,5,1,2,3],[4,6,5,2,3,1],[4,6,5,3,1,2],[4,6,5,1,3,2],[4,6,5,2,1,3],[4,6,5,3,2,1],
                      [5,4,6,1,2,3],[5,4,6,2,3,1],[5,4,6,3,1,2],[5,4,6,1,3,2],[5,4,6,2,1,3],[5,4,6,3,2,1],    
                      [5,6,4,1,2,3],[5,6,4,2,3,1],[5,6,4,3,1,2],[5,6,4,1,3,2],[5,6,4,2,1,3],[5,6,4,3,2,1],
                      [6,4,5,1,2,3],[6,4,5,2,3,1],[6,4,5,3,1,2],[6,4,5,1,3,2],[6,4,5,2,1,3],[6,4,5,3,2,1],
                      [6,5,4,1,2,3],[6,5,4,2,3,1],[6,5,4,3,1,2],[6,5,4,1,3,2],[6,5,4,2,1,3],[6,5,4,3,2,1]]                      

    def sortULDs(self,permutation):
        currPermutation=self.permuationsAll[permutation]
       
        mapuldtoperm = {"U4": currPermutation[0], "U5": currPermutation[1], "U6": currPermutation[2], "U1": currPermutation[3], "U2": currPermutation[4], "U3": currPermutation[5]}   
        #print(self.ulds)

        self.ulds.sort(key=lambda x: mapuldtoperm[x.id], reverse=True)


    def fitPackages(self, packages, uld, corners, isassigning = 0):# P : this is fitpackagePriority
        takenPackages = []
      
        for package in packages:
            uld.calculatePushLimit()
            
            if package.ULD == -1: 
                done = False

                corners.sort(key=lambda corner: self.calculateEuclideanDistance(corner)) #sort on basis of euclidian
                for corner in corners:
                    if uld.addBox(package, corner):
                        # Remove this corner and add the other 7 new corners
                        corners.remove(corner)
                        new_corners = uld.getNewCorners(package)
                        corners.extend(new_corners)

                        # Re-sort corners by Euclidean distance for the next iteration
                        corners.sort(key=lambda x: self.calculateEuclideanDistance(x))
                        
                        takenPackages.append(package)
                        done = True
                        break
                    # elif(uld.pushAddBox(package, corner)):
                    #     done = True
                    #     takenPackages.append(package)
                    #     corners = uld.recalculate_corners()
                    #     corners.sort(key=lambda x: self.calculateEuclideanDistance(x))
                    #     break
        
                    
        # uld.plotULD()

        #print(len(takenPackages))        
        return corners, takenPackages
    
    # P : we will define new fitpackageEconomy only difference will be we will iterate through uld,package,corner,rotation rest will be same

    def assignPackagesPriority(self):

        # Initial fit for figuring out the assignment of packages to ULDs
        priority_bin = 3
        for uld in self.ulds:
            #print("Assigning Priorty ULD: ", uld.id)
            # print(uld.length,uld.width,uld.height)
            [_, packagesInULD] = self.fitPackages(self.packages, uld, [[0, 0, 0]],True)
            c = 0
            
            self.takenPackages.extend(packagesInULD)
            priority_bin-=1
            if(priority_bin==0):
                break
        
        
        for uld in self.ulds:
            uld.clearBin()

        return
    
    def assignPackagesNormal(self):

        # Initial fit for figuring out the assignment of packages to ULDs
        priority_bin = 3
        for uld in self.ulds:
            if(priority_bin!=0):
                priority_bin-=1
                continue
            #print("Assigning Normal ULD: ", uld.id)
            [_, packagesInULD] = self.fitPackages(self.packages, uld, [[0, 0, 0]],True)
            self.takenPackages.extend(packagesInULD)
        
        priority_bin = 3
        for uld in self.ulds:
            if(priority_bin!=0):
                priority_bin-=1
                continue
            uld.clearBin()

        return
    
    

    def fit_int_ulds(self,packages,ulds,cornermap,mess):
        for ii,uld in enumerate(ulds):
            
            #print("Fitting " +  mess + " ULD: ", uld.id)
            [corners, _] = self.fitPackages(packages, uld, cornermap[uld.id])
            done = False
            cornermap[uld.id] = corners
            for unpacked_package in packages:
                if unpacked_package.ULD == -1:
                    for jj in range(ii+1):
                        ulds[jj].calculatePushLimit()
                        for poss_replace in ulds[jj].packages:
                            if(ulds[jj].inflate_and_replace(unpacked_package,poss_replace)):
                                cornermap[uld.id] = ulds[jj].recalculate_corners()
                                cornermap[uld.id].sort(key=lambda x: self.calculateEuclideanDistance(x))
                                done = True
                                break
                        if done:
                            break            
           
        return cornermap

    def solve(self,permutation):

        self.sortPackagesAssignment(self.packages)
        self.sortULDs(permutation)

        self.assignPackagesPriority()

        cornermap = {}
        for uld in self.ulds:
            cornermap[uld.id] = [[0, 0, 0]]

        # Refit the packages into their respective ULD
        self.sortULDPackages(self.takenPackages)
        cornermap = self.fit_int_ulds(self.takenPackages, self.ulds, cornermap,"Proirity")
        # for uld in self.ulds:
        #     # self.sortULDPackages(uldMapping[uld.id])
        #     print("Fitting Priority ULD: ", uld.id)
        #     [corners, _] = self.fitPackages(self.takenPackages, uld, [[0, 0, 0]])
        #     cornermap[uld.id] = corners

        self.takenPackages = []
        self.assignPackagesNormal()
        self.sortULDPackages(self.takenPackages)
        
        cornermap = self.fit_int_ulds(self.takenPackages, self.ulds, cornermap,"Normal")
        

        self.sortULDPackages(self.packages)

        cornermap = self.fit_int_ulds(self.packages, self.ulds, cornermap,"Remaining")

        for uld in self.ulds:
            for package in uld.packages:
                for axis in Axis.ALL:
                    if uld.project(package,axis) != -1:
                        package.position[axis] = uld.project(package,axis)


        # self.ulds[0].plotULD()
        # self.ulds[1].plotULD()
        # self.ulds[2].plotULD()
        # self.ulds[3].plotULD()
        # self.ulds[4].plotULD()
        # self.ulds[5].plotULD()


# 4,13,15,17,19,20,21,23,
# 23,19,17,13