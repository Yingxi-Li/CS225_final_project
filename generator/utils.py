import pandas as pd
import math
import numpy as np

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

def not_nan_or_none(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def generate_neighboring_pairs_and_dict():
    """
    Return a set of neighboring pairs in the form of tuples (id1, id2)

    Returns:
        _type_: set of tuples
    """
    neighbor_data = pd.read_csv("data/block_adjacency_matrix.csv")
    
    # Initialize an empty list to store the neighboring pairs
    neighboring_pairs = []
    neighbor_dict = {}

    # Iterate over each row in the DataFrame
    for row in neighbor_data.itertuples(index=False):
        # The first element is the neighbor for all other elements in the row
        main_id = row[0]
        neighbors = row[1:]
        # Remove NaN values using filter
        cleaned_list = list(filter(not_nan_or_none, neighbors))
        
        for neighbor_id in cleaned_list:
            neighboring_pairs.append((main_id, neighbor_id))
        
        values = list(cleaned_list)
        neighbor_dict[main_id] = values
            
    return set(neighboring_pairs), neighbor_dict

def filter_nonexisting_units(pairs, dict, units):
    new_pairs = []
    for u, v in pairs:
        if u in units and v in units:
            new_pairs.append((u, v))
        if u not in units and u in dict:
            del dict[u]
            if v in dict:
                dict[v].remove(u)
        if v not in units and v in dict:
            del dict[v]
            if u in dict:
                dict[u].remove(v)

    return new_pairs, dict


def generate_distance_to_centroid(centroids, units):
        
    distances = pd.read_csv("data/distances_b2b.csv")
    distances.set_index('Block', inplace=True)
    centroids = [int(centroid) for centroid in centroids]
    
    rows = distances.index.tolist() # Ints
    cols = list(distances.columns) # Strings
    
    cent_dist = distances.loc[centroids]
    return cent_dist


def filter_closer_than_cent(v_list, u, cent, d):
    filtered_list = []
    for v in v_list:
        try:
            if d.loc[int(cent), str(int(v))] <= d.loc[int(cent), str(int(u))]:
                filtered_list.append(v)
            else:
                continue
        except:
            # print("key error", v, u)
            pass

    return filtered_list

def filter_closer_than_cent_pseudo(v_list, u, cent, d_pseudo):
    
    filtered_list = []
    for v in v_list:
        if d_pseudo.loc[cent, v] <= d_pseudo.loc[cent, u]:
            filtered_list.append(v)

    return filtered_list