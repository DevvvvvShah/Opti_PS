import matplotlib
import numpy as np
from cartons import cartons
from containers import containers
cartons = cartons()
containers = containers()
from model import container_loading_with_relative_constraints as solver
# print(len(cartons))
# print(cartons)
# print(len(containers))
# print(containers)
solution = solver()

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


for i in range(len(solution)):
    for j in range(i + 1, len(solution)):
        if solution[i]["container_id"] != solution[j]["container_id"]:
            continue
        if are_cubes_intersecting(solution[i], solution[j]):
            print("Cubes intersecting:", solution[i]["carton_id"], solution[j]["carton_id"])
for i in range(len(solution)):
    for j in range(len(containers)):
        if solution[i]['container_id'] == containers[j]['id']:
            if is_box_inside_container(solution[i], containers[j]) == 0:
                print(f"out of range ! carton : {solution[i]['carton_id']}")
print("Found a valid solution: ")
print(solution)
plot(solution)
