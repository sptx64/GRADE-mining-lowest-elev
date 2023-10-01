import pandas as pd
import numpy as np
from io import StringIO
from scipy.interpolate import LinearNDInterpolator
import geopandas as gpd
import os

def clean_str(string_file) :
    with open(f"input/{string_file}") as f :
        string = f.read().splitlines()
        output_lines = []
        for line in string[2:]:
            fields = line.split(',')
            output_line = ','.join(fields[:4])  # Extract the first four fields
            output_lines.append(output_line)

    output = '\n'.join(output_lines)
    output = pd.read_csv(StringIO(output), header=None)
    return output


def to_surpac_str(df, z="min_topo") :
    first_row = "topo_def,11-Sep-23,blablabla.str,blablabla.ssi\n"
    second_row = "0,           0.000,           0.000,           0.000,           0.000,           0.000,           0.000\n"
    x, y, z = df["x"].to_numpy(), df["y"].to_numpy(), df[z].to_numpy()
    string_no = 1
    
    strxyz = []
    for i in range(len(x)) :
        strxyz.append(f"{string_no}, {y[i]}, {x[i]}, {z[i]},\n")
    print(f"...ecriture de {len(strxyz)} lignes...")
    with open('output/output_topo_def.str', 'w') as f:
        f.write(first_row)
        f.write(second_row)
        f.writelines(strxyz)
        f.write("0, 0.000, 0.000, 0.000,\n")
        f.write("0, 0.000, 0.000, 0.000, END")

        
def load_boundary(file_path="input boundary/bd_topo_def.gpkg") :
    return gpd.read_file(file_path)



def bd_clip_grid(bd, grid_df) :
    #get bd enveloppe
    print("Début du clipping")
    bd_emprise = bd.total_bounds #unary_union.envelope
    grid_df = grid_df[(grid_df.x >= bd_emprise[0]) & (grid_df.x <= bd_emprise[2]) & (grid_df.y >= bd_emprise[1]) & (grid_df.y <= bd_emprise[3])]
    print(f"Cutté à l'emprise. Longueur de la grille avant clipping : {len(grid_df)}")
    xmin, xmax, ymin, ymax = grid_df.x.min(), grid_df.x.max(), grid_df.y.min(), grid_df.y.max()
    band = 1000
    
    x = xmin
    while x<=xmax :
        y=ymin
        while y<=ymax :
            grid_chunk = grid_df[(grid_df.x >= x) & (grid_df.x < x+band) & (grid_df.y >= y) & (grid_df.y < y+band)]
            if (x == xmin) & (y == ymin) :
                grid_gdf = gpd.GeoDataFrame(grid_chunk, geometry=gpd.points_from_xy(grid_chunk.x, grid_chunk.y), crs='epsg:3163')
                grid_gdf = gpd.clip(grid_gdf, bd)
            
            else :
                grid_chunk_gdf = gpd.GeoDataFrame(grid_chunk, geometry=gpd.points_from_xy(grid_chunk.x, grid_chunk.y), crs='epsg:3163')
                grid_chunk_gdf = gpd.clip(grid_chunk_gdf, bd)
                grid_gdf = pd.concat([grid_gdf, grid_chunk_gdf])
            y+=band
        x+=band
        
    return grid_gdf.drop(columns=["geometry"])


def read_convert_line_shp(file_path) :
    lines = gpd.read_file("input/" + file_path)
    lines.crs="epsg:3163"
    return lines["geometry"].get_coordinates(include_z=True, ignore_index=True)

    
def main_process(res, list_topo_str_up, list_topo_shp_up) :
    print("0% - Initialisation")

    #list_topo_up = list_topo_up[list_topo_up != np.nan]
    #list_topo = np.zeros_like(list_topo_up)
    coord_xmin, coord_ymin, coord_xmax, coord_ymax, list_topo = [],[],[],[],[]

    print("5% - Nettoyage des .str en cours")

    #read topos
    value=0
    for uploaded_file in list_topo_str_up:
        topo = clean_str(uploaded_file)
        f"... topo .str {value} cleaned", len(topo)
        topo = topo.rename(columns={1:"y", 2:"x", 3:"z"})
        topo = topo[topo["x"] > 0]
        topo["x"], topo["y"], topo["z"] = topo["x"].round(2), topo["y"].round(2), topo["z"].round(2)

        list_topo.append(topo)
        xmin, xmax = topo["x"].min(), topo["x"].max()
        ymin, ymax = topo["y"].min(), topo["y"].max()
        coord_xmin.append(xmin)
        coord_xmax.append(xmax)
        coord_ymin.append(ymin)
        coord_ymax.append(ymax)
        value+=1

    for uploaded_file in list_topo_shp_up:
        topo = read_convert_line_shp(uploaded_file)
        
        f"... topo .shp {value} cleaned", len(topo)
        topo = topo[topo["x"] > 0]
        topo["x"], topo["y"], topo["z"] = topo["x"].round(2), topo["y"].round(2), topo["z"].round(2)

        list_topo.append(topo)
        xmin, xmax = topo["x"].min(), topo["x"].max()
        ymin, ymax = topo["y"].min(), topo["y"].max()
        coord_xmin.append(xmin)
        coord_xmax.append(xmax)
        coord_ymin.append(ymin)
        coord_ymax.append(ymax)
        value+=1

    print("10% - Création de la grille en fonction des bbox observées des topos")

    #create grids
    grid_x_min, grid_x_max, grid_y_min, grid_y_max = min(coord_xmin), max(coord_xmax), min(coord_ymin), max(coord_ymax)
    print("11% - emprise totale des topographies calculée :")
    print(f"xmin:{min(coord_xmin)}, xmax: {max(coord_xmax)}, ymin: {min(coord_ymin)}, ymax: {max(coord_ymax)}")
    
    print("12 % - Création de la grille")

    import numpy as np


    grid_coord=[]
    x=grid_x_min
    while x<grid_x_max :
        y=grid_y_min
        while y<grid_y_max :
            grid_coord.append([x,y])
            y+=res
        x+=res

    print("20% - Création de la DataFrame de la grille...")

    grid_df = pd.DataFrame(grid_coord, columns=["x","y"])
    
    print("25% - Vérification et application de la limite de la zone d'étude...")
    
    file_path="input boundary/bd_topo_def.gpkg"
    
    if os.path.exists(file_path) :
        print("26% - Ok la limite a été trouvée...")
        bd = load_boundary(file_path)
        print(f"27% - avant clipping {len(grid_df)}")
        grid_df = bd_clip_grid(bd, grid_df)
        grid_coord=grid_df[["x","y"]].values
        print(f"27% - après clipping {len(grid_df)}")
    else :
        print("26% - boundary does not exist...")
    
    
    column_topo_name = [f"topo{i}" for i in range(len(list_topo))]

    print("30% - Lecture des topos et interpolation...")
    z_results = []
    
    for topo, column_name in zip(list_topo, column_topo_name) :
        interp = LinearNDInterpolator(topo[["x", "y"]], topo["z"])
        print(f"{column_name} linearNDinterpolator solved")
        z_results.append(interp(grid_coord))
        print(f"{column_name} interpolation appliquée à la grille...")


    print("85% - Récupération des z et soustraction des colonnes...")
    
    z_min = np.nanmin(z_results, axis=0)
    grid_df["min_topo"] = z_min
    
    print(f"len grid_df = {len(grid_df)} before drop")
    grid_df.dropna(subset=["min_topo"], inplace=True)
    print(f"len grid_df = {len(grid_df)} after drop")
    
    print("90% - Conversion Surpac...")

    to_surpac_str(grid_df, z="min_topo")

    print("100% - Terminé")
