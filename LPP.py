import gurobipy as gp
from gurobipy import GRB


def are_cubes_intersecting(obj1, obj2):
    """
    Check if two cubes intersect.

    Each cube is defined by its base point (x, y, z) and dimensions (dimX, dimY, dimZ).

    Parameters:
        cube1: tuple (x1, y1, z1, dimX1, dimY1, dimZ1) for cube 1
        cube2: tuple (x2, y2, z2, dimX2, dimY2, dimZ2) for cube 2

    Returns:
        bool: True if the cubes intersect, False otherwise.
    """
    if obj1['container_id'] != obj2['container_id']:
        return False
    x1 = obj1['x']
    y1 = obj1['y']
    z1 = obj1['z']
    dimX1 = obj1['DimX']
    dimY1 = obj1['DimY']
    dimZ1 = obj1['DimZ']
    x2 = obj2['x']
    y2 = obj2['y']
    z2 = obj2['z']
    dimX2 = obj2['DimX']
    dimY2 = obj2['DimY']
    dimZ2 = obj2['DimZ']
    # Calculate the max and min coordinates for both cubes
    x1_min, x1_max = x1, x1 + dimX1
    y1_min, y1_max = y1, y1 + dimY1
    z1_min, z1_max = z1, z1 + dimZ1

    x2_min, x2_max = x2, x2 + dimX2
    y2_min, y2_max = y2, y2 + dimY2
    z2_min, z2_max = z2, z2 + dimZ2

    # Check for overlap on all three axes
    intersects = (
            x1_min < x2_max and x1_max > x2_min and  # X-axis overlap
            y1_min < y2_max and y1_max > y2_min and  # Y-axis overlap
            z1_min < z2_max and z1_max > z2_min  # Z-axis overlap
    )

    return intersects

def container_loading_with_relative_constraints(cartons, containers):
    """
    Solve the 3D container loading problem using mixed integer programming,
    incorporating relative positioning constraints (aik, bik, cik, dik, eik, fik).

    Parameters:
    cartons: list of dictionaries with carton details (dimensions and weight).
             Each carton is represented as {'id': int, 'length': float, 'width': float, 'height': float, 'weight': float}.
    containers: list of dictionaries with container dimensions.
             Each container is represented as {'id': int, 'length': float, 'width': float, 'height': float}.

    Returns:
    Optimal packing solution with carton placements, orientations, and container usage.
    """

    # Create a model
    model = gp.Model("3D_Container_Loading_with_Relative_Positioning")
    # model.Params.LogToConsole = 1  # Show optimization logs

    # Define constants
    M = 100000  # Large constant for "big-M" constraints

    # Decision variables
    sij = {}  # Binary: carton i assigned to container j
    xi, yi, zi = {}, {}, {}  # Continuous: coordinates of FLB corner of carton i
    nj = {}
    orientation = {}  # Binary variables for carton orientation (rotation matrix)
    relative_position = {}  # Binary variables for relative positions (aik, bik, cik, dik, eik, fik)
    # Add variables
    x = model.addVar(vtype=GRB.BINARY, name="1")
    model.addConstr(x == 1)
    # for container in containers:
    #     nj[container['id']] = model.addVar(vtype=GRB.INTEGER, name=f"n_{container['id']}")
    for carton in cartons:
        for container in containers:
            sij[(carton['id'], container['id'])] = model.addVar(vtype=GRB.BINARY,
                                                                name=f"s_{carton['id']}_{container['id']}")
        xi[carton['id']] = model.addVar(vtype=GRB.INTEGER, name=f"x_{carton['id']}")
        yi[carton['id']] = model.addVar(vtype=GRB.INTEGER, name=f"y_{carton['id']}")
        zi[carton['id']] = model.addVar(vtype=GRB.INTEGER, name=f"z_{carton['id']}")
        model.addConstr(xi[carton['id']] >= 0)
        model.addConstr(yi[carton['id']] >= 0)
        model.addConstr(zi[carton['id']] >= 0)
        # Add 9 binary orientation variables for each carton
        orientation[carton['id']] = {
            "lx": model.addVar(vtype=GRB.BINARY, name=f"lx_{carton['id']}"),
            "ly": model.addVar(vtype=GRB.BINARY, name=f"ly_{carton['id']}"),
            "lz": model.addVar(vtype=GRB.BINARY, name=f"lz_{carton['id']}"),
            "wx": model.addVar(vtype=GRB.BINARY, name=f"wx_{carton['id']}"),
            "wy": model.addVar(vtype=GRB.BINARY, name=f"wy_{carton['id']}"),
            "wz": model.addVar(vtype=GRB.BINARY, name=f"wz_{carton['id']}"),
            "hx": model.addVar(vtype=GRB.BINARY, name=f"hx_{carton['id']}"),
            "hy": model.addVar(vtype=GRB.BINARY, name=f"hy_{carton['id']}"),
            "hz": model.addVar(vtype=GRB.BINARY, name=f"hz_{carton['id']}"),
        }

    # Relative positioning variables: aik, bik, cik, dik, eik, fik
    for i in range(len(cartons)):
        for k in range(i + 1, len(cartons)):
            carton_i = cartons[i]
            carton_k = cartons[k]
            relative_position[(carton_i['id'], carton_k['id'])] = {
                "aik": model.addVar(vtype=GRB.BINARY, name=f"aik_{carton_i['id']}_{carton_k['id']}"),
                "bik": model.addVar(vtype=GRB.BINARY, name=f"bik_{carton_i['id']}_{carton_k['id']}"),
                "cik": model.addVar(vtype=GRB.BINARY, name=f"cik_{carton_i['id']}_{carton_k['id']}"),
                "dik": model.addVar(vtype=GRB.BINARY, name=f"dik_{carton_i['id']}_{carton_k['id']}"),
                "eik": model.addVar(vtype=GRB.BINARY, name=f"eik_{carton_i['id']}_{carton_k['id']}"),
                "fik": model.addVar(vtype=GRB.BINARY, name=f"fik_{carton_i['id']}_{carton_k['id']}"),
            }

    # Constraints
    # 1. Assign each carton to exactly one container
    for carton in cartons:
        model.addConstr(sum(sij[(carton['id'], container['id'])] for container in containers) <= 1,
                        name=f"assign_{carton['id']}")
    # for container in containers:
    #     model.addConstr(sum(sij[(carton['id'], container['id'])] for carton in cartons) <= M*nj[container['id']],
    #                     name=f"assign_{container['id']}")
    # 2. Orientation consistency: Each dimension aligns with exactly one axis
    for carton in cartons:
        orients = orientation[carton['id']]
        model.addConstr(orients["lx"] + orients["ly"] + orients["lz"] == 1, name=f"orient_length_{carton['id']}")
        model.addConstr(orients["wx"] + orients["wy"] + orients["wz"] == 1, name=f"orient_width_{carton['id']}")
        model.addConstr(orients["hx"] + orients["hy"] + orients["hz"] == 1, name=f"orient_height_{carton['id']}")

        # Each axis has one dimension
        model.addConstr(orients["lx"] + orients["wx"] + orients["hx"] == 1, name=f"axis_x_{carton['id']}")
        model.addConstr(orients["ly"] + orients["wy"] + orients["hy"] == 1, name=f"axis_y_{carton['id']}")
        model.addConstr(orients["lz"] + orients["wz"] + orients["hz"] == 1, name=f"axis_z_{carton['id']}")

    # 3. Fit cartons within container dimensions
    for carton in cartons:
        for container in containers:
            orients = orientation[carton['id']]
            model.addConstr(xi[carton['id']] + carton['length'] * orients["lx"] +
                            carton['width'] * orients["wx"] +
                            carton['height'] * orients["hx"] <= container['length'] + (
                                        1 - sij[(carton['id'], container['id'])]) * M,
                            name=f"fit_x_{carton['id']}_{container['id']}")

            model.addConstr(yi[carton['id']] + carton['length'] * orients["ly"] +
                            carton['width'] * orients["wy"] +
                            carton['height'] * orients["hy"] <= container['width'] + (
                                        1 - sij[(carton['id'], container['id'])]) * M,
                            name=f"fit_y_{carton['id']}_{container['id']}")

            model.addConstr(zi[carton['id']] + carton['length'] * orients["lz"] +
                            carton['width'] * orients["wz"] +
                            carton['height'] * orients["hz"] <= container['height'] + (
                                        1 - sij[(carton['id'], container['id'])]) * M,
                            name=f"fit_z_{carton['id']}_{container['id']}")

    # 4. Prevent overlapping of cartons with aik, bik, cik, dik, eik, fik
    for container in containers:
        model.addConstr(sum((sij[(carton['id'], container['id'])] * carton['weight']) for carton in cartons) <= container['weight'],
                        name=f"weight_limit_constr{container['id']}")
        for i in range(len(cartons)):
            for k in range(i + 1, len(cartons)):
                carton_i = cartons[i]
                carton_k = cartons[k]
                rel = relative_position[(carton_i['id'], carton_k['id'])]
                model.addConstr((rel["aik"] + rel["bik"] + rel["cik"] + rel["dik"] + rel["eik"] + rel["fik"] >=
                                 sij[(carton_i['id'], container['id'])] + sij[(carton_k['id'], container['id'])] - x),
                                name=f"relative_sum_{carton_i['id']}_{carton_k['id']}_{container['id']}")
    for i in range(len(cartons)):
        for k in range(i+1, len(cartons)):
            carton_i = cartons[i]
            carton_k = cartons[k]
            rel = relative_position[(carton_i['id'], carton_k['id'])]
            model.addConstr(
                xi[carton_i['id']] + carton_i['length'] * orientation[carton_i['id']]["lx"] + carton_i['width'] *
                orientation[carton_i['id']]["wx"] + carton_i['height'] * orientation[carton_i['id']]["hx"] <= xi[
                    carton_k['id']] + (1 - rel["aik"]) * M, name=f"no_overlap_x_a_{carton_i['id']}_{carton_k['id']}")
            model.addConstr(
                xi[carton_k['id']] + carton_k['length'] * orientation[carton_k['id']]["lx"] + carton_k['width'] *
                orientation[carton_k['id']]["wx"] + carton_k['height'] * orientation[carton_k['id']]["hx"] <= xi[
                    carton_i['id']] + (1 - rel["bik"]) * M, name=f"no_overlap_x_b_{carton_i['id']}_{carton_k['id']}")
            model.addConstr(
                yi[carton_i['id']] + carton_i['length'] * orientation[carton_i['id']]["ly"] + carton_i['width'] *
                orientation[carton_i['id']]["wy"] + carton_i['height'] * orientation[carton_i['id']]["hy"] <= yi[
                    carton_k['id']] + (1 - rel["cik"]) * M, name=f"no_overlap_y_c_{carton_i['id']}_{carton_k['id']}")
            model.addConstr(
                yi[carton_k['id']] + carton_k['length'] * orientation[carton_k['id']]["ly"] + carton_k['width'] *
                orientation[carton_k['id']]["wy"] + carton_k['height'] * orientation[carton_k['id']]["hy"] <= yi[
                    carton_i['id']] + (1 - rel["dik"]) * M, name=f"no_overlap_y_d_{carton_i['id']}_{carton_k['id']}")
            model.addConstr(
                zi[carton_i['id']] + carton_i['length'] * orientation[carton_i['id']]["lz"] + carton_i['width'] *
                orientation[carton_i['id']]["wz"] + carton_i['height'] * orientation[carton_i['id']]["hz"] <= zi[
                    carton_k['id']] + (1 - rel["eik"]) * M, name=f"no_overlap_z_e_{carton_i['id']}_{carton_k['id']}")
            model.addConstr(
                zi[carton_k['id']] + carton_k['length'] * orientation[carton_k['id']]["lz"] + carton_k['width'] *
                orientation[carton_k['id']]["wz"] + carton_k['height'] * orientation[carton_k['id']]["hz"] <= zi[
                    carton_i['id']] + (1 - rel["fik"]) * M, name=f"no_overlap_z_f_{carton_i['id']}_{carton_k['id']}")
    print(cartons)

   # Objective: Minimize unused space
    priority_penalty = 0
    for container in containers:
       prod = 0
       for carton in cartons:
           prod = prod or ((sij[(carton['id'], container['id'])] * carton['priority']))
       priority_penalty += prod
    priority_penalty *= 5000
    economy_penalty = 0
    for carton in cartons:
        s = 1
        for container in containers:
            s -= sij[(carton['id'], container['id'])]
        economy_penalty += s * carton['cost']
    penalty = priority_penalty + economy_penalty
    model.setObjective(penalty, GRB.MINIMIZE)
    model.optimize()
    # Extract the solution
    if model.status == GRB.OPTIMAL:
        print("Optimal solution found. Checking constraints:")
        # for c in model.getConstrs():
        #     lhs = model.getRow(c).getValue()
        #     rhs = c.RHS
            # print(f"{c.ConstrName}: LHS = {lhs}, RHS = {rhs}, Sense = {c.Sense}")
        # print(sij["P-365", "U6"].X)
        # print(sij["P-165", "U6"].X)
        model.printQuality()
        solution = []
        # for container in containers:
        # for i in range(len(cartons)):
        #     for j in range(i + 1, len(cartons)):
        #         rel = relative_position[(cartons[i]['id'], cartons[j]['id'])]
        #         print(cartons[i]['id'], cartons[j]['id'], container['id'])
        #         print(rel["aik"].X, rel["bik"].X, rel["cik"].X, rel["dik"].X, rel["eik"].X, rel["fik"].X)
        for container in containers:
            for carton in cartons:
                if sij[(carton['id'], container['id'])].X > 0.5:
                    solution.append({
                            "carton_id": carton['id'],
                            "container_id": container['id'],
                            "x": xi[carton['id']].X,
                            "y": yi[carton['id']].X,
                            "z": zi[carton['id']].X,
                            "DimX": carton['length'] * orientation[carton['id']]["lx"].X + carton['width'] * orientation[carton['id']]["wx"].X + carton['height'] * orientation[carton['id']]["hx"].X,
                            "DimY": carton['length'] * orientation[carton['id']]["ly"].X + carton['width'] * orientation[carton['id']]["wy"].X + carton['height'] * orientation[carton['id']]["hy"].X,
                            "DimZ": carton['length'] * orientation[carton['id']]["lz"].X + carton['width'] * orientation[carton['id']]["wz"].X + carton['height'] * orientation[carton['id']]["hz"].X
                        })
                    # Print aik and bik variables
        return solution
    else:
        print("No feasible solution found.")


cartons = [{'id': 'P-1', 'length': 99.0, 'width': 53.0, 'height': 55.0, 'weight': 61.0, 'priority': 0, 'cost': 176.0}, {'id': 'P-2', 'length': 56.0, 'width': 99.0, 'height': 81.0, 'weight': 53.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-3', 'length': 42.0, 'width': 101.0, 'height': 51.0, 'weight': 17.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-4', 'length': 108.0, 'width': 75.0, 'height': 56.0, 'weight': 73.0, 'priority': 0, 'cost': 138.0}, {'id': 'P-5', 'length': 88.0, 'width': 58.0, 'height': 64.0, 'weight': 93.0, 'priority': 0, 'cost': 139.0}, {'id': 'P-6', 'length': 91.0, 'width': 56.0, 'height': 84.0, 'weight': 47.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-7', 'length': 88.0, 'width': 78.0, 'height': 93.0, 'weight': 117.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-8', 'length': 108.0, 'width': 105.0, 'height': 76.0, 'weight': 142.0, 'priority': 0, 'cost': 108.0}, {'id': 'P-9', 'length': 73.0, 'width': 71.0, 'height': 88.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-10', 'length': 88.0, 'width': 70.0, 'height': 85.0, 'weight': 81.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-11', 'length': 55.0, 'width': 80.0, 'height': 81.0, 'weight': 23.0, 'priority': 0, 'cost': 96.0}, {'id': 'P-12', 'length': 48.0, 'width': 80.0, 'height': 88.0, 'weight': 27.0, 'priority': 0, 'cost': 117.0}, {'id': 'P-13', 'length': 55.0, 'width': 94.0, 'height': 87.0, 'weight': 41.0, 'priority': 0, 'cost': 73.0}, {'id': 'P-14', 'length': 45.0, 'width': 46.0, 'height': 81.0, 'weight': 27.0, 'priority': 0, 'cost': 68.0}, {'id': 'P-15', 'length': 84.0, 'width': 49.0, 'height': 60.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-16', 'length': 48.0, 'width': 93.0, 'height': 63.0, 'weight': 82.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-17', 'length': 83.0, 'width': 63.0, 'height': 57.0, 'weight': 29.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-18', 'length': 68.0, 'width': 101.0, 'height': 95.0, 'weight': 96.0, 'priority': 0, 'cost': 65.0}, {'id': 'P-19', 'length': 51.0, 'width': 87.0, 'height': 69.0, 'weight': 73.0, 'priority': 0, 'cost': 107.0}, {'id': 'P-20', 'length': 88.0, 'width': 106.0, 'height': 56.0, 'weight': 71.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-21', 'length': 105.0, 'width': 71.0, 'height': 105.0, 'weight': 223.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-22', 'length': 100.0, 'width': 92.0, 'height': 99.0, 'weight': 191.0, 'priority': 0, 'cost': 86.0}, {'id': 'P-23', 'length': 51.0, 'width': 50.0, 'height': 110.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-24', 'length': 81.0, 'width': 109.0, 'height': 55.0, 'weight': 123.0, 'priority': 0, 'cost': 69.0}, {'id': 'P-25', 'length': 44.0, 'width': 77.0, 'height': 53.0, 'weight': 37.0, 'priority': 0, 'cost': 108.0}, {'id': 'P-26', 'length': 69.0, 'width': 56.0, 'height': 73.0, 'weight': 56.0, 'priority': 0, 'cost': 130.0}, {'id': 'P-27', 'length': 93.0, 'width': 62.0, 'height': 49.0, 'weight': 18.0, 'priority': 0, 'cost': 122.0}, {'id': 'P-28', 'length': 81.0, 'width': 64.0, 'height': 95.0, 'weight': 70.0, 'priority': 0, 'cost': 139.0}, {'id': 'P-29', 'length': 62.0, 'width': 86.0, 'height': 53.0, 'weight': 23.0, 'priority': 0, 'cost': 122.0}, {'id': 'P-30', 'length': 88.0, 'width': 85.0, 'height': 102.0, 'weight': 164.0, 'priority': 0, 'cost': 70.0}, {'id': 'P-31', 'length': 71.0, 'width': 49.0, 'height': 76.0, 'weight': 67.0, 'priority': 0, 'cost': 76.0}, {'id': 'P-32', 'length': 70.0, 'width': 44.0, 'height': 98.0, 'weight': 53.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-33', 'length': 90.0, 'width': 89.0, 'height': 73.0, 'weight': 132.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-34', 'length': 87.0, 'width': 45.0, 'height': 81.0, 'weight': 45.0, 'priority': 0, 'cost': 77.0}, {'id': 'P-35', 'length': 83.0, 'width': 72.0, 'height': 63.0, 'weight': 96.0, 'priority': 0, 'cost': 103.0}, {'id': 'P-36', 'length': 86.0, 'width': 80.0, 'height': 78.0, 'weight': 146.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-37', 'length': 59.0, 'width': 76.0, 'height': 51.0, 'weight': 33.0, 'priority': 0, 'cost': 131.0}, {'id': 'P-38', 'length': 84.0, 'width': 96.0, 'height': 48.0, 'weight': 21.0, 'priority': 0, 'cost': 60.0}, {'id': 'P-39', 'length': 96.0, 'width': 64.0, 'height': 61.0, 'weight': 61.0, 'priority': 0, 'cost': 111.0}, {'id': 'P-40', 'length': 70.0, 'width': 45.0, 'height': 90.0, 'weight': 78.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-41', 'length': 104.0, 'width': 90.0, 'height': 68.0, 'weight': 72.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-42', 'length': 62.0, 'width': 109.0, 'height': 41.0, 'weight': 46.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-43', 'length': 51.0, 'width': 86.0, 'height': 108.0, 'weight': 87.0, 'priority': 0, 'cost': 109.0}, {'id': 'P-44', 'length': 84.0, 'width': 40.0, 'height': 49.0, 'weight': 28.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-45', 'length': 91.0, 'width': 72.0, 'height': 81.0, 'weight': 92.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-46', 'length': 71.0, 'width': 62.0, 'height': 94.0, 'weight': 39.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-47', 'length': 86.0, 'width': 58.0, 'height': 104.0, 'weight': 149.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-48', 'length': 53.0, 'width': 65.0, 'height': 48.0, 'weight': 33.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-49', 'length': 69.0, 'width': 40.0, 'height': 100.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-50', 'length': 73.0, 'width': 104.0, 'height': 64.0, 'weight': 75.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-51', 'length': 57.0, 'width': 86.0, 'height': 97.0, 'weight': 65.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-52', 'length': 104.0, 'width': 88.0, 'height': 102.0, 'weight': 96.0, 'priority': 0, 'cost': 121.0}, {'id': 'P-53', 'length': 44.0, 'width': 53.0, 'height': 106.0, 'weight': 14.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-54', 'length': 106.0, 'width': 51.0, 'height': 59.0, 'weight': 20.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-55', 'length': 95.0, 'width': 93.0, 'height': 77.0, 'weight': 71.0, 'priority': 0, 'cost': 78.0}, {'id': 'P-56', 'length': 65.0, 'width': 68.0, 'height': 109.0, 'weight': 77.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-57', 'length': 83.0, 'width': 64.0, 'height': 59.0, 'weight': 32.0, 'priority': 0, 'cost': 137.0}, {'id': 'P-58', 'length': 95.0, 'width': 102.0, 'height': 55.0, 'weight': 126.0, 'priority': 0, 'cost': 134.0}, {'id': 'P-59', 'length': 85.0, 'width': 79.0, 'height': 49.0, 'weight': 26.0, 'priority': 0, 'cost': 111.0}, {'id': 'P-60', 'length': 60.0, 'width': 85.0, 'height': 87.0, 'weight': 23.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-61', 'length': 57.0, 'width': 109.0, 'height': 95.0, 'weight': 130.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-62', 'length': 43.0, 'width': 92.0, 'height': 88.0, 'weight': 25.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-63', 'length': 75.0, 'width': 69.0, 'height': 85.0, 'weight': 111.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-64', 'length': 100.0, 'width': 56.0, 'height': 104.0, 'weight': 123.0, 'priority': 0, 'cost': 62.0}, {'id': 'P-65', 'length': 50.0, 'width': 78.0, 'height': 110.0, 'weight': 56.0, 'priority': 0, 'cost': 121.0}, {'id': 'P-66', 'length': 50.0, 'width': 47.0, 'height': 86.0, 'weight': 53.0, 'priority': 0, 'cost': 72.0}, {'id': 'P-67', 'length': 76.0, 'width': 57.0, 'height': 101.0, 'weight': 34.0, 'priority': 0, 'cost': 65.0}, {'id': 'P-68', 'length': 92.0, 'width': 46.0, 'height': 81.0, 'weight': 62.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-69', 'length': 84.0, 'width': 47.0, 'height': 54.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-70', 'length': 108.0, 'width': 101.0, 'height': 77.0, 'weight': 158.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-71', 'length': 99.0, 'width': 43.0, 'height': 60.0, 'weight': 41.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-72', 'length': 89.0, 'width': 83.0, 'height': 44.0, 'weight': 79.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-73', 'length': 104.0, 'width': 86.0, 'height': 63.0, 'weight': 79.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-74', 'length': 73.0, 'width': 87.0, 'height': 69.0, 'weight': 115.0, 'priority': 0, 'cost': 61.0}, {'id': 'P-75', 'length': 74.0, 'width': 43.0, 'height': 85.0, 'weight': 42.0, 'priority': 0, 'cost': 128.0}, {'id': 'P-76', 'length': 40.0, 'width': 92.0, 'height': 96.0, 'weight': 81.0, 'priority': 0, 'cost': 123.0}, {'id': 'P-77', 'length': 96.0, 'width': 50.0, 'height': 65.0, 'weight': 57.0, 'priority': 0, 'cost': 88.0}, {'id': 'P-78', 'length': 74.0, 'width': 104.0, 'height': 42.0, 'weight': 85.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-79', 'length': 86.0, 'width': 62.0, 'height': 75.0, 'weight': 61.0, 'priority': 0, 'cost': 91.0}, {'id': 'P-80', 'length': 43.0, 'width': 85.0, 'height': 44.0, 'weight': 20.0, 'priority': 0, 'cost': 127.0}, {'id': 'P-81', 'length': 110.0, 'width': 101.0, 'height': 93.0, 'weight': 94.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-82', 'length': 66.0, 'width': 71.0, 'height': 97.0, 'weight': 130.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-83', 'length': 106.0, 'width': 105.0, 'height': 99.0, 'weight': 168.0, 'priority': 0, 'cost': 97.0}, {'id': 'P-84', 'length': 94.0, 'width': 66.0, 'height': 78.0, 'weight': 41.0, 'priority': 0, 'cost': 82.0}, {'id': 'P-85', 'length': 47.0, 'width': 68.0, 'height': 44.0, 'weight': 42.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-86', 'length': 65.0, 'width': 63.0, 'height': 41.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-87', 'length': 54.0, 'width': 53.0, 'height': 107.0, 'weight': 84.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-88', 'length': 70.0, 'width': 106.0, 'height': 62.0, 'weight': 106.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-89', 'length': 68.0, 'width': 109.0, 'height': 108.0, 'weight': 60.0, 'priority': 0, 'cost': 117.0}, {'id': 'P-90', 'length': 44.0, 'width': 98.0, 'height': 102.0, 'weight': 119.0, 'priority': 0, 'cost': 60.0}, {'id': 'P-91', 'length': 91.0, 'width': 92.0, 'height': 50.0, 'weight': 89.0, 'priority': 0, 'cost': 76.0}, {'id': 'P-92', 'length': 58.0, 'width': 58.0, 'height': 65.0, 'weight': 59.0, 'priority': 0, 'cost': 138.0}, {'id': 'P-93', 'length': 88.0, 'width': 68.0, 'height': 92.0, 'weight': 100.0, 'priority': 0, 'cost': 133.0}, {'id': 'P-94', 'length': 67.0, 'width': 98.0, 'height': 66.0, 'weight': 95.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-95', 'length': 91.0, 'width': 69.0, 'height': 89.0, 'weight': 68.0, 'priority': 0, 'cost': 73.0}, {'id': 'P-96', 'length': 50.0, 'width': 65.0, 'height': 84.0, 'weight': 40.0, 'priority': 0, 'cost': 68.0}, {'id': 'P-97', 'length': 53.0, 'width': 53.0, 'height': 93.0, 'weight': 54.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-98', 'length': 108.0, 'width': 63.0, 'height': 94.0, 'weight': 139.0, 'priority': 0, 'cost': 76.0}, {'id': 'P-99', 'length': 71.0, 'width': 70.0, 'height': 68.0, 'weight': 28.0, 'priority': 0, 'cost': 108.0}, {'id': 'P-100', 'length': 100.0, 'width': 62.0, 'height': 87.0, 'weight': 104.0, 'priority': 0, 'cost': 79.0}, {'id': 'P-101', 'length': 102.0, 'width': 82.0, 'height': 76.0, 'weight': 154.0, 'priority': 0, 'cost': 109.0}, {'id': 'P-102', 'length': 70.0, 'width': 106.0, 'height': 64.0, 'weight': 70.0, 'priority': 0, 'cost': 135.0}, {'id': 'P-103', 'length': 44.0, 'width': 78.0, 'height': 102.0, 'weight': 84.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-104', 'length': 90.0, 'width': 95.0, 'height': 95.0, 'weight': 110.0, 'priority': 0, 'cost': 108.0}, {'id': 'P-105', 'length': 80.0, 'width': 95.0, 'height': 103.0, 'weight': 225.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-106', 'length': 90.0, 'width': 54.0, 'height': 92.0, 'weight': 100.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-107', 'length': 99.0, 'width': 100.0, 'height': 100.0, 'weight': 252.0, 'priority': 0, 'cost': 134.0}, {'id': 'P-108', 'length': 47.0, 'width': 109.0, 'height': 70.0, 'weight': 95.0, 'priority': 0, 'cost': 90.0}, {'id': 'P-109', 'length': 98.0, 'width': 79.0, 'height': 44.0, 'weight': 53.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-110', 'length': 86.0, 'width': 88.0, 'height': 100.0, 'weight': 158.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-111', 'length': 62.0, 'width': 103.0, 'height': 65.0, 'weight': 27.0, 'priority': 0, 'cost': 60.0}, {'id': 'P-112', 'length': 63.0, 'width': 79.0, 'height': 67.0, 'weight': 20.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-113', 'length': 55.0, 'width': 86.0, 'height': 75.0, 'weight': 88.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-114', 'length': 80.0, 'width': 93.0, 'height': 104.0, 'weight': 175.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-115', 'length': 46.0, 'width': 105.0, 'height': 102.0, 'weight': 112.0, 'priority': 0, 'cost': 105.0}, {'id': 'P-116', 'length': 106.0, 'width': 109.0, 'height': 83.0, 'weight': 132.0, 'priority': 0, 'cost': 128.0}, {'id': 'P-117', 'length': 52.0, 'width': 49.0, 'height': 65.0, 'weight': 33.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-118', 'length': 90.0, 'width': 82.0, 'height': 75.0, 'weight': 55.0, 'priority': 0, 'cost': 114.0}, {'id': 'P-119', 'length': 41.0, 'width': 79.0, 'height': 104.0, 'weight': 25.0, 'priority': 0, 'cost': 61.0}, {'id': 'P-120', 'length': 48.0, 'width': 91.0, 'height': 74.0, 'weight': 82.0, 'priority': 0, 'cost': 105.0}, {'id': 'P-121', 'length': 79.0, 'width': 108.0, 'height': 80.0, 'weight': 99.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-122', 'length': 77.0, 'width': 104.0, 'height': 46.0, 'weight': 67.0, 'priority': 0, 'cost': 105.0}, {'id': 'P-123', 'length': 43.0, 'width': 62.0, 'height': 40.0, 'weight': 7.0, 'priority': 0, 'cost': 75.0}, {'id': 'P-124', 'length': 54.0, 'width': 104.0, 'height': 72.0, 'weight': 96.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-125', 'length': 68.0, 'width': 85.0, 'height': 91.0, 'weight': 139.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-126', 'length': 85.0, 'width': 64.0, 'height': 60.0, 'weight': 94.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-127', 'length': 71.0, 'width': 78.0, 'height': 67.0, 'weight': 79.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-128', 'length': 79.0, 'width': 102.0, 'height': 66.0, 'weight': 44.0, 'priority': 0, 'cost': 92.0}, {'id': 'P-129', 'length': 110.0, 'width': 59.0, 'height': 85.0, 'weight': 64.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-130', 'length': 78.0, 'width': 45.0, 'height': 40.0, 'weight': 18.0, 'priority': 0, 'cost': 79.0}, {'id': 'P-131', 'length': 82.0, 'width': 80.0, 'height': 79.0, 'weight': 84.0, 'priority': 0, 'cost': 109.0}, {'id': 'P-132', 'length': 92.0, 'width': 102.0, 'height': 42.0, 'weight': 115.0, 'priority': 0, 'cost': 77.0}, {'id': 'P-133', 'length': 63.0, 'width': 109.0, 'height': 91.0, 'weight': 174.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-134', 'length': 80.0, 'width': 88.0, 'height': 97.0, 'weight': 150.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-135', 'length': 108.0, 'width': 66.0, 'height': 45.0, 'weight': 56.0, 'priority': 0, 'cost': 132.0}, {'id': 'P-136', 'length': 47.0, 'width': 66.0, 'height': 102.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-137', 'length': 59.0, 'width': 110.0, 'height': 96.0, 'weight': 108.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-138', 'length': 85.0, 'width': 80.0, 'height': 89.0, 'weight': 142.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-139', 'length': 96.0, 'width': 84.0, 'height': 75.0, 'weight': 123.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-140', 'length': 84.0, 'width': 106.0, 'height': 65.0, 'weight': 60.0, 'priority': 0, 'cost': 119.0}, {'id': 'P-141', 'length': 70.0, 'width': 43.0, 'height': 87.0, 'weight': 34.0, 'priority': 0, 'cost': 70.0}, {'id': 'P-142', 'length': 92.0, 'width': 74.0, 'height': 83.0, 'weight': 169.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-143', 'length': 82.0, 'width': 100.0, 'height': 106.0, 'weight': 206.0, 'priority': 0, 'cost': 76.0}, {'id': 'P-144', 'length': 59.0, 'width': 72.0, 'height': 106.0, 'weight': 120.0, 'priority': 0, 'cost': 111.0}, {'id': 'P-145', 'length': 75.0, 'width': 106.0, 'height': 79.0, 'weight': 66.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-146', 'length': 100.0, 'width': 45.0, 'height': 56.0, 'weight': 46.0, 'priority': 0, 'cost': 92.0}, {'id': 'P-147', 'length': 65.0, 'width': 46.0, 'height': 55.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-148', 'length': 67.0, 'width': 100.0, 'height': 49.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-149', 'length': 63.0, 'width': 45.0, 'height': 104.0, 'weight': 76.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-150', 'length': 54.0, 'width': 42.0, 'height': 58.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-151', 'length': 44.0, 'width': 106.0, 'height': 79.0, 'weight': 23.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-152', 'length': 67.0, 'width': 57.0, 'height': 49.0, 'weight': 39.0, 'priority': 0, 'cost': 73.0}, {'id': 'P-153', 'length': 62.0, 'width': 64.0, 'height': 51.0, 'weight': 59.0, 'priority': 0, 'cost': 62.0}, {'id': 'P-154', 'length': 64.0, 'width': 103.0, 'height': 91.0, 'weight': 47.0, 'priority': 0, 'cost': 118.0}, {'id': 'P-155', 'length': 95.0, 'width': 87.0, 'height': 47.0, 'weight': 95.0, 'priority': 0, 'cost': 99.0}, {'id': 'P-156', 'length': 47.0, 'width': 73.0, 'height': 110.0, 'weight': 57.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-157', 'length': 88.0, 'width': 88.0, 'height': 54.0, 'weight': 30.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-158', 'length': 72.0, 'width': 107.0, 'height': 95.0, 'weight': 135.0, 'priority': 0, 'cost': 61.0}, {'id': 'P-159', 'length': 50.0, 'width': 92.0, 'height': 52.0, 'weight': 15.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-160', 'length': 108.0, 'width': 82.0, 'height': 99.0, 'weight': 232.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-161', 'length': 78.0, 'width': 97.0, 'height': 62.0, 'weight': 127.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-162', 'length': 46.0, 'width': 104.0, 'height': 65.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-163', 'length': 49.0, 'width': 83.0, 'height': 83.0, 'weight': 45.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-164', 'length': 102.0, 'width': 40.0, 'height': 87.0, 'weight': 99.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-165', 'length': 103.0, 'width': 96.0, 'height': 93.0, 'weight': 267.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-166', 'length': 84.0, 'width': 62.0, 'height': 103.0, 'weight': 142.0, 'priority': 0, 'cost': 134.0}, {'id': 'P-167', 'length': 47.0, 'width': 50.0, 'height': 100.0, 'weight': 33.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-168', 'length': 68.0, 'width': 87.0, 'height': 88.0, 'weight': 109.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-169', 'length': 48.0, 'width': 87.0, 'height': 94.0, 'weight': 102.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-170', 'length': 100.0, 'width': 81.0, 'height': 44.0, 'weight': 39.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-171', 'length': 50.0, 'width': 55.0, 'height': 93.0, 'weight': 55.0, 'priority': 0, 'cost': 110.0}, {'id': 'P-172', 'length': 51.0, 'width': 71.0, 'height': 76.0, 'weight': 22.0, 'priority': 0, 'cost': 112.0}, {'id': 'P-173', 'length': 92.0, 'width': 81.0, 'height': 89.0, 'weight': 130.0, 'priority': 0, 'cost': 81.0}, {'id': 'P-174', 'length': 107.0, 'width': 101.0, 'height': 47.0, 'weight': 107.0, 'priority': 0, 'cost': 127.0}, {'id': 'P-175', 'length': 66.0, 'width': 88.0, 'height': 96.0, 'weight': 127.0, 'priority': 0, 'cost': 121.0}, {'id': 'P-176', 'length': 60.0, 'width': 62.0, 'height': 102.0, 'weight': 42.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-177', 'length': 44.0, 'width': 41.0, 'height': 99.0, 'weight': 17.0, 'priority': 0, 'cost': 77.0}, {'id': 'P-178', 'length': 78.0, 'width': 69.0, 'height': 96.0, 'weight': 97.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-179', 'length': 62.0, 'width': 73.0, 'height': 63.0, 'weight': 38.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-180', 'length': 80.0, 'width': 71.0, 'height': 59.0, 'weight': 43.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-181', 'length': 98.0, 'width': 58.0, 'height': 57.0, 'weight': 93.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-182', 'length': 45.0, 'width': 70.0, 'height': 78.0, 'weight': 42.0, 'priority': 0, 'cost': 65.0}, {'id': 'P-183', 'length': 105.0, 'width': 72.0, 'height': 57.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-184', 'length': 88.0, 'width': 96.0, 'height': 74.0, 'weight': 129.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-185', 'length': 42.0, 'width': 67.0, 'height': 100.0, 'weight': 52.0, 'priority': 0, 'cost': 133.0}, {'id': 'P-186', 'length': 47.0, 'width': 84.0, 'height': 93.0, 'weight': 60.0, 'priority': 0, 'cost': 118.0}, {'id': 'P-187', 'length': 54.0, 'width': 84.0, 'height': 78.0, 'weight': 97.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-188', 'length': 86.0, 'width': 51.0, 'height': 51.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-189', 'length': 56.0, 'width': 63.0, 'height': 87.0, 'weight': 66.0, 'priority': 0, 'cost': 121.0}, {'id': 'P-190', 'length': 108.0, 'width': 101.0, 'height': 52.0, 'weight': 143.0, 'priority': 0, 'cost': 128.0}, {'id': 'P-191', 'length': 100.0, 'width': 71.0, 'height': 94.0, 'weight': 123.0, 'priority': 0, 'cost': 64.0}, {'id': 'P-192', 'length': 54.0, 'width': 76.0, 'height': 74.0, 'weight': 33.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-193', 'length': 72.0, 'width': 87.0, 'height': 67.0, 'weight': 113.0, 'priority': 0, 'cost': 75.0}, {'id': 'P-194', 'length': 71.0, 'width': 48.0, 'height': 109.0, 'weight': 97.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-195', 'length': 102.0, 'width': 57.0, 'height': 72.0, 'weight': 62.0, 'priority': 0, 'cost': 90.0}, {'id': 'P-196', 'length': 64.0, 'width': 107.0, 'height': 66.0, 'weight': 85.0, 'priority': 0, 'cost': 60.0}, {'id': 'P-197', 'length': 109.0, 'width': 82.0, 'height': 99.0, 'weight': 68.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-198', 'length': 74.0, 'width': 59.0, 'height': 84.0, 'weight': 68.0, 'priority': 0, 'cost': 113.0}, {'id': 'P-199', 'length': 58.0, 'width': 67.0, 'height': 73.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-200', 'length': 74.0, 'width': 74.0, 'height': 83.0, 'weight': 81.0, 'priority': 0, 'cost': 95.0}, {'id': 'P-201', 'length': 80.0, 'width': 106.0, 'height': 76.0, 'weight': 159.0, 'priority': 0, 'cost': 139.0}, {'id': 'P-202', 'length': 52.0, 'width': 94.0, 'height': 40.0, 'weight': 57.0, 'priority': 0, 'cost': 105.0}, {'id': 'P-203', 'length': 68.0, 'width': 106.0, 'height': 93.0, 'weight': 52.0, 'priority': 0, 'cost': 63.0}, {'id': 'P-204', 'length': 55.0, 'width': 88.0, 'height': 103.0, 'weight': 150.0, 'priority': 0, 'cost': 101.0}, {'id': 'P-205', 'length': 47.0, 'width': 40.0, 'height': 109.0, 'weight': 24.0, 'priority': 0, 'cost': 107.0}, {'id': 'P-206', 'length': 60.0, 'width': 47.0, 'height': 41.0, 'weight': 29.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-207', 'length': 70.0, 'width': 45.0, 'height': 95.0, 'weight': 46.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-208', 'length': 89.0, 'width': 50.0, 'height': 102.0, 'weight': 117.0, 'priority': 0, 'cost': 127.0}, {'id': 'P-209', 'length': 75.0, 'width': 44.0, 'height': 72.0, 'weight': 57.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-210', 'length': 45.0, 'width': 93.0, 'height': 88.0, 'weight': 64.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-211', 'length': 96.0, 'width': 95.0, 'height': 81.0, 'weight': 142.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-212', 'length': 105.0, 'width': 74.0, 'height': 48.0, 'weight': 96.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-213', 'length': 71.0, 'width': 50.0, 'height': 105.0, 'weight': 94.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-214', 'length': 58.0, 'width': 81.0, 'height': 61.0, 'weight': 40.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-215', 'length': 87.0, 'width': 89.0, 'height': 80.0, 'weight': 126.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-216', 'length': 44.0, 'width': 64.0, 'height': 83.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-217', 'length': 78.0, 'width': 74.0, 'height': 72.0, 'weight': 97.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-218', 'length': 90.0, 'width': 77.0, 'height': 59.0, 'weight': 63.0, 'priority': 0, 'cost': 134.0}, {'id': 'P-219', 'length': 94.0, 'width': 61.0, 'height': 76.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-220', 'length': 44.0, 'width': 104.0, 'height': 71.0, 'weight': 80.0, 'priority': 0, 'cost': 137.0}, {'id': 'P-221', 'length': 68.0, 'width': 44.0, 'height': 49.0, 'weight': 13.0, 'priority': 0, 'cost': 86.0}, {'id': 'P-222', 'length': 88.0, 'width': 73.0, 'height': 41.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-223', 'length': 83.0, 'width': 92.0, 'height': 109.0, 'weight': 145.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-224', 'length': 68.0, 'width': 99.0, 'height': 56.0, 'weight': 103.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-225', 'length': 54.0, 'width': 68.0, 'height': 93.0, 'weight': 52.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-226', 'length': 60.0, 'width': 72.0, 'height': 74.0, 'weight': 27.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-227', 'length': 59.0, 'width': 73.0, 'height': 96.0, 'weight': 58.0, 'priority': 0, 'cost': 118.0}, {'id': 'P-228', 'length': 98.0, 'width': 92.0, 'height': 51.0, 'weight': 128.0, 'priority': 0, 'cost': 75.0}, {'id': 'P-229', 'length': 69.0, 'width': 81.0, 'height': 104.0, 'weight': 171.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-230', 'length': 46.0, 'width': 48.0, 'height': 86.0, 'weight': 44.0, 'priority': 0, 'cost': 82.0}, {'id': 'P-231', 'length': 96.0, 'width': 68.0, 'height': 49.0, 'weight': 48.0, 'priority': 0, 'cost': 91.0}, {'id': 'P-232', 'length': 67.0, 'width': 84.0, 'height': 47.0, 'weight': 38.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-233', 'length': 71.0, 'width': 59.0, 'height': 101.0, 'weight': 120.0, 'priority': 0, 'cost': 63.0}, {'id': 'P-234', 'length': 43.0, 'width': 65.0, 'height': 104.0, 'weight': 60.0, 'priority': 0, 'cost': 101.0}, {'id': 'P-235', 'length': 80.0, 'width': 105.0, 'height': 84.0, 'weight': 61.0, 'priority': 0, 'cost': 95.0}, {'id': 'P-236', 'length': 91.0, 'width': 56.0, 'height': 56.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-237', 'length': 97.0, 'width': 74.0, 'height': 101.0, 'weight': 193.0, 'priority': 0, 'cost': 97.0}, {'id': 'P-238', 'length': 50.0, 'width': 69.0, 'height': 102.0, 'weight': 74.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-239', 'length': 79.0, 'width': 85.0, 'height': 71.0, 'weight': 94.0, 'priority': 0, 'cost': 93.0}, {'id': 'P-240', 'length': 101.0, 'width': 88.0, 'height': 65.0, 'weight': 84.0, 'priority': 0, 'cost': 127.0}, {'id': 'P-241', 'length': 71.0, 'width': 74.0, 'height': 91.0, 'weight': 25.0, 'priority': 0, 'cost': 115.0}, {'id': 'P-242', 'length': 89.0, 'width': 69.0, 'height': 53.0, 'weight': 48.0, 'priority': 0, 'cost': 118.0}, {'id': 'P-243', 'length': 69.0, 'width': 77.0, 'height': 105.0, 'weight': 98.0, 'priority': 0, 'cost': 76.0}, {'id': 'P-244', 'length': 76.0, 'width': 62.0, 'height': 75.0, 'weight': 24.0, 'priority': 0, 'cost': 111.0}, {'id': 'P-245', 'length': 53.0, 'width': 105.0, 'height': 80.0, 'weight': 61.0, 'priority': 0, 'cost': 67.0}, {'id': 'P-246', 'length': 60.0, 'width': 102.0, 'height': 61.0, 'weight': 58.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-247', 'length': 98.0, 'width': 62.0, 'height': 79.0, 'weight': 61.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-248', 'length': 77.0, 'width': 67.0, 'height': 52.0, 'weight': 70.0, 'priority': 0, 'cost': 139.0}, {'id': 'P-249', 'length': 89.0, 'width': 67.0, 'height': 55.0, 'weight': 66.0, 'priority': 0, 'cost': 88.0}, {'id': 'P-250', 'length': 65.0, 'width': 59.0, 'height': 102.0, 'weight': 105.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-251', 'length': 78.0, 'width': 44.0, 'height': 106.0, 'weight': 106.0, 'priority': 0, 'cost': 71.0}, {'id': 'P-252', 'length': 48.0, 'width': 110.0, 'height': 95.0, 'weight': 139.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-253', 'length': 91.0, 'width': 49.0, 'height': 99.0, 'weight': 99.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-254', 'length': 99.0, 'width': 51.0, 'height': 79.0, 'weight': 101.0, 'priority': 0, 'cost': 72.0}, {'id': 'P-255', 'length': 64.0, 'width': 98.0, 'height': 96.0, 'weight': 78.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-256', 'length': 92.0, 'width': 64.0, 'height': 66.0, 'weight': 117.0, 'priority': 0, 'cost': 99.0}, {'id': 'P-257', 'length': 67.0, 'width': 51.0, 'height': 54.0, 'weight': 40.0, 'priority': 0, 'cost': 103.0}, {'id': 'P-258', 'length': 71.0, 'width': 55.0, 'height': 82.0, 'weight': 43.0, 'priority': 0, 'cost': 138.0}, {'id': 'P-259', 'length': 84.0, 'width': 72.0, 'height': 86.0, 'weight': 55.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-260', 'length': 43.0, 'width': 49.0, 'height': 99.0, 'weight': 20.0, 'priority': 0, 'cost': 65.0}, {'id': 'P-261', 'length': 100.0, 'width': 77.0, 'height': 42.0, 'weight': 80.0, 'priority': 0, 'cost': 114.0}, {'id': 'P-262', 'length': 103.0, 'width': 92.0, 'height': 109.0, 'weight': 99.0, 'priority': 0, 'cost': 65.0}, {'id': 'P-263', 'length': 56.0, 'width': 83.0, 'height': 98.0, 'weight': 33.0, 'priority': 0, 'cost': 107.0}, {'id': 'P-264', 'length': 60.0, 'width': 68.0, 'height': 108.0, 'weight': 35.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-265', 'length': 47.0, 'width': 60.0, 'height': 58.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-266', 'length': 61.0, 'width': 88.0, 'height': 53.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-267', 'length': 54.0, 'width': 97.0, 'height': 98.0, 'weight': 130.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-268', 'length': 84.0, 'width': 63.0, 'height': 100.0, 'weight': 99.0, 'priority': 0, 'cost': 95.0}, {'id': 'P-269', 'length': 58.0, 'width': 56.0, 'height': 74.0, 'weight': 25.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-270', 'length': 52.0, 'width': 70.0, 'height': 47.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-271', 'length': 41.0, 'width': 44.0, 'height': 92.0, 'weight': 30.0, 'priority': 0, 'cost': 63.0}, {'id': 'P-272', 'length': 75.0, 'width': 64.0, 'height': 40.0, 'weight': 54.0, 'priority': 0, 'cost': 133.0}, {'id': 'P-273', 'length': 85.0, 'width': 79.0, 'height': 71.0, 'weight': 127.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-274', 'length': 75.0, 'width': 88.0, 'height': 110.0, 'weight': 114.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-275', 'length': 74.0, 'width': 77.0, 'height': 45.0, 'weight': 31.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-276', 'length': 46.0, 'width': 69.0, 'height': 62.0, 'weight': 29.0, 'priority': 0, 'cost': 70.0}, {'id': 'P-277', 'length': 54.0, 'width': 108.0, 'height': 105.0, 'weight': 93.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-278', 'length': 73.0, 'width': 44.0, 'height': 80.0, 'weight': 60.0, 'priority': 0, 'cost': 96.0}, {'id': 'P-279', 'length': 85.0, 'width': 99.0, 'height': 52.0, 'weight': 118.0, 'priority': 0, 'cost': 101.0}, {'id': 'P-280', 'length': 90.0, 'width': 61.0, 'height': 53.0, 'weight': 75.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-281', 'length': 55.0, 'width': 84.0, 'height': 105.0, 'weight': 57.0, 'priority': 0, 'cost': 95.0}, {'id': 'P-282', 'length': 107.0, 'width': 92.0, 'height': 54.0, 'weight': 147.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-283', 'length': 100.0, 'width': 97.0, 'height': 66.0, 'weight': 79.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-284', 'length': 70.0, 'width': 110.0, 'height': 52.0, 'weight': 86.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-285', 'length': 81.0, 'width': 108.0, 'height': 54.0, 'weight': 78.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-286', 'length': 93.0, 'width': 75.0, 'height': 73.0, 'weight': 133.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-287', 'length': 99.0, 'width': 86.0, 'height': 84.0, 'weight': 94.0, 'priority': 0, 'cost': 110.0}, {'id': 'P-288', 'length': 61.0, 'width': 101.0, 'height': 94.0, 'weight': 36.0, 'priority': 0, 'cost': 122.0}, {'id': 'P-289', 'length': 70.0, 'width': 43.0, 'height': 66.0, 'weight': 28.0, 'priority': 0, 'cost': 79.0}, {'id': 'P-290', 'length': 80.0, 'width': 69.0, 'height': 46.0, 'weight': 23.0, 'priority': 0, 'cost': 64.0}, {'id': 'P-291', 'length': 74.0, 'width': 81.0, 'height': 40.0, 'weight': 42.0, 'priority': 0, 'cost': 124.0}, {'id': 'P-292', 'length': 63.0, 'width': 100.0, 'height': 93.0, 'weight': 46.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-293', 'length': 56.0, 'width': 104.0, 'height': 56.0, 'weight': 78.0, 'priority': 0, 'cost': 81.0}, {'id': 'P-294', 'length': 88.0, 'width': 93.0, 'height': 44.0, 'weight': 30.0, 'priority': 0, 'cost': 69.0}, {'id': 'P-295', 'length': 49.0, 'width': 109.0, 'height': 69.0, 'weight': 32.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-296', 'length': 92.0, 'width': 81.0, 'height': 93.0, 'weight': 50.0, 'priority': 0, 'cost': 60.0}, {'id': 'P-297', 'length': 103.0, 'width': 101.0, 'height': 68.0, 'weight': 149.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-298', 'length': 44.0, 'width': 91.0, 'height': 86.0, 'weight': 57.0, 'priority': 0, 'cost': 83.0}, {'id': 'P-299', 'length': 83.0, 'width': 87.0, 'height': 80.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-300', 'length': 97.0, 'width': 69.0, 'height': 101.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-301', 'length': 61.0, 'width': 72.0, 'height': 69.0, 'weight': 76.0, 'priority': 0, 'cost': 72.0}, {'id': 'P-302', 'length': 64.0, 'width': 106.0, 'height': 65.0, 'weight': 98.0, 'priority': 0, 'cost': 84.0}, {'id': 'P-303', 'length': 57.0, 'width': 62.0, 'height': 106.0, 'weight': 75.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-304', 'length': 51.0, 'width': 68.0, 'height': 89.0, 'weight': 31.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-305', 'length': 53.0, 'width': 58.0, 'height': 63.0, 'weight': 22.0, 'priority': 0, 'cost': 104.0}, {'id': 'P-306', 'length': 88.0, 'width': 91.0, 'height': 90.0, 'weight': 57.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-307', 'length': 43.0, 'width': 82.0, 'height': 96.0, 'weight': 100.0, 'priority': 0, 'cost': 123.0}, {'id': 'P-308', 'length': 57.0, 'width': 64.0, 'height': 110.0, 'weight': 62.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-309', 'length': 104.0, 'width': 91.0, 'height': 60.0, 'weight': 135.0, 'priority': 0, 'cost': 66.0}, {'id': 'P-310', 'length': 65.0, 'width': 59.0, 'height': 43.0, 'weight': 15.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-311', 'length': 79.0, 'width': 101.0, 'height': 43.0, 'weight': 26.0, 'priority': 0, 'cost': 69.0}, {'id': 'P-312', 'length': 90.0, 'width': 97.0, 'height': 56.0, 'weight': 121.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-313', 'length': 91.0, 'width': 54.0, 'height': 54.0, 'weight': 73.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-314', 'length': 84.0, 'width': 53.0, 'height': 93.0, 'weight': 48.0, 'priority': 0, 'cost': 93.0}, {'id': 'P-315', 'length': 50.0, 'width': 75.0, 'height': 53.0, 'weight': 14.0, 'priority': 0, 'cost': 104.0}, {'id': 'P-316', 'length': 105.0, 'width': 103.0, 'height': 71.0, 'weight': 201.0, 'priority': 0, 'cost': 123.0}, {'id': 'P-317', 'length': 53.0, 'width': 86.0, 'height': 50.0, 'weight': 44.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-318', 'length': 86.0, 'width': 75.0, 'height': 99.0, 'weight': 47.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-319', 'length': 48.0, 'width': 102.0, 'height': 101.0, 'weight': 144.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-320', 'length': 64.0, 'width': 53.0, 'height': 57.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-321', 'length': 71.0, 'width': 78.0, 'height': 98.0, 'weight': 92.0, 'priority': 0, 'cost': 91.0}, {'id': 'P-322', 'length': 45.0, 'width': 66.0, 'height': 102.0, 'weight': 72.0, 'priority': 0, 'cost': 104.0}, {'id': 'P-323', 'length': 72.0, 'width': 98.0, 'height': 97.0, 'weight': 183.0, 'priority': 0, 'cost': 129.0}, {'id': 'P-324', 'length': 68.0, 'width': 40.0, 'height': 41.0, 'weight': 27.0, 'priority': 0, 'cost': 122.0}, {'id': 'P-325', 'length': 80.0, 'width': 63.0, 'height': 77.0, 'weight': 93.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-326', 'length': 84.0, 'width': 51.0, 'height': 45.0, 'weight': 17.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-327', 'length': 58.0, 'width': 96.0, 'height': 44.0, 'weight': 18.0, 'priority': 0, 'cost': 119.0}, {'id': 'P-328', 'length': 50.0, 'width': 78.0, 'height': 82.0, 'weight': 57.0, 'priority': 0, 'cost': 72.0}, {'id': 'P-329', 'length': 94.0, 'width': 65.0, 'height': 58.0, 'weight': 26.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-330', 'length': 105.0, 'width': 106.0, 'height': 97.0, 'weight': 271.0, 'priority': 0, 'cost': 75.0}, {'id': 'P-331', 'length': 71.0, 'width': 43.0, 'height': 88.0, 'weight': 64.0, 'priority': 0, 'cost': 91.0}, {'id': 'P-332', 'length': 57.0, 'width': 103.0, 'height': 79.0, 'weight': 63.0, 'priority': 0, 'cost': 108.0}, {'id': 'P-333', 'length': 100.0, 'width': 85.0, 'height': 72.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-334', 'length': 65.0, 'width': 99.0, 'height': 54.0, 'weight': 103.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-335', 'length': 91.0, 'width': 57.0, 'height': 95.0, 'weight': 47.0, 'priority': 0, 'cost': 140.0}, {'id': 'P-336', 'length': 49.0, 'width': 68.0, 'height': 72.0, 'weight': 33.0, 'priority': 0, 'cost': 114.0}, {'id': 'P-337', 'length': 40.0, 'width': 77.0, 'height': 102.0, 'weight': 52.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-338', 'length': 46.0, 'width': 88.0, 'height': 87.0, 'weight': 75.0, 'priority': 0, 'cost': 70.0}, {'id': 'P-339', 'length': 54.0, 'width': 76.0, 'height': 76.0, 'weight': 80.0, 'priority': 0, 'cost': 94.0}, {'id': 'P-340', 'length': 103.0, 'width': 90.0, 'height': 49.0, 'weight': 66.0, 'priority': 0, 'cost': 98.0}, {'id': 'P-341', 'length': 72.0, 'width': 87.0, 'height': 57.0, 'weight': 50.0, 'priority': 0, 'cost': 109.0}, {'id': 'P-342', 'length': 63.0, 'width': 66.0, 'height': 78.0, 'weight': 83.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-343', 'length': 107.0, 'width': 67.0, 'height': 77.0, 'weight': 98.0, 'priority': 0, 'cost': 130.0}, {'id': 'P-344', 'length': 55.0, 'width': 89.0, 'height': 92.0, 'weight': 111.0, 'priority': 0, 'cost': 95.0}, {'id': 'P-345', 'length': 43.0, 'width': 78.0, 'height': 47.0, 'weight': 43.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-346', 'length': 83.0, 'width': 95.0, 'height': 110.0, 'weight': 54.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-347', 'length': 53.0, 'width': 105.0, 'height': 102.0, 'weight': 96.0, 'priority': 0, 'cost': 116.0}, {'id': 'P-348', 'length': 89.0, 'width': 77.0, 'height': 56.0, 'weight': 60.0, 'priority': 0, 'cost': 89.0}, {'id': 'P-349', 'length': 99.0, 'width': 104.0, 'height': 68.0, 'weight': 70.0, 'priority': 0, 'cost': 80.0}, {'id': 'P-350', 'length': 85.0, 'width': 60.0, 'height': 69.0, 'weight': 52.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-351', 'length': 107.0, 'width': 41.0, 'height': 92.0, 'weight': 42.0, 'priority': 0, 'cost': 112.0}, {'id': 'P-352', 'length': 89.0, 'width': 43.0, 'height': 66.0, 'weight': 32.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-353', 'length': 66.0, 'width': 61.0, 'height': 70.0, 'weight': 33.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-354', 'length': 52.0, 'width': 70.0, 'height': 70.0, 'weight': 47.0, 'priority': 0, 'cost': 78.0}, {'id': 'P-355', 'length': 45.0, 'width': 60.0, 'height': 52.0, 'weight': 42.0, 'priority': 0, 'cost': 72.0}, {'id': 'P-356', 'length': 77.0, 'width': 99.0, 'height': 95.0, 'weight': 133.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-357', 'length': 40.0, 'width': 58.0, 'height': 56.0, 'weight': 15.0, 'priority': 0, 'cost': 110.0}, {'id': 'P-358', 'length': 81.0, 'width': 60.0, 'height': 74.0, 'weight': 55.0, 'priority': 0, 'cost': 93.0}, {'id': 'P-359', 'length': 101.0, 'width': 86.0, 'height': 98.0, 'weight': 188.0, 'priority': 0, 'cost': 103.0}, {'id': 'P-360', 'length': 80.0, 'width': 76.0, 'height': 53.0, 'weight': 23.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-361', 'length': 65.0, 'width': 61.0, 'height': 51.0, 'weight': 55.0, 'priority': 0, 'cost': 68.0}, {'id': 'P-362', 'length': 75.0, 'width': 61.0, 'height': 86.0, 'weight': 99.0, 'priority': 0, 'cost': 92.0}, {'id': 'P-363', 'length': 67.0, 'width': 72.0, 'height': 79.0, 'weight': 29.0, 'priority': 0, 'cost': 136.0}, {'id': 'P-364', 'length': 68.0, 'width': 53.0, 'height': 110.0, 'weight': 29.0, 'priority': 0, 'cost': 94.0}, {'id': 'P-365', 'length': 88.0, 'width': 110.0, 'height': 95.0, 'weight': 217.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-366', 'length': 56.0, 'width': 71.0, 'height': 105.0, 'weight': 112.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-367', 'length': 54.0, 'width': 69.0, 'height': 106.0, 'weight': 74.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-368', 'length': 71.0, 'width': 99.0, 'height': 97.0, 'weight': 178.0, 'priority': 0, 'cost': 85.0}, {'id': 'P-369', 'length': 84.0, 'width': 75.0, 'height': 58.0, 'weight': 92.0, 'priority': 0, 'cost': 110.0}, {'id': 'P-370', 'length': 106.0, 'width': 47.0, 'height': 100.0, 'weight': 95.0, 'priority': 0, 'cost': 68.0}, {'id': 'P-371', 'length': 91.0, 'width': 52.0, 'height': 48.0, 'weight': 50.0, 'priority': 0, 'cost': 106.0}, {'id': 'P-372', 'length': 110.0, 'width': 84.0, 'height': 79.0, 'weight': 182.0, 'priority': 0, 'cost': 96.0}, {'id': 'P-373', 'length': 62.0, 'width': 84.0, 'height': 72.0, 'weight': 108.0, 'priority': 0, 'cost': 105.0}, {'id': 'P-374', 'length': 81.0, 'width': 71.0, 'height': 101.0, 'weight': 169.0, 'priority': 0, 'cost': 96.0}, {'id': 'P-375', 'length': 48.0, 'width': 67.0, 'height': 97.0, 'weight': 35.0, 'priority': 0, 'cost': 99.0}, {'id': 'P-376', 'length': 101.0, 'width': 101.0, 'height': 89.0, 'weight': 73.0, 'priority': 0, 'cost': 96.0}, {'id': 'P-377', 'length': 101.0, 'width': 88.0, 'height': 105.0, 'weight': 118.0, 'priority': 0, 'cost': 80.0}, {'id': 'P-378', 'length': 59.0, 'width': 53.0, 'height': 89.0, 'weight': 61.0, 'priority': 0, 'cost': 131.0}, {'id': 'P-379', 'length': 68.0, 'width': 89.0, 'height': 98.0, 'weight': 58.0, 'priority': 0, 'cost': 77.0}, {'id': 'P-380', 'length': 41.0, 'width': 56.0, 'height': 62.0, 'weight': 22.0, 'priority': 0, 'cost': 102.0}, {'id': 'P-381', 'length': 64.0, 'width': 48.0, 'height': 69.0, 'weight': 60.0, 'priority': 0, 'cost': 87.0}, {'id': 'P-382', 'length': 102.0, 'width': 106.0, 'height': 43.0, 'weight': 41.0, 'priority': 0, 'cost': 130.0}, {'id': 'P-383', 'length': 85.0, 'width': 103.0, 'height': 60.0, 'weight': 61.0, 'priority': 0, 'cost': 83.0}, {'id': 'P-384', 'length': 69.0, 'width': 73.0, 'height': 60.0, 'weight': 16.0, 'priority': 0, 'cost': 97.0}, {'id': 'P-385', 'length': 64.0, 'width': 48.0, 'height': 40.0, 'weight': 23.0, 'priority': 0, 'cost': 113.0}, {'id': 'P-386', 'length': 63.0, 'width': 110.0, 'height': 65.0, 'weight': 88.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-387', 'length': 42.0, 'width': 47.0, 'height': 96.0, 'weight': 37.0, 'priority': 0, 'cost': 140.0}, {'id': 'P-388', 'length': 99.0, 'width': 89.0, 'height': 97.0, 'weight': 88.0, 'priority': 0, 'cost': 134.0}, {'id': 'P-389', 'length': 49.0, 'width': 95.0, 'height': 72.0, 'weight': 55.0, 'priority': 0, 'cost': 61.0}, {'id': 'P-390', 'length': 82.0, 'width': 106.0, 'height': 96.0, 'weight': 244.0, 'priority': 0, 'cost': 114.0}, {'id': 'P-391', 'length': 65.0, 'width': 87.0, 'height': 73.0, 'weight': 71.0, 'priority': 0, 'cost': 122.0}, {'id': 'P-392', 'length': 87.0, 'width': 63.0, 'height': 40.0, 'weight': 59.0, 'priority': 0, 'cost': 74.0}, {'id': 'P-393', 'length': 44.0, 'width': 47.0, 'height': 65.0, 'weight': 23.0, 'priority': 0, 'cost': 133.0}, {'id': 'P-394', 'length': 109.0, 'width': 90.0, 'height': 81.0, 'weight': 68.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-395', 'length': 60.0, 'width': 108.0, 'height': 73.0, 'weight': 112.0, 'priority': 0, 'cost': 107.0}, {'id': 'P-396', 'length': 102.0, 'width': 109.0, 'height': 42.0, 'weight': 118.0, 'priority': 0, 'cost': 120.0}, {'id': 'P-397', 'length': 80.0, 'width': 51.0, 'height': 59.0, 'weight': 51.0, 'priority': 0, 'cost': 81.0}, {'id': 'P-398', 'length': 52.0, 'width': 103.0, 'height': 85.0, 'weight': 68.0, 'priority': 0, 'cost': 130.0}, {'id': 'P-399', 'length': 45.0, 'width': 44.0, 'height': 89.0, 'weight': 22.0, 'priority': 0, 'cost': 63.0}, {'id': 'P-400', 'length': 52.0, 'width': 50.0, 'height': 64.0, 'weight': 37.0, 'priority': 0, 'cost': 71.0}]

containers = [{'id': 'U1', 'length': 224.0, 'width': 318.0, 'height': 162.0, 'weight': 2500.0}, {'id': 'U2', 'length': 224.0, 'width': 318.0, 'height': 162.0, 'weight': 2500.0}, {'id': 'U3', 'length': 244.0, 'width': 318.0, 'height': 244.0, 'weight': 2800.0}, {'id': 'U4', 'length': 244.0, 'width': 318.0, 'height': 244.0, 'weight': 2800.0}, {'id': 'U5', 'length': 244.0, 'width': 318.0, 'height': 285.0, 'weight': 3500.0}, {'id': 'U6', 'length': 244.0, 'width': 318.0, 'height': 285.0, 'weight': 3500.0}]

def plot(answer):
    import math
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    def getCube(limits=None):
        '''get the vertices, edges, and faces of a cuboid defined by its limits

        limits = np.array([[x_min, x_max],
                        [y_min, y_max],
                        [z_min, z_max]])
        '''
        if limits is None:
            limits = np.array([[0, 1], [0, 1], [0, 1]])
        v = np.array([[x, y, z] for x in limits[0] for y in limits[1] for z in limits[2]])
        e = np.array([[0, 1], [1, 3], [3, 2], [2, 0],
                      [4, 5], [5, 7], [7, 6], [6, 4],
                      [0, 4], [1, 5], [2, 6], [3, 7]])
        f = np.array([[0, 1, 3, 2], [4, 5, 7, 6],
                      [0, 1, 5, 4], [2, 3, 7, 6],
                      [0, 2, 6, 4], [1, 3, 7, 5]])

        return v, e, f

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim([0, 300])
    ax.set_ylim([0, 300])
    ax.set_zlim([0, 300])
    for package in answer:
        if package['container_id'] == "U6":
            continue
        x, y, z = package['x'], package['y'], package['z']
        dx, dy, dz = package['DimX'], package['DimY'], package['DimZ']
        v, e, f = getCube(np.array([[x, x + dx], [y, y + dy], [z, z + dz]]))
        ax.plot(*v.T, marker='o', color='k', ls='')
        for i, j in e:
            ax.plot(*v[[i, j], :].T, color='r', ls='-')
        # for i in f:
        #     if package.stable == -1:
        #         ax.add_collection3d(Poly3DCollection([v[i]], facecolors='red', linewidths=1, edgecolors='r', alpha=.25))
        #     elif package.stable:
        #         ax.add_collection3d(
        #             Poly3DCollection([v[i]], facecolors='cyan', linewidths=1, edgecolors='r', alpha=.25))
        #     else:
            ax.add_collection3d(
                Poly3DCollection([v[i] for i in f], facecolors='green', linewidths=1, edgecolors='r', alpha=.25))

    plt.show()
solution = container_loading_with_relative_constraints(cartons, containers)
# plot(solution)
for i in range(len(solution)):
    for j in range(i+1, len(solution)):
        if(solution[i]["container_id"] != solution[j]["container_id"]):
            continue
        if are_cubes_intersecting(solution[i], solution[j]):
            print("Cubes intersecting:", solution[i]["carton_id"], solution[j]["carton_id"])
print("Solution:", solution)
