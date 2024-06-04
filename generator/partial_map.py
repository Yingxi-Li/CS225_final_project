import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt


CENSUS_SHAPEFILE_PATH = "data/shape_file/geo_export_d4e9e90c-ff77-4dc9-a766-6a1a7f7d9f9c.shp"
CENSUS_TRASLATOR_PATH = "data/block_blockgroup_tract.csv"

def get_census_df():
    census = gpd.read_file(CENSUS_SHAPEFILE_PATH)

    census['geoid10'] = census['geoid10'].fillna(value=0).astype('int64', copy=False)
    df = pd.read_csv(CENSUS_TRASLATOR_PATH)
    df['Block'] = df['Block'].fillna(value=0).astype('int64', copy=False)
    census = census.merge(df, how='left', left_on='geoid10', right_on='Block')
    return census

def generate_partial_map():
    census_original = get_census_df()

    census = census_original.copy()
    census = census.dissolve(by="Tract", as_index=False)

    # Filter tracts with latitude greater than a specific value
    latitude_threshold = 37.76  # Example latitude threshold

    census = census[census.centroid.y > latitude_threshold]
    # for i, y in enumerate(census.centroid.y):
    #     if y < latitude_threshold:
    #         census.drop(i, inplace=True)
    remaining_tracts = census.index.tolist()
    
    return remaining_tracts