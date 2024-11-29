import csv

def cartons():
    file_path = './package.csv'
    cartons = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            v = [float(row[1]), float(row[2]), float(row[3])]
            v.sort()
            carton = {
                "id": row[0],
                "length": float(v[0]),
                "width": float(v[1]),
                "height": float(v[2]),
                "weight": float(row[4]),
                "priority": 1 if row[5] == "Priority" else 0,
                "cost": float(row[6]) if row[6] != '-' else 1e6
            }
            cartons.append(carton)
    cartons.sort(key=lambda x: x['id'])

    return cartons