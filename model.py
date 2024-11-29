import gurobipy as gp
from gurobipy import GRB
from cartons import cartons
from containers import containers
cartons = cartons()
containers = containers()

def container_loading_with_relative_constraints():
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
    # extra constraints redundant
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
    # redundant constraints
    # for container in containers:
    #     model.addConstr(sum(sij[(carton['id'], container['id'])] for carton in cartons) <= M*nj[container['id']],
    #  name=f"assign_{container['id']}")


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
        # weight constraints
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

def container_model_with_correct_objectives():
    # Create a model
    model = gp.Model("3D_Container_Loading_with_Relative_Positioning")
    # model.Params.LogToConsole = 1  # Show optimization logs

    # Define constants
    M = 100000  # Large constant for "big-M" constraints

    # Decision variables
    sij = {}  # Binary: carton i assigned to container j
    xi, yi, zi = {}, {}, {}  # Continuous: coordinates of FLB corner of carton i
    pj = {}
    orientation = {}  # Binary variables for carton orientation (rotation matrix)
    relative_position = {}  # Binary variables for relative positions (aik, bik, cik, dik, eik, fik)
    # Add variables
    x = model.addVar(vtype=GRB.BINARY, name="1")
    model.addConstr(x == 1)
    # extra constraints redundant
    # for container in containers:
    #     nj[container['id']] = model.addVar(vtype=GRB.INTEGER, name=f"n_{container['id']}")
    for container in containers:
        pj[container['id']] = model.addVar(vtype=GRB.BINARY, name=f"contains_priority_{container['id']}")
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
    # redundant constraints
    # for container in containers:
    #     model.addConstr(sum(sij[(carton['id'], container['id'])] for carton in cartons) <= M*nj[container['id']],
    #  name=f"assign_{container['id']}")


    # check for priority packages spread :
    for container in containers:
        for carton in cartons:
            model.addConstr(pj[container['id']] >= sij[(carton['id'], container['id'])] * carton['priority'], name=f"priority_{carton['id']}_{container['id']}")

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
        # weight constraints
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
    penalty = 5000 * sum(pj[container['id']] for container in containers)
    for carton in cartons:
        s = 1
        for container in containers:
            s -= sij[(carton['id'], container['id'])]
        penalty += s * carton['cost']
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
        #debugging statements for constraints
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
        print(solution)
        return solution
    else:
        print("No feasible solution found.")

#
# cartons = [{'id': 'P-2', 'length': 56.0, 'width': 99.0, 'height': 81.0, 'weight': 53.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-3', 'length': 42.0, 'width': 101.0, 'height': 51.0, 'weight': 17.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-6', 'length': 91.0, 'width': 56.0, 'height': 84.0, 'weight': 47.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-9', 'length': 73.0, 'width': 71.0, 'height': 88.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-10', 'length': 88.0, 'width': 70.0, 'height': 85.0, 'weight': 81.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-15', 'length': 84.0, 'width': 49.0, 'height': 60.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-16', 'length': 48.0, 'width': 93.0, 'height': 63.0, 'weight': 82.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-17', 'length': 83.0, 'width': 63.0, 'height': 57.0, 'weight': 29.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-20', 'length': 88.0, 'width': 106.0, 'height': 56.0, 'weight': 71.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-23', 'length': 51.0, 'width': 50.0, 'height': 110.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-36', 'length': 86.0, 'width': 80.0, 'height': 78.0, 'weight': 146.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-41', 'length': 104.0, 'width': 90.0, 'height': 68.0, 'weight': 72.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-42', 'length': 62.0, 'width': 109.0, 'height': 41.0, 'weight': 46.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-45', 'length': 91.0, 'width': 72.0, 'height': 81.0, 'weight': 92.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-46', 'length': 71.0, 'width': 62.0, 'height': 94.0, 'weight': 39.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-49', 'length': 69.0, 'width': 40.0, 'height': 100.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-50', 'length': 73.0, 'width': 104.0, 'height': 64.0, 'weight': 75.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-68', 'length': 92.0, 'width': 46.0, 'height': 81.0, 'weight': 62.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-69', 'length': 84.0, 'width': 47.0, 'height': 54.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-71', 'length': 99.0, 'width': 43.0, 'height': 60.0, 'weight': 41.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-73', 'length': 104.0, 'width': 86.0, 'height': 63.0, 'weight': 79.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-82', 'length': 66.0, 'width': 71.0, 'height': 97.0, 'weight': 130.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-86', 'length': 65.0, 'width': 63.0, 'height': 41.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-94', 'length': 67.0, 'width': 98.0, 'height': 66.0, 'weight': 95.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-103', 'length': 44.0, 'width': 78.0, 'height': 102.0, 'weight': 84.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-105', 'length': 80.0, 'width': 95.0, 'height': 103.0, 'weight': 225.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-106', 'length': 90.0, 'width': 54.0, 'height': 92.0, 'weight': 100.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-109', 'length': 98.0, 'width': 79.0, 'height': 44.0, 'weight': 53.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-112', 'length': 63.0, 'width': 79.0, 'height': 67.0, 'weight': 20.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-117', 'length': 52.0, 'width': 49.0, 'height': 65.0, 'weight': 33.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-124', 'length': 54.0, 'width': 104.0, 'height': 72.0, 'weight': 96.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-125', 'length': 68.0, 'width': 85.0, 'height': 91.0, 'weight': 139.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-126', 'length': 85.0, 'width': 64.0, 'height': 60.0, 'weight': 94.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-129', 'length': 110.0, 'width': 59.0, 'height': 85.0, 'weight': 64.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-133', 'length': 63.0, 'width': 109.0, 'height': 91.0, 'weight': 174.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-134', 'length': 80.0, 'width': 88.0, 'height': 97.0, 'weight': 150.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-136', 'length': 47.0, 'width': 66.0, 'height': 102.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-139', 'length': 96.0, 'width': 84.0, 'height': 75.0, 'weight': 123.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-142', 'length': 92.0, 'width': 74.0, 'height': 83.0, 'weight': 169.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-145', 'length': 75.0, 'width': 106.0, 'height': 79.0, 'weight': 66.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-147', 'length': 65.0, 'width': 46.0, 'height': 55.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-148', 'length': 67.0, 'width': 100.0, 'height': 49.0, 'weight': 50.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-150', 'length': 54.0, 'width': 42.0, 'height': 58.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-157', 'length': 88.0, 'width': 88.0, 'height': 54.0, 'weight': 30.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-162', 'length': 46.0, 'width': 104.0, 'height': 65.0, 'weight': 36.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-163', 'length': 49.0, 'width': 83.0, 'height': 83.0, 'weight': 45.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-165', 'length': 103.0, 'width': 96.0, 'height': 93.0, 'weight': 267.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-168', 'length': 68.0, 'width': 87.0, 'height': 88.0, 'weight': 109.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-180', 'length': 80.0, 'width': 71.0, 'height': 59.0, 'weight': 43.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-181', 'length': 98.0, 'width': 58.0, 'height': 57.0, 'weight': 93.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-183', 'length': 105.0, 'width': 72.0, 'height': 57.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-187', 'length': 54.0, 'width': 84.0, 'height': 78.0, 'weight': 97.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-188', 'length': 86.0, 'width': 51.0, 'height': 51.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-199', 'length': 58.0, 'width': 67.0, 'height': 73.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-207', 'length': 70.0, 'width': 45.0, 'height': 95.0, 'weight': 46.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-211', 'length': 96.0, 'width': 95.0, 'height': 81.0, 'weight': 142.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-212', 'length': 105.0, 'width': 74.0, 'height': 48.0, 'weight': 96.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-214', 'length': 58.0, 'width': 81.0, 'height': 61.0, 'weight': 40.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-215', 'length': 87.0, 'width': 89.0, 'height': 80.0, 'weight': 126.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-216', 'length': 44.0, 'width': 64.0, 'height': 83.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-217', 'length': 78.0, 'width': 74.0, 'height': 72.0, 'weight': 97.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-219', 'length': 94.0, 'width': 61.0, 'height': 76.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-222', 'length': 88.0, 'width': 73.0, 'height': 41.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-224', 'length': 68.0, 'width': 99.0, 'height': 56.0, 'weight': 103.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-226', 'length': 60.0, 'width': 72.0, 'height': 74.0, 'weight': 27.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-232', 'length': 67.0, 'width': 84.0, 'height': 47.0, 'weight': 38.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-236', 'length': 91.0, 'width': 56.0, 'height': 56.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-238', 'length': 50.0, 'width': 69.0, 'height': 102.0, 'weight': 74.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-252', 'length': 48.0, 'width': 110.0, 'height': 95.0, 'weight': 139.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-255', 'length': 64.0, 'width': 98.0, 'height': 96.0, 'weight': 78.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-264', 'length': 60.0, 'width': 68.0, 'height': 108.0, 'weight': 35.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-265', 'length': 47.0, 'width': 60.0, 'height': 58.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-266', 'length': 61.0, 'width': 88.0, 'height': 53.0, 'weight': 37.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-270', 'length': 52.0, 'width': 70.0, 'height': 47.0, 'weight': 12.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-273', 'length': 85.0, 'width': 79.0, 'height': 71.0, 'weight': 127.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-274', 'length': 75.0, 'width': 88.0, 'height': 110.0, 'weight': 114.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-275', 'length': 74.0, 'width': 77.0, 'height': 45.0, 'weight': 31.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-277', 'length': 54.0, 'width': 108.0, 'height': 105.0, 'weight': 93.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-280', 'length': 90.0, 'width': 61.0, 'height': 53.0, 'weight': 75.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-282', 'length': 107.0, 'width': 92.0, 'height': 54.0, 'weight': 147.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-283', 'length': 100.0, 'width': 97.0, 'height': 66.0, 'weight': 79.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-284', 'length': 70.0, 'width': 110.0, 'height': 52.0, 'weight': 86.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-285', 'length': 81.0, 'width': 108.0, 'height': 54.0, 'weight': 78.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-295', 'length': 49.0, 'width': 109.0, 'height': 69.0, 'weight': 32.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-297', 'length': 103.0, 'width': 101.0, 'height': 68.0, 'weight': 149.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-299', 'length': 83.0, 'width': 87.0, 'height': 80.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-300', 'length': 97.0, 'width': 69.0, 'height': 101.0, 'weight': 57.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-304', 'length': 51.0, 'width': 68.0, 'height': 89.0, 'weight': 31.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-310', 'length': 65.0, 'width': 59.0, 'height': 43.0, 'weight': 15.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-319', 'length': 48.0, 'width': 102.0, 'height': 101.0, 'weight': 144.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-320', 'length': 64.0, 'width': 53.0, 'height': 57.0, 'weight': 55.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-329', 'length': 94.0, 'width': 65.0, 'height': 58.0, 'weight': 26.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-333', 'length': 100.0, 'width': 85.0, 'height': 72.0, 'weight': 59.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-345', 'length': 43.0, 'width': 78.0, 'height': 47.0, 'weight': 43.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-346', 'length': 83.0, 'width': 95.0, 'height': 110.0, 'weight': 54.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-350', 'length': 85.0, 'width': 60.0, 'height': 69.0, 'weight': 52.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-352', 'length': 89.0, 'width': 43.0, 'height': 66.0, 'weight': 32.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-353', 'length': 66.0, 'width': 61.0, 'height': 70.0, 'weight': 33.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-356', 'length': 77.0, 'width': 99.0, 'height': 95.0, 'weight': 133.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-360', 'length': 80.0, 'width': 76.0, 'height': 53.0, 'weight': 23.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-365', 'length': 88.0, 'width': 110.0, 'height': 95.0, 'weight': 217.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-366', 'length': 56.0, 'width': 71.0, 'height': 105.0, 'weight': 112.0, 'priority': 1, 'cost': 10000000000.0}, {'id': 'P-394', 'length': 109.0, 'width': 90.0, 'height': 81.0, 'weight': 68.0, 'priority': 1, 'cost': 10000000000.0}]
#
#
# containers = [{'id': 'U1', 'length': 224.0, 'width': 318.0, 'height': 162.0, 'weight': 2500.0}, {'id': 'U2', 'length': 224.0, 'width': 318.0, 'height': 162.0, 'weight': 2500.0}, {'id': 'U3', 'length': 244.0, 'width': 318.0, 'height': 244.0, 'weight': 2800.0}, {'id': 'U4', 'length': 244.0, 'width': 318.0, 'height': 244.0, 'weight': 2800.0}, {'id': 'U5', 'length': 244.0, 'width': 318.0, 'height': 285.0, 'weight': 3500.0}, {'id': 'U6', 'length': 244.0, 'width': 318.0, 'height': 285.0, 'weight': 3500.0}]
#
#
container_model_with_correct_objectives()
# solution = container_loading_with_relative_constraints(cartons, containers)
# # plot(solution)
# for i in range(len(solution)):
#     for j in range(i+1, len(solution)):
#         if(solution[i]["container_id"] != solution[j]["container_id"]):
#             continue
#         if are_cubes_intersecting(solution[i], solution[j]):
#             print("Cubes intersecting:", solution[i]["carton_id"], solution[j]["carton_id"])
# print("Solution:", solution)
