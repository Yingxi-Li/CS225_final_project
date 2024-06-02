import pandas as pd

def map_centroid_to_zone(centroids, units):
    """
    Map each centroid to a zone number.
    """

    school_data = pd.read_csv("data/schools_rehauled_2324.csv")
    
    # Create a dictionary to map school_id to block for quick lookup
    school_id_to_block = school_data.set_index('school_id')['Block'].to_dict()
    
    # Create a list of blocks for the given school_ids
    blocks = [float(school_id_to_block[school_id]) for school_id in centroids if school_id in school_id_to_block]
    
    for block in blocks:
        assert block in units
    
    return blocks