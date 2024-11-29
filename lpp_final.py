import gurobipy as gp
from gurobipy import GRB
from cartons import cartons
from containers import containers
cartons = cartons()
containers = containers()

def container_loading_with_relative_constraints():
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
