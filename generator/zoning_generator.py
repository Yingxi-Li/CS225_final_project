import geopandas as gpd
import pandas as pd

from utils import map_centroid_to_zone, \
        generate_neighboring_pairs_and_dict, \
        filter_nonexisting_units, generate_distance_to_centroid, \
        filter_closer_than_cent
from partial_map import generate_partial_map

class SchoolZoning(object):
    def __init__(self, file, centroids=[670, 593, 497, 723]):

        # Load area data
        self.area_data = pd.read_csv("data/area_data.csv")
        # self.area_data = self.area_data["Tract" in generate_partial_map()]
        # print("Number of blocks: ", len(self.area_data))
        
        # There exists a few duplicated census blocks, we remove them
        self.area_data = self.area_data.drop_duplicates(subset='census_block')
        self.area_data['index'] = range(1, len(self.area_data) + 1)
        
        units = set(self.area_data['census_block'].to_list())
        
        # Dictionary with key as index and value as census block id (area)
        self.index_unit_map = dict(zip(self.area_data['index'], units))
        # The reverse of the above mapping
        self.unit_index_map = dict(zip(units, self.area_data['index'])) 
        self.unit_indices = self.area_data['index']
        
        # Number of students in units (area)
        # Dictionary with key as unit (area) and value as number of students in that unit
        self.studentsInArea = dict(zip(self.area_data['index'], self.area_data['number_of_students']))
        
        # Number of seats in units (area)
        # Dictionary with key as unit (area) and value as number of seats in that unit
        self.seatsInArea = dict(zip(self.area_data['index'], self.area_data['total_seat_capacity']))
        
        # self.schools is a dictionary of:
        # (keys: area index j), (values: number of schools in area index j) this value is usually 0 or 1
        # Example: self.schools[41] == number of schools in area index 41 (this value is usually 0 or 1)
        self.schoolsInArea = dict(zip(self.area_data['index'], self.area_data['number_of_schools']))
        
        # File to write in
        self.file = file
        
        # Centroids of zones in census ID
        self.Z = len(centroids)
        self.centroids = map_centroid_to_zone(centroids, units)
        
        # Neighbor data
        neighbor_pairs, neighbor_dict = generate_neighboring_pairs_and_dict()
        self.neighbor_pairs, self.neighbor_dict = filter_nonexisting_units(neighbor_pairs, neighbor_dict, units)
        
        # Number of schools
        self.SCH = self.area_data['number_of_schools'].sum()
        self.c_count = 1
        
        self.d = generate_distance_to_centroid(self.centroids, units)
        
    def add_objective(self):
        
        self.file.write("Minimize\n obj: ")
        self.file.write(" + ".join(f"b{self.unit_index_map[float(u)]}_{self.unit_index_map[float(v)]}" for u, v in self.neighbor_pairs))
        self.file.write("\nSubject To\n")
        
    def add_feasibility_constraints(self):
        # Each area is assigned to 1 zone
        for u in self.unit_indices:
            self.file.write(f" c{self.c_count}: " + " + ".join(f"x{u}_{z}" for z in range(self.Z)) + " = 1\n")
            self.c_count += 1
        
        # Compactness constraint
        print("Adding Compactness constraint")
        for u, v in self.neighbor_pairs:
            for z in range(self.Z):
                u_id = self.unit_index_map[u]
                v_id = self.unit_index_map[v]
                self.file.write(f" c{self.c_count}: x{u_id}_{z} - x{v_id}_{z} - b{u_id}_{v_id} <= 0\n")
                self.c_count += 1
                self.file.write(f" c{self.c_count}: x{u_id}_{z} - x{v_id}_{z} + b{u_id}_{v_id} >= 0\n")
                self.c_count += 1
        print("Compactness constraint added")
                
        # Contiguity cosntraint
        print("Adding Contiguity constraint")
        for u in self.unit_indices:
            for z in range(self.Z):
                try:
                    cent = self.centroids[z]
                except:
                    print("Error", z)
                    print(self.centroids)
                    1/0
                v_list = self.neighbor_dict[self.index_unit_map[u]] # List in census block id 
                v_list = filter_closer_than_cent(v_list, self.index_unit_map[u], cent, self.d)
                v_list = [self.unit_index_map[v] for v in v_list]
                
                self.file.write(f" c{self.c_count}: x{u}_{z} - " + " - ".join(f"x{v}_{z}" for v in v_list) + " <= 0 \n")
                # if v_list != []:
                #     print(f" c{self.c_count}: x{u}_{z} - " + " - ".join(f"x{v}_{z}" for v in v_list) + " <= 0 \n")
                self.c_count += 1
        print("Contiguity constraint added")
        
    
    def add_balancing_constraints(self):
        # Add seat balancing constraint
        for z in range(self.Z):
            self.file.write(
                f" c{self.c_count}: " + " + ".join(
                    f"{self.seatsInArea[u] - self.studentsInArea[u]} x{u}_{z}" for u in self.unit_indices if (self.seatsInArea[u] - self.studentsInArea[u]) != 0
                ) + " >= 0\n"
            )
            self.c_count += 1
            
        # Add number of school balancing constraint
        for z in range(self.Z):
            self.file.write(f" c{self.c_count}: - " + " - ".join(f"{str(self.schoolsInArea[u])} x{u}_{z}" for u in self.unit_indices if self.schoolsInArea[u] != 0) + f" <= {str(1 - self.SCH / self.Z)} \n")
            self.c_count += 1
            
            self.file.write(f" c{self.c_count}: - " + " - ".join(f"{str(self.schoolsInArea[u])} x{u}_{z}" for u in self.unit_indices if self.schoolsInArea[u] != 0) + f" >= {str(- 1 - self.SCH / self.Z)} \n")
            self.c_count += 1
    
    
    def add_variables_and_end(self):
        self.file.write("Binaries\n")
        for u in self.unit_indices:
            for z in range(self.Z):
                self.file.write(f" x{u}_{z}\n")
                    
        for u, v in self.neighbor_pairs:
            u_id, v_id = self.unit_index_map[u], self.unit_index_map[v]
            self.file.write(f" b{u_id}_{v_id}\n")
        
        self.file.write("End\n")
        
        
if __name__ == "__main__":
    
    lst_centroids = [[750, 830], [670, 593, 497, 723], 
                     [544, 569, 823], [664, 544, 750, 862], 
                     [664, 862, 722, 867], [544, 569, 823], [723, 456, 838, 497], 
                     [497, 456, 838, 507, 625, 830, 453], [722, 420, 575, 656, 603, 680, 723], 
                     [525, 823, 834, 801, 638, 490, 562, 872]]
    for i, cent in enumerate(lst_centroids):
        with open(f"lp_test_files/school/school_zoning_{i}.lp", "w") as f:
            school_zoning = SchoolZoning(f, centroids=cent)
            school_zoning.add_objective()
            school_zoning.add_feasibility_constraints()
            school_zoning.add_balancing_constraints()
            school_zoning.add_variables_and_end()
        print(f"File {i} written")
        