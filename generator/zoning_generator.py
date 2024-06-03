import geopandas as gpd
import pandas as pd

from utils import map_centroid_to_zone, generate_neighboring_pairs_and_dict, filter_nonexisting_units

class SchoolZoning(object):
    def __init__(self, file):

        # Load area data
        self.area_data = pd.read_csv("data/area_data.csv")
        self.area_data['index'] = range(1, len(self.area_data) + 1)
        
        # There exists a few duplicated census blocks, we remove them
        self.area_data.drop_duplicates(subset='census_block')
        
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
        self.schools = dict(zip(self.area_data['index'], self.area_data['number_of_schools']))
        
        # File to write in
        self.file = file
        
        # Centroids of zones in census ID
        centroid_schools = [670, 593, 497, 723]
        self.Z = len(centroid_schools)
        self.centroids = map_centroid_to_zone(centroid_schools, units)
        
        # Neighbor data
        neighbor_pairs, neighbor_dict = generate_neighboring_pairs_and_dict()
        self.neighbor_pairs, self.neighbor_dict = filter_nonexisting_units(neighbor_pairs, neighbor_dict, units)
        
        # Number of schools
        self.SCH = self.area_data['number_of_schools'].sum()
        
        
    def add_objective(self):
        
        self.file.write("Minimize\n obj: ")
        self.file.write(" + ".join(f"d{self.unit_index_map[float(u)]}_{self.unit_index_map[float(v)]}" for u, v in self.neighbor_pairs))
        self.file.write("\nSubject To\n")
        
    def add_feasibility_constraints(self):
        # Each area is assigned to 1 zone
        c_count = 1
        for u in self.unit_indices:
            self.file.write(f" c{c_count}: " + " + ".join(f"x{u}_{z}" for z in range(self.Z)) + " = 1\n")
            c_count += 1
        
        # Compactness constraint
        for u, v in self.neighbor_pairs:
            for z in range(self.Z):
                u_id = self.unit_index_map[u]
                v_id = self.unit_index_map[v]
                self.file.write(f" c{c_count}: x{u_id}_{z} - x{v_id}_{z} - b{u_id}_{v_id} <= 0\n")
                self.file.write(f" c{c_count}: x{u_id}_{z} - x{v_id}_{z} + b{u_id}_{v_id} >= 0\n")
                c_count += 1
                
        # Contiguity cosntraint
        # for u in self.unit_indices:
        #     for z in range(self.Z):
        #         v_list = [] # TODO: Get neighbors of u
        #         self.file.write(f" c{c_count}: x{u}_{z} <= " + " + ".join(f"x{v}_{z}" for v in v_list) + "\n")
        #         c_count += 1
        
    
    def add_balancing_constraints(self):
        # Add seat balancing constraint
        pass
    
        # Add number of school balancing constraint
        pass
    
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
    with open("lp_test_files/school_zoning.lp", "w") as f:
        school_zoning = SchoolZoning(f)
        school_zoning.add_objective()
        school_zoning.add_feasibility_constraints()
        # school_zoning.add_balancing_constraints()
        school_zoning.add_variables_and_end()
        