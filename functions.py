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
    if os.path.exists(file_path) :
        return gpd.read_file(file_path)
    else :
        print("ATTENTION : Boundary non trouvée dans input_boundary, vérifier le nom du gpkg.")

              
              
def create_grid_from_bd(res, epsg=3163) :
    #import de la bd
    bd_file = load_boundary()
    bd_file.crs = f"epsg:{epsg}"
    
    #extraction des sommets
    bd_file["geometry_str"] = bd_file["geometry"].astype(str).str.replace("POLYGON ((", "").str.replace("))", "")
    geometry_str = bd_file["geometry_str"].values
    x_polygon = []
    y_polygon = []
    for i in range(len(geometry_str)) :
        row = geometry_str[i].split(", ")
        for coords in row :
            coords = coords.split(" ")
            x_polygon.append(float(coords[0]))
            y_polygon.append(float(coords[1]))
            
    #calcul des min et max
    xmin,xmax = min(x_polygon), max(x_polygon)
    ymin,ymax = min(y_polygon), max(y_polygon)
    
    #creation de la grille
    grid_coord=[]
    x=xmin
    while x<xmax :
        y=ymin
        while y<ymax :
            grid_coord.append([x,y])
            y+=res
        x+=res
    
    #conversion dataframe
    grid_df = pd.DataFrame(grid_coord, columns=["x","y"])
    
    #clipper la grille avec une boucle pour limiter la taille du gdf
    band = 1000
    x = xmin
    while x<=xmax :
        y=ymin
        while y<=ymax :
            grid_chunk = grid_df[(grid_df.x >= x) & (grid_df.x < x+band) & (grid_df.y >= y) & (grid_df.y < y+band)]
            if (x == xmin) & (y == ymin) :
                grid_gdf = gpd.GeoDataFrame(grid_chunk, geometry=gpd.points_from_xy(grid_chunk.x, grid_chunk.y), crs='epsg:3163')
                grid_gdf = gpd.clip(grid_gdf, bd_file)

            else :
                grid_chunk_gdf = gpd.GeoDataFrame(grid_chunk, geometry=gpd.points_from_xy(grid_chunk.x, grid_chunk.y), crs='epsg:3163')
                grid_chunk_gdf = gpd.clip(grid_chunk_gdf, bd_file)
                grid_gdf = pd.concat([grid_gdf, grid_chunk_gdf])
            y+=band
        x+=band
    
    return grid_gdf.drop(columns=["geometry"])



def read_convert_line_shp(file_path) :
    lines = gpd.read_file("input/" + file_path)
    lines.crs="epsg:3163"
    return lines["geometry"].get_coordinates(include_z=True, ignore_index=True)



def main_process(res, list_topo_str_up, list_topo_shp_up, list_topo_dxf_up) :
    print("0% - Initialisation")

    #list_topo_up = list_topo_up[list_topo_up != np.nan]
    #list_topo = np.zeros_like(list_topo_up)
    list_topo = []
    
    print("5% - import de la limite polygone à partir de input boundary/bd_topo_def.gpkg")
    grid_df = create_grid_from_bd(res, epsg=3163)
    grid_coord=grid_df[["x","y"]].values


    print("15% - Nettoyage des .str, .dxf, .shp en cours")

    #read topos
    value=0
    for type_list, list_values in zip(["str", "dxf", "shp"], [list_topo_str_up, list_topo_dxf_up, list_topo_shp_up]) :
        for uploaded_file in list_values :
            if type_list=="str" :
                topo = clean_str(uploaded_file)
                topo = topo.rename(columns={1:"y", 2:"x", 3:"z"})

            else :
                topo = read_convert_line_shp(uploaded_file)
              
            print(f"... topo .{type_list} {value} cleaned"), print(f"{len(topo)} points trouvés")

            topo = topo[topo["x"] > 0]
            topo["x"], topo["y"], topo["z"] = topo["x"].round(2), topo["y"].round(2), topo["z"].round(2)
            
            interp = LinearNDInterpolator(topo[["x", "y"]], topo["z"])
            print(f"topo {value} linearNDinterpolator solved")
            
            if value == 0 :
                z_min = interp(grid_coord)
                print(f"topo {value} interpolation appliquée à la grille...")
            else :
                z_results = [z_min, interp(grid_coord)]
                z_min = np.nanmin(z_results, axis=0)

            value+=1
       
    print("85% - Merge des resultats defruites dans la dataframe")
    grid_df["min_topo"] = z_min

    print(f"len grid_df = {len(grid_df)} before drop")
    grid_df.dropna(subset=["min_topo"], inplace=True)
    
    print(f"len grid_df = {len(grid_df)} after drop")
    print("90% - Conversion Surpac...")

    to_surpac_str(grid_df, z="min_topo")

    print("100% - Terminé")
