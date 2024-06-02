import geopandas as gpd
import pandas as pd

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
        
        # Number of zones
        self.Z = 4
        
        # Centroids of zones
        self.centroids = map_centroid_to_zone([497, 456, 838, 507, 625, 830, 453], self.units)
        
    def add_variables_and_objective(self):
        
        self.file.write("Minimize\n obj: ")
        self.file.write(" + ".join(f"{str(distances[i][j])} x{i+1}{j+1}" for i in range(n) for j in range(n) if i != j))
        self.file.write("\nSubject To\n")
        
        # Each city must be entered exactly once
        for i in range(1, n+1):
            self.file.write(f" c{i}: " + " + ".join(f"x{i}{j}" for j in range(1, n+1) if i != j) + " = 1\n")
        
        # Each city must be left exactly once
        for j in range(1, n+1):
            self.file.write(f" c{n+j}: " + " + ".join(f"x{i}{j}" for i in range(1, n+1) if i != j) + " = 1\n")
        
        # MTZ constraints
        constraint_count = 2 * n
        for i in range(2, n+1):
            for j in range(2, n+1):
                if i != j:
                    file.write(f" u{i}u{j}: u{i} - u{j} + {n} x{i}{j} <= {n-1}\n")
                    constraint_count += 1

        file.write("Bounds\n")
        for i in range(1, n+1):
            for j in range(1, n+1):
                if i != j:
                    file.write(f" 0 <= x{i}{j} <= 1\n")
        
        file.write("Binaries\n")
        for i in range(1, n+1):
            for j in range(1, n+1):
                if i != j:
                    file.write(f" x{i}{j}\n")
                    
        file.write("General\n")
        for i in range(2, n+1):
            file.write(f" u{i}\n")
        
        file.write("End\n")
        
        
if __name__ == "__main__":
    sz = SchoolZoning(None)
    # with open("school_zoning.lp", "w") as file:
    #     sz = SchoolZoning(file)
    #     sz.add_variables_and_objective()


    