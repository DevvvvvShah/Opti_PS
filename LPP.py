import gurobipy as gp
from gurobipy import GRB


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
    model.Params.LogToConsole = 1  # Show optimization logs

    # Define constants
    M = 1000  # Large constant for "big-M" constraints

    # Decision variables
    sij = {}  # Binary: carton i assigned to container j
    xi, yi, zi = {}, {}, {}  # Continuous: coordinates of FLB corner of carton i
    nj = {}
    orientation = {}  # Binary variables for carton orientation (rotation matrix)
    relative_position = {}  # Binary variables for relative positions (aik, bik, cik, dik, eik, fik)
    # Add variables
    x = model.addVar(vtype=GRB.BINARY, name="1")
    model.addConstr(x == 1)
    for container in containers:
        nj[container['id']] = model.addVar(vtype=GRB.INTEGER, name=f"n_{container['id']}")
    for carton in cartons:
        for container in containers:
            sij[(carton['id'], container['id'])] = model.addVar(vtype=GRB.BINARY,
                                                                name=f"s_{carton['id']}_{container['id']}")
        xi[carton['id']] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_{carton['id']}")
        yi[carton['id']] = model.addVar(vtype=GRB.CONTINUOUS, name=f"y_{carton['id']}")
        zi[carton['id']] = model.addVar(vtype=GRB.CONTINUOUS, name=f"z_{carton['id']}")
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
        model.addConstr(sum(sij[(carton['id'], container['id'])] for container in containers) == 1,
                        name=f"assign_{carton['id']}")
    for container in containers:
        model.addConstr(sum(sij[(carton['id'], container['id'])] for carton in cartons) <= M*nj[container['id']],
                        name=f"assign_{container['id']}")
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
        print("Container:", container['id'])
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

        # Objective: Minimize unused space
    unused_space = sum(
        sij[(carton['id'], container['id'])] * (
                container['length'] * container['width'] * container['height'] -
                carton['length'] * carton['width'] * carton['height']
        )
        for carton in cartons for container in containers
    )
    model.setObjective(unused_space, GRB.MINIMIZE)
    # Optimize the model
    model.optimize()
    # Extract the solution
    if model.status == GRB.OPTIMAL:
        print("Optimal solution found. Checking constraints:")
        for c in model.getConstrs():
            lhs = model.getRow(c).getValue()
            rhs = c.RHS
            print(f"{c.ConstrName}: LHS = {lhs}, RHS = {rhs}, Sense = {c.Sense}")
        # print(sij["P-365", "U6"].X)
        # print(sij["P-165", "U6"].X)
        model.printQuality()
        solution = []
        # for container in containers:
        for carton in cartons:
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


cartons = [
    {"id": "P-365", "length": 88, "width": 95, "height": 110, "weight": 217},
    {"id": "P-165", "length": 93, "width": 96, "height": 103, "weight": 267},
    {"id": "P-346", "length": 83, "width": 95, "height": 110, "weight": 54},
    {"id": "P-394", "length": 81, "width": 90, "height": 109, "weight": 68},
    {"id": "P-105", "length": 80, "width": 95, "height": 103, "weight": 225},
    {"id": "P-211", "length": 81, "width": 95, "height": 96, "weight": 142},
    {"id": "P-274", "length": 75, "width": 88, "height": 110, "weight": 114},
    {"id": "P-356", "length": 77, "width": 95, "height": 99, "weight": 133},
    {"id": "P-297", "length": 68, "width": 101, "height": 103, "weight": 149},
    {"id": "P-134", "length": 80, "width": 88, "height": 97, "weight": 150},
    {"id": "P-300", "length": 69, "width": 97, "height": 101, "weight": 57},
    {"id": "P-283", "length": 66, "width": 97, "height": 100, "weight": 79},
    {"id": "P-41", "length": 68, "width": 90, "height": 104, "weight": 72},
    {"id": "P-145", "length": 75, "width": 79, "height": 106, "weight": 66},
    {"id": "P-133", "length": 63, "width": 91, "height": 109, "weight": 174},
    {"id": "P-215", "length": 80, "width": 87, "height": 89, "weight": 126},
    {"id": "P-277", "length": 54, "width": 105, "height": 108, "weight": 93},
    {"id": "P-333", "length": 72, "width": 85, "height": 100, "weight": 59},
    {"id": "P-139", "length": 75, "width": 84, "height": 96, "weight": 123},
    # {"id": "P-255", "length": 64, "width": 96, "height": 98, "weight": 78},
    # {"id": "P-73", "length": 63, "width": 86, "height": 104, "weight": 79},
    # {"id": "P-252", "length": 48, "width": 95, "height": 110, "weight": 139},
    # {"id": "P-50", "length": 64, "width": 73, "height": 104, "weight": 75},
    # {"id": "P-2", "length": 56, "width": 81, "height": 99, "weight": 53},
    # {"id": "P-264", "length": 60, "width": 68, "height": 108, "weight": 35},
    # {"id": "P-46", "length": 62, "width": 71, "height": 94, "weight": 39},
    # {"id": "P-187", "length": 54, "width": 78, "height": 84, "weight": 97},
    # {"id": "P-68", "length": 46, "width": 81, "height": 92, "weight": 62},
    # {"id": "P-49", "length": 40, "width": 69, "height": 100, "weight": 55}
]
containers = [
    {"id": "U5", "length": 244, "width": 318, "height": 285, "weight": 3500}
    # {"id": "U6", "length": 244, "width": 318, "height": 285, "weight": 3500}
]
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
        if package['container_id'] == "U5" :
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
plot(solution)
print("Solution:", solution)
