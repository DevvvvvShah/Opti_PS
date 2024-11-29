def get_from_greedy():
    import csv
    from structs import CartonPackage as Package
    import ast
    packages = []
    ULDS = ["U1", "U2", "U3", "U4", "U5", "U6"]
    with open('greedyOutput.csv', mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            package = Package(row[0], row[1], ast.literal_eval(row[2]), ast.literal_eval(row[3]), row[4], row[5],
                              row[6])
            packages.append(package)

    initialsij = {}
    for package in packages:
        for uld in ULDS:
            initialsij[(package.id, uld)] = 0
            if package.uld == uld:
                initialsij[(package.id, uld)] = 1
    initialxi = {}
    initialyi = {}
    initialzi = {}
    for package in packages:
        # print(package.id, package.position[0])
        initialxi[package.id] = package.position[0]
        initialyi[package.id] = package.position[1]
        initialzi[package.id] = package.position[2]
        if package.position[0] == -1:
            initialxi[package.id] = 0
            initialyi[package.id] = 0
            initialzi[package.id] = 0
    initialrelative_position = {}
    for package in packages:
        for other_package in packages:
            if package.id >= other_package.id:
                continue
            dict = {}
            if (package.uld != other_package.uld):
                dict["aik"] = 0
                dict["bik"] = 0
                dict["cik"] = 0
                dict["dik"] = 0
                dict["eik"] = 0
                dict["fik"] = 0
                initialrelative_position[(package.id, other_package.id)] = dict
                continue

            if (package.position[0] + package.dimensions[0] <= other_package.position[0]):
                dict["aik"] = 1
                dict["bik"] = 0
            elif (package.position[0] >= other_package.position[0] + other_package.dimensions[0]):
                dict["aik"] = 0
                dict["bik"] = 1
            else:
                dict["aik"] = 0
                dict["bik"] = 0
            if (package.position[1] + package.dimensions[1] <= other_package.position[1]):
                dict["cik"] = 1
                dict["dik"] = 0
            elif (package.position[1] >= other_package.position[1] + other_package.dimensions[1]):
                dict["cik"] = 0
                dict["dik"] = 1
            else:
                dict["cik"] = 0
                dict["dik"] = 0
            if (package.position[2] + package.dimensions[2] <= other_package.position[2]):
                dict["eik"] = 1
                dict["fik"] = 0
            elif (package.position[2] >= other_package.position[2] + other_package.dimensions[2]):
                dict["eik"] = 0
                dict["fik"] = 1
            else:
                dict["eik"] = 0
                dict["fik"] = 0
            initialrelative_position[(package.id, other_package.id)] = dict

    initialorientation = {}
    for package in packages:
        [len, wid, hei] = sorted([package.dimensions[0], package.dimensions[1], package.dimensions[2]])
        dict = {}

        if len == package.dimensions[0] and wid == package.dimensions[1] and hei == package.dimensions[2]:
            dict["lx"] = 1
            dict["ly"] = 0
            dict["lz"] = 0
            dict["wx"] = 0
            dict["wy"] = 1
            dict["wz"] = 0
            dict["hx"] = 0
            dict["hy"] = 0
            dict["hz"] = 1
        elif len == package.dimensions[0] and wid == package.dimensions[2] and hei == package.dimensions[1]:
            dict["lx"] = 1
            dict["ly"] = 0
            dict["lz"] = 0
            dict["wx"] = 0
            dict["wy"] = 0
            dict["wz"] = 1
            dict["hx"] = 0
            dict["hy"] = 1
            dict["hz"] = 0
        elif len == package.dimensions[1] and wid == package.dimensions[0] and hei == package.dimensions[2]:
            dict["lx"] = 0
            dict["ly"] = 1
            dict["lz"] = 0
            dict["wx"] = 1
            dict["wy"] = 0
            dict["wz"] = 0
            dict["hx"] = 0
            dict["hy"] = 0
            dict["hz"] = 1
        elif len == package.dimensions[1] and wid == package.dimensions[2] and hei == package.dimensions[0]:
            dict["lx"] = 0
            dict["ly"] = 1
            dict["lz"] = 0
            dict["wx"] = 0
            dict["wy"] = 0
            dict["wz"] = 1
            dict["hx"] = 1
            dict["hy"] = 0
            dict["hz"] = 0
        elif len == package.dimensions[2] and wid == package.dimensions[0] and hei == package.dimensions[1]:
            dict["lx"] = 0
            dict["ly"] = 0
            dict["lz"] = 1
            dict["wx"] = 1
            dict["wy"] = 0
            dict["wz"] = 0
            dict["hx"] = 0
            dict["hy"] = 1
            dict["hz"] = 0
        else:
            dict["lx"] = 0
            dict["ly"] = 0
            dict["lz"] = 1
            dict["wx"] = 0
            dict["wy"] = 1
            dict["wz"] = 0
            dict["hx"] = 1
            dict["hy"] = 0
            dict["hz"] = 0
        initialorientation[package.id] = dict
    # print sij,xi,yi,zi,relative_position,orientation for 2 packages
    package1 = packages[-1]
    package2 = packages[-2]
    initial_solution = {'sij': initialsij, 'xi': initialxi, 'yi': initialyi, 'zi': initialzi,
                        'relative_position': initialrelative_position, 'orientation': initialorientation}
    return initial_solution
