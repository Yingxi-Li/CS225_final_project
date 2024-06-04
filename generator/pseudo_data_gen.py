import pandas as pd
import numpy as np
import random
from itertools import product
from utils import filter_closer_than_cent_pseudo

def generate_school_data(n, m, c_i, s_j):
    # Generate zone IDs
    zone_ids = np.arange(1, n**2 + 1)
    
    # Randomly select m zones to build schools
    selected_zones = random.sample(list(zone_ids), m)
    
    # Create data for the pandas DataFrame
    data = {
        'census_block': zone_ids,
        'number_of_schools': [1 if zone_id in selected_zones else 0 for zone_id in zone_ids],
        'total_seat_capacity': [c_i if zone_id in selected_zones else 0 for zone_id in zone_ids],
        'number_of_students': [random.randint(0, s_j) for _ in range(n**2)]
    }
    
    # Create the DataFrame
    df = pd.DataFrame(data)
    
    # Generate neighboring pairs
    neighboring_pairs = []
    for i in range(1, n**2+1):
        for j in range(1, n**2+1):
            zone_id = (i-1) * n + j
            neighbors = []
            if i > 1 and zone_id - n > 0:
                neighbors.append(zone_id - n)
            if i < n and zone_id + n <= n**2:
                neighbors.append(zone_id + n)
            if j > 1 and zone_id - 1 > 0:
                neighbors.append(zone_id - 1)
            if j < n and zone_id + 1 <= n**2:
                neighbors.append(zone_id + 1)
            neighboring_pairs.extend([(zone_id, neighbor) for neighbor in neighbors])
    
    # Create a dictionary with zone_id as keys and a list of neighbor zones as values
    neighbors_dict = {}
    for zone_id in zone_ids:
        neighbors_dict[zone_id] = set([neighbor[1] for neighbor in neighboring_pairs if neighbor[0] == zone_id])
    
    # Create a DataFrame for the distance between every zone pair
    distances = []
    for pair in product(zone_ids, repeat=2):
        if pair[0] != pair[1]:
            dist = abs((pair[0]-1) // n - (pair[1]-1) // n) + abs((pair[0]-1) % n - (pair[1]-1) % n)
            distances.append(pair + (dist,))
    
    distance_df = pd.DataFrame(distances, columns=['zone_id_1', 'zone_id_2', 'distance'])
    
    # Create a square DataFrame initialized with NaNs
    distance_matrix = pd.DataFrame(np.nan, index=zone_ids, columns=zone_ids)

    # Fill the matrix with distances
    for _, row in distance_df.iterrows():
        distance_matrix.at[row['zone_id_1'], row['zone_id_2']] = row['distance']
        distance_matrix.at[row['zone_id_2'], row['zone_id_1']] = row['distance']

    # Set diagonal to 0 (distance from a zone to itself)
    np.fill_diagonal(distance_matrix.values, 0)

    
    return df, neighboring_pairs, neighbors_dict, distance_matrix, selected_zones

class SchoolZoning(object):
    def __init__(self, file):
        
        n = 6  # Size of the grid map (n x n)
        m = 6  # Number of zones to build schools
        c_i = 30  # Capacity of each school
        s_j = 5  # Maximum number of students in each zone

        school_df, neighboring_pairs, neighbors_dict, distance_matrix, centroids = generate_school_data(n, m, c_i, s_j)

        # Load area data
        self.area_data = school_df
        # self.area_data = self.area_data["Tract" in generate_partial_map()]
        # print("Number of blocks: ", len(self.area_data))
        
        self.units = set(self.area_data['census_block'].to_list())
        
        # Number of students in units (area)
        # Dictionary with key as unit (area) and value as number of students in that unit
        self.studentsInArea = dict(zip(self.area_data['census_block'], self.area_data['number_of_students']))
        
        # Number of seats in units (area)
        # Dictionary with key as unit (area) and value as number of seats in that unit
        self.seatsInArea = dict(zip(self.area_data['census_block'], self.area_data['total_seat_capacity']))
        
        # self.schools is a dictionary of:
        # (keys: area index j), (values: number of schools in area index j) this value is usually 0 or 1
        # Example: self.schools[41] == number of schools in area index 41 (this value is usually 0 or 1)
        self.schoolsInArea = dict(zip(self.area_data['census_block'], self.area_data['number_of_schools']))
        
        # File to write in
        self.file = file
        
        # Centroids of zones in census ID
        self.Z = len(centroids)
        self.centroids = centroids
        
        # Neighbor data
        neighbor_pairs, neighbor_dict = set(neighboring_pairs), neighbors_dict
        self.neighbor_pairs, self.neighbor_dict = neighbor_pairs, neighbor_dict
        
        # Number of schools
        self.SCH = self.area_data['number_of_schools'].sum()
        self.c_count = 1
        
        self.d = distance_matrix
        
    def add_objective(self):
        
        self.file.write("Minimize\n obj: ")
        self.file.write(" + ".join(f"b{u}_{v}" for u, v in self.neighbor_pairs))
        self.file.write("\nSubject To\n")
        
    def add_feasibility_constraints(self):
        # Each area is assigned to 1 zone
        for u in self.units:
            self.file.write(f" c{self.c_count}: " + " + ".join(f"x{u}_{z}" for z in range(self.Z)) + " = 1\n")
            self.c_count += 1
        
        # Compactness constraint
        print("Adding Compactness constraint")
        for u, v in self.neighbor_pairs:
            for z in range(self.Z):
                self.file.write(f" c{self.c_count}: x{u}_{z} - x{v}_{z} - b{u}_{v} <= 0\n")
                self.c_count += 1
                self.file.write(f" c{self.c_count}: x{u}_{z} - x{v}_{z} + b{u}_{v} >= 0\n")
                self.c_count += 1
        print("Compactness constraint added")
                
        # Contiguity cosntraint
        print("Adding Contiguity constraint")
        for u in self.units:
            for z in range(self.Z):
                cent = self.centroids[z]
                
                v_list = self.neighbor_dict[u] # List in census block id 
                v_list = filter_closer_than_cent_pseudo(v_list, u, cent, self.d) 
                
                if v_list != []:
                    self.file.write(f" c{self.c_count}: x{u}_{z} - " + " - ".join(f"x{v}_{z}" for v in v_list) + " <= 0 \n")
                self.c_count += 1
        print("Contiguity constraint added")
        
    
    def add_balancing_constraints(self):
        # Add seat balancing constraint
        for z in range(self.Z):
            self.file.write(
                f" c{self.c_count}: " + " + ".join(
                    f"{self.seatsInArea[u] - self.studentsInArea[u]} x{u}_{z}" for u in self.units if (self.seatsInArea[u] - self.studentsInArea[u]) != 0
                ) + " >= 0\n"
            )
            self.c_count += 1
            
        # Add number of school balancing constraint
        for z in range(self.Z):
            self.file.write(f" c{self.c_count}: - " + " - ".join(f"{str(self.schoolsInArea[u])} x{u}_{z}" for u in self.units if self.schoolsInArea[u] != 0) + f" <= {str(1 - self.SCH / self.Z)} \n")
            self.c_count += 1
            
            self.file.write(f" c{self.c_count}: - " + " - ".join(f"{str(self.schoolsInArea[u])} x{u}_{z}" for u in self.units if self.schoolsInArea[u] != 0) + f" >= {str(- 1 - self.SCH / self.Z)} \n")
            self.c_count += 1
    
    
    def add_variables_and_end(self):
        self.file.write("Binaries\n")
        for u in self.units:
            for z in range(self.Z):
                self.file.write(f" x{u}_{z}\n")
                    
        for u, v in self.neighbor_pairs:
            self.file.write(f" b{u}_{v}\n")
        
        self.file.write("End\n")
        

if __name__ == "__main__":
    for i in range(10):
        with open(f"lp_test_files/zone_pseudo_{i}.lp", "w") as f:
            school_zoning = SchoolZoning(f)
            school_zoning.add_objective()
            school_zoning.add_feasibility_constraints()
            school_zoning.add_balancing_constraints()
            school_zoning.add_variables_and_end()