


#Always LWH is default unless specified otherwise

def isIntersecting(package1,package2,x,y):
    d1 = package1.getDimensions()
    d2 = package2.getDimensions()

    cx1 = package1.position[x] + d1[x]/2
    cy1 = package1.position[y] + d1[y]/2
    cx2 = package2.position[x] + d2[x]/2
    cy2 = package2.position[y] + d2[y]/2

    ix = max(cx1, cx2) - min(cx1, cx2)
    iy = max(cy1, cy2) - min(cy1, cy2)

    return ix < (d1[x]+d2[x])/2 and iy < (d1[y]+d2[y])/2



class Rotation:
    LWH = 0
    LHW = 1
    WLH = 2
    WHL = 3
    HLW = 4
    HWL = 5

    ALL = [LWH,LHW,WLH,WHL,HLW,HWL]
 
class Axis:
    LENGTH = 0
    WIDTH = 1
    HEIGHT = 2

    ALL = [LENGTH, WIDTH, HEIGHT]

class Package:

    def __init__(self, length, width, height, weight,id,priority,cost = 10000000):
        self.position = [-1,-1,-1] #default if not placed
        self.ULD = -1 #default when ULD not chosen
        self.length = int(length)
        self.width = int(width)
        self.height = int(height)
        [self.length,self.width,self.height] = sorted([self.length,self.width,self.height])
        self.weight = int(weight)
        self.id = id
        self.priority = priority
        self.cost = int(cost)
        self.rotation = Rotation.LWH
        self.pqPriority = 0

    def getMaxBase(self):
        #already sorted
        return self.length*self.width

    def getVolume(self):
        return self.length*self.width*self.height
    

    def isIntersecting(self,other):
        return (isIntersecting(self,other,Axis.LENGTH,Axis.WIDTH) 
                and isIntersecting(self,other,Axis.HEIGHT,Axis.WIDTH)
                and isIntersecting(self,other,Axis.LENGTH,Axis.HEIGHT))


    def getDimensions(self):
        dim = []
        if self.rotation == Rotation.LWH: dim = [self.length,self.width,self.height]
        if self.rotation == Rotation.WLH: dim = [self.width,self.length,self.height]
        if self.rotation == Rotation.HLW: dim = [self.height,self.length,self.width]
        if self.rotation == Rotation.HWL: dim = [self.height,self.width,self.length]
        if self.rotation == Rotation.LHW: dim = [self.length,self.height,self.width]
        if self.rotation == Rotation.WHL: dim = [self.width,self.height,self.length]

        return dim

    def getCenterOfMass(self):
        return [self.position[0] + self.length/2, self.position[1] + self.width/2, self.position[2] + self.height/2]
    
class ULD:
    def __init__(self,length,width,height,weight_limit,id):
        self.length = int(length)
        self.width = int(width)
        self.height = int(height)
        self.weight_limit = int(weight_limit)
        self.id = id
        self.isPriority = False
        self.packages = []
    
    def weightLeft(self):
        curr = self.weight_limit
        for package in self.packages: curr-=package.weight
        return curr
    
    def getVolume(self):
        return self.length*self.width*self.height
    
    def checkBox(self, currPackage, pivot, rotations = Rotation.ALL):
        prevPosition = currPackage.position
        currPackage.position = pivot
        valid = False
        if (self.weightLeft() < currPackage.weight) : 
            return valid
        for rotation in rotations:
            currPackage.rotation = rotation
            dimensions = currPackage.getDimensions()
            if (
                self.length < pivot[0] + dimensions[0] or
                self.width < pivot[1] + dimensions[1] or
                self.height < pivot[2] + dimensions[2] or
                pivot[0] < 0 or pivot[1] < 0 or pivot[2] < 0
            ): continue

            valid = True

            for package in self.packages:
                if package.isIntersecting(currPackage):
                    valid = False
                    break
        currPackage.position = prevPosition
        return valid
    
    def addBoxBestRotation(self, currPackage, pivot, rotations = Rotation.ALL):
        prevPosition = currPackage.position
        currPackage.position = pivot
        valid = False
        if (self.weightLeft() < currPackage.weight) : 
            return valid
        bestRotation = None 
        min_distance = float('inf')
        for rotation in rotations:
            currPackage.rotation = rotation
            dimensions = currPackage.getDimensions()
            if (
            self.length < pivot[0] + dimensions[0] or
            self.width < pivot[1] + dimensions[1] or
            self.height < pivot[2] + dimensions[2] or
            pivot[0] < 0 or pivot[1] < 0 or pivot[2] < 0
            ): continue
            valid = True 
            for package in self.packages:
                if package.isIntersecting(currPackage):
                    valid = False
                    break
            if valid == False:
                continue
            distance = (pivot[0] + dimensions[0])**2 + (pivot[1] + dimensions[1])**2 + (pivot[2] + dimensions[2])**2
            if distance < min_distance:
                min_distance = distance
                bestRotation = rotation

        if bestRotation is not None:
            currPackage.rotation = bestRotation
        if bestRotation is not None:
                #check for stability?
                #update uld criteria if needed for solver
                currPackage.ULD = self.id
                #do we need to deepcopy this?
                self.packages.append(currPackage)
                if(currPackage.priority == "Priority"): self.isPriority = True
                return valid

        # for rotation in rotations:
        #     currPackage.rotation = rotation
        #     dimensions = currPackage.getDimensions()
        #     if (
        #         self.length < pivot[0] + dimensions[0] or
        #         self.width < pivot[1] + dimensions[1] or
        #         self.height < pivot[2] + dimensions[2] or
        #         pivot[0] < 0 or pivot[1] < 0 or pivot[2] < 0
        #     ): continue

        #     valid = True

        #     for package in self.packages:
        #         if package.isIntersecting(currPackage):
        #             valid = False
        #             break

        #     if valid:
        #         #check for stability?
        #         #update uld criteria if needed for solver
        #         currPackage.ULD = self.id
        #         #do we need to deepcopy this?
        #         self.packages.append(currPackage)
        #         if(currPackage.priority == "Priority"): self.isPriority = True
        #         return valid
            
        currPackage.position = prevPosition
        return valid
    def addBox(self, currPackage, pivot, rotations = Rotation.ALL):
        prevPosition = currPackage.position
        currPackage.position = pivot
        valid = False
        if (self.weightLeft() < currPackage.weight) : 
            return valid
        for rotation in rotations:
            currPackage.rotation = rotation
            dimensions = currPackage.getDimensions()
            if (
                self.length < pivot[0] + dimensions[0] or
                self.width < pivot[1] + dimensions[1] or
                self.height < pivot[2] + dimensions[2] or
                pivot[0] < 0 or pivot[1] < 0 or pivot[2] < 0
            ): continue

            valid = True

            for package in self.packages:
                if package.isIntersecting(currPackage):
                    valid = False
                    break

            if valid:
                #check for stability?
                #update uld criteria if needed for solver
                currPackage.ULD = self.id
                #do we need to deepcopy this?
                self.packages.append(currPackage)
                if(currPackage.priority == "Priority"): self.isPriority = True
                return valid
            
        currPackage.position = prevPosition
        return valid
    
    def getNewCorners(self,package,corner):
        # print(corner, package.getDimensions())
    
        extreme_points = set()
        # print(corner)
        [x, y, z] = corner
        [dx, dy, dz] = package.getDimensions()
        L = self.length
        W = self.width
        H = self.height

        def project_along_axis(fixed_axis, variable_axis1, variable_axis2,x1,y1,z1):
            
            if fixed_axis == "x":
                fixed, dim, limit = x1, dx, L
                var1, var2 = y1, z1
            elif fixed_axis == "y":
                fixed, dim, limit = y1, dy, W
                var1, var2 = x1, z1
            elif fixed_axis == "z":
                fixed, dim, limit = z1, dz, H
                var1, var2 = x1, y1
            else:
                raise ValueError("Invalid axis!")

            # Initialize projection limit (container boundary)
            max_extent =  0

            # Check intersection with all packages
            for pkg in self.packages:
                
                px, py, pz = pkg.position
                pdx,pdy,pdz = pkg.getDimensions()

                # Get the package boundaries
                pkg_min = {"x": px, "y": py, "z": pz}
                pkg_max = {"x": px + pdx, "y": py + pdy, "z": pz + pdz}

                # Check if the package intersects the projection plane
                if pkg_min[variable_axis1] <= var1 < pkg_max[variable_axis1] and \
                pkg_min[variable_axis2] <= var2 < pkg_max[variable_axis2]:
                    if pkg_max[fixed_axis] <= fixed:
                        max_extent = max(max_extent, pkg_max[fixed_axis])  # Blocked by package

            # Return the maximum valid extent
            return max_extent

        
        ex1 = project_along_axis("x", "y", "z", x,y+dy,z)  
        extreme_points.add((ex1, y+dy, z))

        ez1 = project_along_axis("z", "x", "y", x,y+dy,z)  
        extreme_points.add((x, y+dy, ez1))          

        ex2 = project_along_axis("x", "y", "z", x,y,z+dz)  
        extreme_points.add((ex2, y,z+dz))

        ey1 = project_along_axis("y", "z", "x", x,y,z+dz)  
        extreme_points.add((x,ey1,z+dz))     

        ey2 = project_along_axis("y", "z", "x", x+dx,y,z)  
        extreme_points.add((x+dx,ey2,z))

        ez2 = project_along_axis("z", "x", "y", x+dx,y,z)  
        extreme_points.add((x+dx, y, ez2))     

        extreme_points.add((x+dx,y,z))
        extreme_points.add((x,y+dy,z))
        extreme_points.add((x,y,z+dz))
        
        return extreme_points

    def clearBin(self):
        for package in self.packages:
            package.ULD = -1
            package.position = [-1,-1,-1]
        self.packages = []
        self.isPriority = False
    


    def getLoadCenterOfMass(self):
        x = 0
        y = 0
        z = 0
        for package in self.packages:
            com = package.getCenterOfMass()
            weight = package.weight
            x+=com[0]*weight
            y+=com[1]*weight
            z+=com[2]*weight
        totalWeight = sum([package.weight for package in self.packages])
        return [x/totalWeight,y/totalWeight,z/totalWeight]
    

class CartonPackage:
    
    def __init__(self, id, uldid, position, dimensions, weight, cost, rotation):
        self.id = id
        self.uld = uldid
        self.position = position
        self.dimensions = dimensions
        self.weight = weight
        self.cost = cost
        self.rotation = rotation
        self.priority = 1 if uldid == "Priority" else 0