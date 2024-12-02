import csv
from math import floor
from binsearch.model_binsearch import container_loading_with_relative_constraints as solver
from utils.lpp_utils import are_cubes_intersecting, is_box_inside_container, plot



file_path = 'output.csv'
# get_containers()

def binsearch(file_path = None, packageArray = None, uldArray = None):



    def get_more_packages(file_path = None, packageArray = None, uldArray = None):
        new_cartons = []
        containers = []
        new_solution = []
        container_wise_solution = {}
        container_assigned = []
        same_assignment_cartons = []
        extra_fitted_cartons = []
        cost_reduction = 0
        print("xxxxxxxxxxxxytewrsfd")
        print(uldArray)
        free_list=["U1","U2","U6"]

        if file_path is None:
            for container in uldArray:

                if container.id not in free_list:
                    continue

                container = {
                    "id": container.id,
                    "length": container.length,
                    "width": container.width,
                    "height": container.height,
                    "weight": container.weight_limit
                }
                container['free_space'] = container['length'] * container['width'] * container['height']
                same_assignment_cartons.append(container['id'])
                containers.append(container)
        else:
            file1_path = './ULD.csv'
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
        print(containers)
        container_assigned = {container['id']: [] for container in containers}
        container_lists = {container['id']: [] for container in containers}


        if file_path is None:
            for package in packageArray:
                package.dimensions = package.getDimensions()
                package.dimensions.sort()
                if (package.ULD == -1):
                    new_package = {
                            'id': package.id,
                            'length': package.dimensions[0],
                            'width': package.dimensions[1],
                            'height': package.dimensions[2],
                            'weight': package.weight,
                            'cost': package.cost,
                            'priority': package.priority
                        }
                    new_cartons.append(new_package)
                    print(new_package)

                elif package.ULD in free_list:
                    new_package = {
                        "id": package.id,
                        "length": package.dimensions[0],
                        "width": package.dimensions[1],
                        "height": package.dimensions[2],
                        "weight": package.weight,
                        "cost": package.cost,
                        "priority": package.priority
                    }
                    container_assigned[package.ULD].append(new_package)
            print(len(new_cartons))
        else:
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
                                    'priority': row[7]   
                                }
                            )
                            container['free_space'] -= dimensions[0] * dimensions[1] * dimensions[2]

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
                                'priority': row[7]
                            }
                        )

        

        old_new_cartons = new_cartons
        new_cartons = sorted(new_cartons, key=lambda x: (floor((x['length']*x['width']*x['height'])/100),-x['cost'],min(x['length'],x['width'],x['height'])))
        new_cartons = new_cartons[:25]

        if file_path is None:
            for container in container_assigned:
                original_solution = []
                for package in packageArray:
                    if package.ULD != container:
                        continue
                    package.dimensions = package.getDimensions()
                    original_solution.append({
                        "carton_id": package.id,
                        "container_id": package.ULD,
                        "x": package.position[0],
                        "y": package.position[1],
                        "z": package.position[2],
                        "DimX": package.dimensions[0],
                        "DimY": package.dimensions[1],
                        "DimZ": package.dimensions[2],
                        "weight": package.weight,
                        "cost": package.cost,
                        "priority": package.priority
                    })
                container_wise_solution[container] = original_solution

        for container in containers:
            print(container_assigned[container['id']].__len__())

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
        return old_new_cartons, new_cartons, containers, new_solution, container_wise_solution, same_assignment_cartons, extra_fitted_cartons

    old_new_cartons, new_cartons, containers, new_solution, container_wise_solution, same_assignment_cartons, extra_fitted_cartons = get_more_packages(file_path, packageArray, uldArray)
    print("done")

    # weight_cost_priority_info = {}
    # with open(file_path, mode='r') as file:
    #     csv_reader = csv.reader(file)
    #     for row in csv_reader:
    #         if not ' '.join(row).strip():
    #             continue
    #         weight_cost_priority_info[row[0]] = [int(row[4]), int(row[5]), row[7]]



    added_cartons = {}
    for every_container in container_wise_solution:
        print("Container ", every_container, "was modified")
        same_assignment_cartons.remove(every_container)
        added_cartons[every_container] = 1
        for assignment in container_wise_solution[every_container]:
        #     assignment['weight'] = weight_cost_priority_info[assignment['carton_id']][0]
        #     assignment['cost'] = weight_cost_priority_info[assignment['carton_id']][1]
        #     assignment['priority'] = weight_cost_priority_info[assignment['carton_id']][2]
            new_solution.append(assignment)


    for carton in old_new_cartons:
        if carton['id'] in extra_fitted_cartons:
            continue
        carton = {
            "carton_id": carton['id'],
            "container_id": '-1',
            "x": 0,
            "y": 0,
            "z": 0,
            "DimX": carton['length'],
            "DimY": carton['width'],
            "DimZ": carton['height'],
            "weight": carton['weight'],
            "cost": carton['cost'],
            "priority": carton['priority']
        }
        new_solution.append(carton)

    return new_solution

