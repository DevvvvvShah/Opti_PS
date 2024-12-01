import csv
from math import floor
from model_binsearch import container_loading_with_relative_constraints as solver


new_cartons = []
containers = []
new_solution = []
container_wise_solution = {}
container_assigned = []
same_assignment_cartons = []
extra_fitted_cartons = []

cost_reduction = 0

file_path = 'greedyOutput.csv'
# get_containers()

# def get_containers():
def get_more_packages(file_path):
    file1_path = './ULD.csv'
    global new_cartons
    global cost_reduction 
    global container_lists
    global containers
    global container_assigned
    with open(file1_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            container = {
                "id": row[0],
                "length": float(row[1]),
                "width": float(row[2]),
                "height": float(row[3]),
                "weight": float(row[4])
            }
            same_assignment_cartons.append(container['id'])
            container['free_space'] = container['length'] * container['width'] * container['height']
            containers.append(container)

    container_assigned = {container['id']: [] for container in containers}
    container_lists = {container['id']: [] for container in containers}

    for container in containers:
        # cartons = []
        # print(container['id'])
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if not ' '.join(row).strip():
                    continue
                if row[1] == container['id']:
                    package_id = row[0]
                    dimensions = eval(row[3])
                    # print("solving for ", package_id, "th package")
                    container_assigned[container['id']].append(
                        {
                            'id': package_id,
                            'length': dimensions[0],
                            'width': dimensions[1],
                            'height': dimensions[2],
                            'weight': int(row[4]),
                            'cost' : int(row[5]),
                            'Priority': row[7]   
                        }
                    )
                    container['free_space'] -= dimensions[0] * dimensions[1] * dimensions[2]

    # containers.sort(key=lambda x: x['length'] * x['width'] * x['height'])

    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if not ' '.join(row).strip():
                continue
            if row[1] == '-1':
                package_id = row[0]
                dimensions = eval(row[3])
                new_cartons.append(
                    {
                        'id': package_id,
                        'length': dimensions[0],
                        'width': dimensions[1],
                        'height': dimensions[2],
                        'weight': int(row[4]),
                        'cost': int(row[5]),
                        'Priority': row[7]
                    }
                )
    new_cartons = sorted(new_cartons, key=lambda x: (floor((x['length']*x['width']*x['height'])/100),min(x['length'],x['width'],x['height']),x['weight'],x['cost']))
    new_cartons = new_cartons[:5]
    for i in new_cartons:
        containers=sorted(containers,key=lambda x: x['free_space'],reverse=True)
        for container in containers:
            container_assigned[container['id']].append(i)
            obtained_solution = solver(container_assigned[container['id']], [container])
            if obtained_solution:
                extra_fitted_cartons.append(i['id'])
                container_lists[container['id']].append(i)
                cost_reduction += i['cost']
                container['free_space'] -= i['length'] * i['width'] * i['height']
                print()
                print()
                print("------------------")
                print("------------------")
                print(i["id"])
                print(container['id'])
                print("------------------")
                print("------------------")
                print()
                print()
                print("###")
                # print(obtained_solution)
                print("###")
                current_container = obtained_solution[0]['container_id']
                container_wise_solution[current_container] = obtained_solution
                break
            else:
                container_assigned[container['id']].pop()
    
    for container_id, packages in container_lists.items():
        print(f"Container {container_id} contains packages: {packages}")

    print(cost_reduction)

get_more_packages(file_path)
print("done")

weight_cost_priority_info = {}
with open(file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        if not ' '.join(row).strip():
            continue
        weight_cost_priority_info[row[0]] = [int(row[4]), int(row[5]), row[7]]



added_cartons = {}
for every_container in container_wise_solution:
    print("Container ", every_container, "was modified")
    same_assignment_cartons.remove(every_container)
    added_cartons[every_container] = 1
    for assignment in container_wise_solution[every_container]:
        assignment['weight'] = weight_cost_priority_info[assignment['carton_id']][0]
        assignment['cost'] = weight_cost_priority_info[assignment['carton_id']][1]
        assignment['Priority'] = weight_cost_priority_info[assignment['carton_id']][2]
        new_solution.append(assignment)


with open(file_path, mode='r') as file: 
    csv_reader = csv.reader(file)
    for row in csv_reader:
        if not ' '.join(row).strip():
            continue    
        if row[1] not in added_cartons and row[0] not in extra_fitted_cartons:
            carton = {
                "carton_id": row[0],
                "container_id": row[1],
                "x": eval(row[2])[0],
                "y": eval(row[2])[1],
                "z": eval(row[2])[2],
                "DimX": eval(row[3])[0],
                "DimY": eval(row[3])[1],
                "DimZ": eval(row[3])[2],
                "weight": int(row[4]),
                "cost": int(row[5]),
                "Priority": row[7]
            }
            new_solution.append(carton)



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

    num_containers = len(containers)
    fig = plt.figure(figsize=(15, 15))
    for idx, container in enumerate(containers):
        ax = fig.add_subplot(math.ceil(num_containers / 3), 3, idx + 1, projection='3d')
        ax.set_xlim([0, container['length']])
        ax.set_ylim([0, container['width']])
        ax.set_zlim([0, container['height']])
        ax.set_title(f"Container {container['id']}")
        for package in answer:
            if package['container_id'] != container['id']:
                continue
            x, y, z = package['x'], package['y'], package['z']
            dx, dy, dz = package['DimX'], package['DimY'], package['DimZ']
            v, e, f = getCube(np.array([[x, x + dx], [y, y + dy], [z, z + dz]]))
            ax.plot(*v.T, marker='o', color='k', ls='')
            for i, j in e:
                ax.plot(*v[[i, j], :].T, color='r', ls='-')
                ax.add_collection3d(
                    Poly3DCollection([v[i] for i in f], facecolors='green', linewidths=1, edgecolors='r', alpha=.25))

    plt.tight_layout()
    plt.show()

def is_box_inside_container(box, container):
    """
    Verifies if a box lies completely inside a container.

    :param box: Dictionary with keys 'x', 'y', 'z', 'DimX', 'DimY', 'DimZ'
    :param container: Dictionary with keys 'length', 'width', 'height'
    :return: True if the box is inside the container, False otherwise
    """
    return (0 <= box['x'] and box['x'] + box['DimX'] <= container['length'] and
            0 <= box['y'] and box['y'] + box['DimY'] <= container['width'] and
            0 <= box['z'] and box['z'] + box['DimZ'] <= container['height'])

for i in range(len(new_solution)):
    for j in range(i + 1, len(new_solution)):
        if (new_solution[i]["container_id"] != new_solution[j]["container_id"]):
            continue
        if are_cubes_intersecting(new_solution[i], new_solution[j]):
            with open("intersecting_log.txt", "a") as log_file:
                log_file.write(f"Cubes intersecting: {new_solution[i]['carton_id']} {new_solution[j]['carton_id']} in container {new_solution[i]['container_id']}\n")
for i in range(len(new_solution)):
    for j in range(len(containers)):
        if new_solution[i]['container_id'] == containers[j]['id']:
            if is_box_inside_container(new_solution[i], containers[j]) == 0:
                print(f"out of range ! carton : {new_solution[i]['carton_id']}")
                
print("New solution is valid : ")
print(new_solution)
with open("new_solution.txt", "w") as file:
    for solution in new_solution:
        file.write(f"{solution}\n")
plot(new_solution)

