import geopandas as gpd

def get_data():
    tyne_oa = gpd.read_file("data/tyne_oa")
    
    # Location of points of interest (in this case output area population
    # weighted centroids)
    poi_x = tyne_oa["X"].values
    poi_y = tyne_oa["Y"].values
    
    # Weight for each point of interest (in this case population estimate for 
    # each output area)
    poi_weight = tyne_oa["Population"].values
    
    return {"poi_x": poi_x,
            "poi_y": poi_y,
            "poi_weight": poi_weight}
    
    
    
