import csv
from math import floor
from model_binsearch import container_loading_with_relative_constraints as solver


new_cartons = []
containers = []

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
                            'weight': int(row[4])
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
                        'cost': int(row[5])
                    }
                )
    new_cartons = sorted(new_cartons, key=lambda x: (floor((x['length']*x['width']*x['height'])/100),min(x['length'],x['width'],x['height']),x['weight'],x['cost']))
    new_cartons = new_cartons[:5]
    

    for i in new_cartons:

        containers=sorted(containers,key=lambda x: x['free_space'],reverse=True)
        
        for container in containers:
            container_assigned[container['id']].append(i)
            if solver(container_assigned[container['id']], [container]):
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
                break
            else:
                container_assigned[container['id']].pop()
    
    for container_id, packages in container_lists.items():
        print(f"Container {container_id} contains packages: {packages}")

    print(cost_reduction)

    # return temp

# def get_assigned_packages(file_path):
#     with open(file_path, mode='r') as file:
#         csv_reader = csv.reader(file)
#         for row in csv_reader:
#             if not ' '.join(row).strip():
#                 continue
#             if row[1] == 'U5':
#                 package_id = row[0]
#                 dimensions = eval(row[3])
#                 cartons.append(
#                     {
#                         'id': package_id,
#                         'length': dimensions[0],
#                         'width': dimensions[1],
#                         'height': dimensions[2],
#                         'weight': int(row[4])
#                     }
#                 )

# def assign(file_path):
#     global new_cartons
#     global cost_reduction 
#     global container_lists
#     global containers
#     global container_assigned

        


# def get_more_packages(file_path):
#     global new_cartons
#     global cost_reduction 
#     global container_lists
#     global containers
#     global container_assigned
    # print(container_assigned)
    # with open(file_path, mode='r') as file:
    #     csv_reader = csv.reader(file)
    #     for row in csv_reader:
    #         if not ' '.join(row).strip():
    #             continue
    #         if row[1] == '-1':
    #             package_id = row[0]
    #             dimensions = eval(row[3])
    #             new_cartons.append(
    #                 {
    #                     'id': package_id,
    #                     'length': dimensions[0],
    #                     'width': dimensions[1],
    #                     'height': dimensions[2],
    #                     'weight': int(row[4]),
    #                     'cost': int(row[5])
    #                 }
    #             )
    # new_cartons = sorted(new_cartons, key=lambda x: (floor((x['length']*x['width']*x['height'])/100),min(x['length'],x['width'],x['height']),x['weight'],x['cost']))
    # new_cartons = new_cartons[:5]
    # container_lists = {container['id']: [] for container in containers}

    # for i in new_cartons:
    #     containers=sorted(containers,key=lambda x: x['free_space'],reverse=True)
        
    #     for container in containers:
    #         container_assigned[container['id']].append(i)
    #         temp=solver(container_assigned[container['id']], [container])
    #         if temp:
    #             container_lists[container['id']].append(i)
    #             cost_reduction += i['cost']
    #             container['free_space'] -= i['length'] * i['width'] * i['height']
    #             print()
    #             print()
    #             print("------------------")
    #             print("------------------")
    #             print(i["id"])
    #             print(container['id'])
    #             print("------------------")
    #             print("------------------")
    #             print()
    #             print()
    #             break
    #         else:
    #             container_assigned[container['id']].pop()
    
    # for container_id, packages in container_lists.items():
    #     print(f"Container {container_id} contains packages: {packages}")

    # print(cost_reduction)

    # return temp


    # max_cost=0
    # ind=-1
    # for i in new_cartons:
    #     cartons.append(i)
    #     x=i['id']
    #     print("solving for ", x, "th package")
    #     if solver(cartons, containers):
    #         if i['cost']>max_cost:
    #             max_cost=i['cost']
    #             ind=i
    #         print(x)
    #         print("Possible")
    #     else:
    #         print(x)
    #         print("Not possible")
    #     cartons.pop()
    # print("Max cost obtained is ",max_cost," for package ",ind['id'])
    
    

# def get(file_path):
#     with open(file_path, mode='r') as file:
#         csv_reader = csv.reader(file)
#         x=0
#         for row in csv_reader:
#             if not ' '.join(row).strip():
#                 continue
#             if row[1]=="-1":
#                 # x+=1
#                 # if(x==10):
#                 #     break
#                 package_id = row[0]
#                 dimensions = eval(row[3])
#                 # print("ADDAD")
#                 if(x>=1):
#                     cartons.pop()
#                 cartons.append(
#                     {
#                         'id': package_id,
#                         'length': dimensions[0],
#                         'width': dimensions[1],
#                         'height': dimensions[2],
#                         'weight': int(row[4])
#                     }
#                 )
#                 print("solving for ", x, "th package")
#                 if solver(cartons, containers):
#                     print(x)
#                     print("Possible")
#                 else:
#                     print(x)
#                     print("Not possible")
            


# assign(file_path)
get_more_packages(file_path)

print(cost_reduction)

# get_assigned_packages(file_path)
# assigned_count = len(cartons)
# get_more_packages(file_path) 
# get(file_path)
# print(len(cartons))

# max_cartons = 0

# def binsearch(cartons, containers):
#     global max_cartons
#     left, right = assigned_count, len(cartons)
#     while left <= right:
#         mid = (left + right) // 2
#         print("Trying for ", mid, "cartons", sep=" ")
#         if solver(cartons[:mid], containers):
#             print("Possible with ", mid, "cartons", sep=" ")
#             max_cartons = mid
#             left = mid + 1
#         else:
#             print("Not possible with ", mid, "cartons", sep=" ")
#             right = mid - 1

#     return max_cartons



# binsearch(cartons, containers)
# print("Best achieved: ", max_cartons/
# result = binsearch(cartons, containers)
#print(f"Maximum number of cartons packed : {result}")