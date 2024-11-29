import csv

def cartons():
    file_path = './priority_packages.csv'
    cartons = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            carton = {
                "id": row[0],
                "length": float(row[1]),
                "width": float(row[2]),
                "height": float(row[3]),
                "weight": float(row[4]),
                "priority": 1 if row[5] == "Priority" else 0,
                "cost": float(row[6]) if row[6] != '-' else 1e10
            }
            cartons.append(carton)
    return cartons
