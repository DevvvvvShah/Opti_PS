import csv

def containers():
    file_path = './ULD.csv'
    containers = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            container = {
                "id": row[0],
                "length": float(row[1]),
                "width": float(row[2]),
                "height": float(row[3]),
                "weight": float(row[4])
            }
            containers.append(container)
    containers.sort(key=lambda x: x['id'])
    return containers

def containers_specific(container_id):
    file_path = './ULD.csv'
    containers = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            container = {
                "id": row[0],
                "length": float(row[1]),
                "width": float(row[2]),
                "height": float(row[3]),
                "weight": float(row[4])
            }
            if container['id'] != container_id:
                continue
            containers.append(container)
    containers.sort(key=lambda x: x['id'])
    return containers
def containers_specific_multiple(container_ids):
    file_path = './ULD.csv'
    containers = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            container = {
                "id": row[0],
                "length": float(row[1]),
                "width": float(row[2]),
                "height": float(row[3]),
                "weight": float(row[4])
            }
            if container['id'] not in container_ids:
                continue
            containers.append(container)
    containers.sort(key=lambda x: x['id'])
    return containers

