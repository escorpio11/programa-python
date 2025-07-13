from etabs_interface import *
import pandas as pd

def create_grid_system(sapmodel, story_heights, x_coordinates, y_coordinates):
    number_of_stories = len(story_heights)
    typical_story_height = story_heights[1]
    bottom_story_height = story_heights[0]
    number_of_lines_x = len(x_coordinates)
    number_of_lines_y = len(y_coordinates)
    spacing_x = x_coordinates[1]
    spacing_y = y_coordinates[1]

    ret = sapmodel.InitializeNewModel(6)
    if ret == 0:
        print("Function InitializeNewModel was successful")
    else:
        print("Error running function InitializeNewModel")

    ret = sapmodel.File.NewGridOnly(number_of_stories, typical_story_height, bottom_story_height,
                                    number_of_lines_x, number_of_lines_y, spacing_x, spacing_y)
    if ret == 0:
        print("Function NewGridOnly was successful")
    else:
        print("Error running function NewGridOnly")

    grid_points = [[(x, y) for y in y_coordinates] for x in x_coordinates]

    # The output nested list has dimensions: len(x_coordinates) x len(y_coordinates)
    return grid_points

def draw_slab(sapmodel, point_list, start_x_index, end_x_index, start_y_index, end_y_index, offset, z_coordinate, prop_name, balcony_axis=None, width=None, depth=None, balcony_offset=None):
    # Extract corner points of the slab
    x1, y1 = point_list[start_x_index][start_y_index] #primer tupla de la primera lista de listas
    x2, y2 = point_list[end_x_index][start_y_index] # Primera tupla de la ultima lista de listas
    x3, y3 = point_list[end_x_index][end_y_index] # Ultima tupla de la ultima lista de listas
    x4, y4 = point_list[start_x_index][end_y_index] #ultima tupla de la primera lista de listas

    # Apply the offset
    x1 -= offset #igual a 0,3 definido en los parametros iniciales
    y1 -= offset
    x2 += offset
    y2 -= offset
    x3 += offset
    y3 += offset
    x4 -= offset
    y4 += offset

    # Create coordinates arrays
    x_coordinates = [x1, x2, x3, x4]
    y_coordinates = [y1, y2, y3, y4]
    z_coordinates = [z_coordinate] * 4

    # Add balconies if specified
    if balcony_axis is not None and width is not None and depth is not None and balcony_offset is not None:
        x_coordinates, y_coordinates, z_coordinates = add_balconies(point_list, x_coordinates, y_coordinates, z_coordinates, balcony_axis, width, depth, balcony_offset)

    # Define the slab name
    slab_name = ""

    # Add the slab to the ETABS model
    num_points = len(x_coordinates)
    _, _, _, slab_name, ret = sapmodel.AreaObj.AddByCoord(num_points, x_coordinates, y_coordinates, z_coordinates, slab_name, prop_name)
    if ret == 0:
        print(f"Function AddByCoord was successful for slab {slab_name}")
    else:
        print(f"Error running function AddByCoord for slab {slab_name}")

    return slab_name

def define_wall(sapmodel, start_axis, end_axis, top_z, bottom_z, section_prop):
    # Determine if the wall is vertical or horizontal
    is_vertical = start_axis[0] == end_axis[0]

    # Set the corner points of the wall
    x_coordinates = []
    y_coordinates = []
    z_coordinates = [bottom_z, bottom_z, top_z, top_z]

    if is_vertical:
        x_coordinates = [start_axis[0], start_axis[0], end_axis[0], end_axis[0]]
        y_coordinates = [start_axis[1], end_axis[1], end_axis[1], start_axis[1]]
    else:
        x_coordinates = [start_axis[0], end_axis[0], end_axis[0], start_axis[0]]
        y_coordinates = [start_axis[1], start_axis[1], end_axis[1], end_axis[1]]

    # Add the wall in ETABS
    wall_name = ""
    _, _, _, wall_name, ret = sapmodel.AreaObj.AddByCoord(4, x_coordinates, y_coordinates, z_coordinates, wall_name, section_prop)

    # Check if the API call was successful
    if ret == 0:
        print(f"Wall '{wall_name}' was successfully added.")
    else:
        print(f"Error adding wall '{wall_name}'.")

    return wall_name

def define_column(sapmodel, grid_points, horizontal_index, vertical_index, bottom_z, top_z, section_prop):
    # Extract coordinates of the grid point
    x, y = grid_points[horizontal_index][vertical_index]

    # Add a column using the ETABS API
    column_name, ret = sapmodel.FrameObj.AddByCoord(x, y, bottom_z, x, y, top_z, "", section_prop)

    # Check if the API call was successful
    if ret == 0:
        print(f"Column '{column_name}' added successfully.")
    else:
        print(f"Failed to add column at grid point ({horizontal_index}, {vertical_index}).")
    
    return column_name



def draw_opening(sapmodel, point_list, start_x_index, end_x_index, start_y_index, end_y_index, z_coordinate):
    # Call draw_slab with an offset value of zero and a property name of "Default"
    opening_name = draw_slab(sapmodel, point_list, start_x_index, end_x_index, start_y_index, end_y_index, 0, z_coordinate, "Default")

    # Set the new area object as an opening
    ret = sapmodel.AreaObj.SetOpening(opening_name, True)

    if ret == 0:
        print(f"Opening '{opening_name}' created successfully.")
    else:
        print(f"Error creating opening '{opening_name}'.")

    return opening_name

def define_beam(sapmodel, grid_points, start_i, start_j, end_i, end_j, z, section_prop):
    x1, y1 = grid_points[start_i][start_j]
    x2, y2 = grid_points[end_i][end_j]

    if (x1 == x2 and y1 == y2):
        print(f"Skipped beam: identical start and end at ({x1}, {y1}, {z})")
        return None

    frame_name, ret = sapmodel.FrameObj.AddByCoord(x1, y1, z, x2, y2, z, "", section_prop)

    if ret == 0:
        print(f"Beam '{frame_name}' added from ({x1},{y1},{z}) to ({x2},{y2},{z})")
    else:
        print(f"Failed to add beam: ret={ret}, section='{section_prop}', coords=({x1},{y1},{z}) to ({x2},{y2},{z})")

    return frame_name





# This function modifies the coordinates lists to add balconies along the slab edges.
# Each balcony is defined through four additional points that are calculated through the axis index, balcony widht and balcony height.
# The parameter balcony_axis is a nested list in which the first list contains the axis indexes of the balconies along the x axis and the
# secon list contains the axis indexes of the balconies along the y axis
def add_balconies(grid_points, x_coordinates, y_coordinates, z_coordinates, balcony_axis, width, depth, offset):
    new_x_coordinates = list(x_coordinates)
    new_y_coordinates = list(y_coordinates)
    for i in range(len(balcony_axis[0])):
        balcony_center_x = grid_points[balcony_axis[0][i]][0][0]+offset
        balcony_center_y_bottom = y_coordinates[0]
        balcony_center_y_top = y_coordinates[2]
        balcony_x = [balcony_center_x - width/2, balcony_center_x - width/2, balcony_center_x + width/2, balcony_center_x + width/2]
        balcony_y_bottom = [balcony_center_y_bottom,balcony_center_y_bottom-depth,balcony_center_y_bottom-depth,balcony_center_y_bottom]
        balcony_y_top = [balcony_center_y_top,balcony_center_y_top+depth,balcony_center_y_top+depth,balcony_center_y_top]
        new_x_coordinates[len(new_x_coordinates)-3-4*i:len(new_x_coordinates)-3-4*i]=balcony_x
        new_y_coordinates[len(new_y_coordinates)-3-4*i:len(new_y_coordinates)-3-4*i]=balcony_y_bottom
        new_x_coordinates[len(new_x_coordinates)-1-i*4:len(new_x_coordinates)-1 - i*4]=balcony_x[::-1]
        new_y_coordinates[len(new_y_coordinates)-1- i*4:len(new_y_coordinates)-1- i*4]=balcony_y_top
    for i in range(len(balcony_axis[1])):
        balcony_center_y = grid_points[0][balcony_axis[1][i]][1]+offset
        balcony_center_x_right = x_coordinates[1]
        balcony_center_x_left = x_coordinates[3]
        balcony_y = [balcony_center_y - width/2, balcony_center_y - width/2, balcony_center_y + width/2, balcony_center_y + width/2]
        balcony_x_right = [balcony_center_x_right,balcony_center_x_right+depth,balcony_center_x_right+depth,balcony_center_x_right]
        balcony_x_left = [balcony_center_x_left,balcony_center_x_left-depth,balcony_center_x_left-depth,balcony_center_x_left]
        new_x_coordinates[4*len(balcony_axis[0])+2+4*i:4*len(balcony_axis[0])+2]=balcony_x_right
        new_y_coordinates[4*len(balcony_axis[0])+2+4*i:4*len(balcony_axis[0])+2]=balcony_y
        new_x_coordinates[len(new_x_coordinates) - i*4:len(new_x_coordinates)-1 - i*4]=balcony_x_left
        new_y_coordinates[len(new_y_coordinates) - i*4:len(new_y_coordinates)-1 - i*4]=balcony_y[::-1]
    return new_x_coordinates, new_y_coordinates, [z_coordinates[0]] * len(new_x_coordinates)




def get_frame_loads(sapmodel, frame_numbers):
    """
    Extract loads applied to specific frame elements in ETABS
    
    Args:
        sapmodel: ETABS model object
        frame_numbers: List of frame numbers to extract (1-455)
    
    Returns:
        DataFrame containing all loads for specified frames
    """
    # Setup dataframe to store results
    columns = [
        'Frame', 'LoadType', 'LoadName', 'LoadPattern', 'Direction',
        'Distance', 'Value', 'CSys', 'Angle', 'LoadCase'
    ]
    results = []
    
    # Get all load cases first
    ret, load_cases = sapmodel.LoadCases.GetNameList()
    
    for frame_num in frame_numbers:
        frame_name = f"Frame{frame_num}"  # Adjust naming convention if needed
        
        for case in load_cases:
            # Get load case type
            ret, case_type = sapmodel.LoadCases.GetTypeOAPI(case)
            
            if case_type == 1:  # Linear static load case
                # Get point loads
                ret, number_items, load_patterns, directions, distances, values = \
                    sapmodel.FrameObj.GetLoadPoint(frame_name, case)
                
                if ret == 0 and number_items > 0:
                    for i in range(number_items):
                        results.append([
                            frame_name,
                            'Point',
                            f'PointLoad{i+1}',
                            load_patterns[i],
                            directions[i],
                            distances[i],
                            values[i],
                            'Global',
                            0,
                            case
                        ])
                
                # Get distributed loads
                ret, number_items, load_patterns, directions, dist1, dist2, val1, val2 = \
                    sapmodel.FrameObj.GetLoadDistributed(frame_name, case)
                
                if ret == 0 and number_items > 0:
                    for i in range(number_items):
                        results.append([
                            frame_name,
                            'Distributed',
                            f'DistLoad{i+1}',
                            load_patterns[i],
                            directions[i],
                            f"{dist1[i]}-{dist2[i]}",
                            f"{val1[i]}-{val2[i]}",
                            'Global',
                            0,
                            case
                        ])
            
            elif case_type == 6:  # Time history load case
                # Get time history loads using GetLoads function
                ret, num_loads, load_types, load_names, funcs, sfs, tfs, ats, csys, angs = \
                    sapmodel.LoadCases.DirectHistoryLinear.GetLoads(case)
                
                if ret == 0 and num_loads > 0:
                    for i in range(num_loads):
                        results.append([
                            frame_name,
                            load_types[i],
                            load_names[i],
                            funcs[i],
                            '',
                            '',
                            sfs[i],
                            csys[i] if csys else 'Global',
                            angs[i] if angs else 0,
                            case
                        ])
    
    return pd.DataFrame(results, columns=columns)

