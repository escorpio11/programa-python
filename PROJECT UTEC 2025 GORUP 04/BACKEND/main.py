from etabs_interface import *
from functions_parameter_etabs import *
import pandas as pd
balcony_axis=[]
cores=[]
openings=[]
def build_etabs_model_with_beams(
            story_heights,
            x_coordinates,
            y_coordinates,
            slab_prop_name="Slab1",
            slab_offset=0.3,
            balcony_axis=balcony_axis,
            balcony_width=4,
            balcony_depth=2,
            balcony_offset=4.0,
            wall_section="Wall1",
            column_section="ConcCol",
            beam_section="ConcBm",
            cores=cores,
            openings=openings):
            """
            Full model creation including beams at each level.
            """



            balcony_axis = balcony_axis if balcony_axis else [[1, 3, 5, 7], [1, 3]]
            cores = cores if cores else [
                {"horizontal": (2, 3), "vertical": (1, 3)},
                {"horizontal": (2, 3), "vertical": (6, 8)}
            ]
            openings = openings if openings else [(4, 5, 1, 3)]

            try:
                etabs_object, sapmodel = connect_to_etabs()

                if not etabs_object or not sapmodel:
                    print("Failed to connect to ETABS")
                    return False
                
                grid_points = create_grid_system(sapmodel, story_heights, x_coordinates, y_coordinates)
                print(grid_points)
                if not grid_points:
                    return False

                for z, story_height in enumerate(story_heights):  #z y story_height varia entre 0 hasta el numero de elementos de la lista story_heights. 
                    z_coordinate = sum(story_heights[:z + 1])
                    draw_slab(
                        sapmodel, grid_points, 0, len(x_coordinates) - 1, 0, len(y_coordinates) - 1,
                        slab_offset, z_coordinate, slab_prop_name, balcony_axis, balcony_width,
                        balcony_depth, balcony_offset
                    )

                    for opening in openings:
                        draw_opening(sapmodel, grid_points, *opening, z_coordinate)

                    bottom_z = sum(story_heights[:z])
                    top_z = bottom_z + story_height

                    for core in cores:
                        h_start, h_end = core["horizontal"]  #asigna a h_start y h_end el valor de la clave "horizontal" (una tupla) para cada diccionario en la lista de diccionarios. 
                        v_start, v_end = core["vertical"]

                        define_wall(sapmodel, (x_coordinates[v_start], y_coordinates[h_start]), (x_coordinates[v_end], y_coordinates[h_start]), top_z, bottom_z, wall_section) #define las coordenadas donde se crearan los muros
                        define_wall(sapmodel, (x_coordinates[v_end], y_coordinates[h_start]), (x_coordinates[v_end], y_coordinates[h_end]), top_z, bottom_z, wall_section)
                        define_wall(sapmodel, (x_coordinates[v_end], y_coordinates[h_end]), (x_coordinates[v_start], y_coordinates[h_end]), top_z, bottom_z, wall_section)
                        define_wall(sapmodel, (x_coordinates[v_start], y_coordinates[h_end]), (x_coordinates[v_start], y_coordinates[h_start]), top_z, bottom_z, wall_section)

                    # Definicion, creacion de columnas

                    for h in range(len(x_coordinates)):  #cambio: toma x_coordinates de la lista actualizada list_col. h toma valores entre 0 hasta numero de elementos de x_coordinates
                        for v in range(len(y_coordinates)): #cambio: toma y_coordinates de la lista actualizada list_col.
                            skip = any(
                                core["horizontal"][0] <= v <= core["horizontal"][1] and
                                core["vertical"][0] <= h <= core["vertical"][1]
                                for core in cores
                            )
                            if not skip:
                                define_column(sapmodel, grid_points, h, v, bottom_z, top_z, column_section) #cambio: define_column(sapmodel, list_col, h, v, bottom_z, top_z, column_section)

                    # Add beams in X direction
                    for i in range(len(x_coordinates) - 1):
                        for j in range(len(y_coordinates)):
                                define_beam(sapmodel, grid_points, i, j, i + 1, j, z_coordinate, beam_section)

                    # Add beams in Y direction
                    for i in range(len(x_coordinates)):
                        for j in range(len(y_coordinates) - 1):
                                define_beam(sapmodel, grid_points, i, j, i, j + 1, z_coordinate, beam_section)

                # Asignar cargas uniformes a todos los objetos de área del grupo "ALL"
                ret = sapmodel.AreaObj.SetLoadUniform(
                    "ALL",          # Nombre del grupo
                    "DEAD",         # Patrón de carga
                    -2.5,          # Valor de carga uniforme
                    2,              # Dirección (2 = global Y)
                    False,          # No reemplazar otras cargas
                    "Local",        # Sistema de coordenadas
                    1 # Tipo de ítem: aplicar al grupo
                )

                ret = sapmodel.AreaObj.SetLoadUniform(
                    "ALL",          # Nombre del grupo
                    "LIVE",         # Patrón de carga
                    -1.5,          # Valor de carga uniforme
                    2,              # Dirección (2 = global Y)
                    False,          # No reemplazar otras cargas
                    "Local",        # Sistema de coordenadas
                    1 # Tipo de ítem: aplicar al grupo
                )
                
        #Sismic analyse
        #Set mass source
                MyLoadPat = []
                MySF = []
                MyLoadPat.append("DEAD")
                MyLoadPat.append("LIVE")
                MySF.append(1)
                MySF.append(0.25)

                ret = sapmodel.PropMaterial.SetMassSource(2, 2, MyLoadPat, MySF) #mass from laods

        #Add spectrum function
                ret = sapmodel.Func.FuncRS.SetNTC2018("RS-1", 1, 45.9, 12.6, 1, 3, 2, 50, 0.2, 2.4, 0.3, 3, 2, 1, 1, 5, 1)

        #Set response spectrum load case
            
                Name = 'SDX'
                ret = sapmodel.LoadCases.ResponseSpectrum.SetCase(Name)
                NumberLoads = 2
                LoadName = ['U1','U2']
                Func = ['RS-1','RS-1']
                SF = [9.81,2.943]
                CSys = ['Global','Global']
                Ang = [0.0,90.0]
                ret = sapmodel.LoadCases.ResponseSpectrum.SetLoads(Name,NumberLoads,LoadName,Func,SF,CSys,Ang)

                Name = 'SDY'
                ret = sapmodel.LoadCases.ResponseSpectrum.SetCase(Name)
                NumberLoads = 2
                LoadName = ['U2','U1']
                Func = ['RS-1','RS-1']
                SF = [9.81,2.943]
                CSys = ['Global','Global']
                Ang = [90.0,0.0]
                ret = sapmodel.LoadCases.ResponseSpectrum.SetLoads(Name,NumberLoads,LoadName,Func,SF,CSys,Ang)
        
        # crea una combinacion de cargas
        # "1.4DL+1.7LL" (1 = combinación lineal aditiva)
                ret = sapmodel.RespCombo.Add("1.4DL+1.7LL", 0)      
        #add load case to combo
                ret = sapmodel.RespCombo.SetCaseList("1.4DL+1.7LL", 0, "DEAD", 1.4)
                ret = sapmodel.RespCombo.SetCaseList("1.4DL+1.7LL", 0, "LIVE", 1.7)

        # "1.25(DL+LL)+SDX" (1 = combinación lineal aditiva)
                ret = sapmodel.RespCombo.Add("1.25(DL+LL)+SDX", 0)      
        #add load case to combo
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDX", 0, "DEAD", 1.25)
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDX", 0, "LIVE", 1.25)
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDX", 0, "SDX", 1.0)

        # "1.25(DL+LL)+SDY" (1 = combinación lineal aditiva)
                ret = sapmodel.RespCombo.Add("1.25(DL+LL)+SDY", 0)      
        #add load case to combo
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDY", 0, "DEAD", 1.25)
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDY", 0, "LIVE", 1.25)
                ret = sapmodel.RespCombo.SetCaseList("1.25(DL+LL)+SDY", 0, "SDY", 1.0)

        # "0.9DL+SDX" (1 = combinación lineal aditiva)
                ret = sapmodel.RespCombo.Add("0.9DL+SDX", 0)      
        #add load case to combo
                ret = sapmodel.RespCombo.SetCaseList("0.9DL+SDX", 0, "DEAD", 0.9)
                ret = sapmodel.RespCombo.SetCaseList("0.9DL+SDX", 0, "SDX", 1.0)

        # "0.9DL+SDY" (1 = combinación lineal aditiva)
                ret = sapmodel.RespCombo.Add("0.9DL+SDY", 0)      
        #add load case to combo
                ret = sapmodel.RespCombo.SetCaseList("0.9DL+SDY", 0, "DEAD", 0.9)
                ret = sapmodel.RespCombo.SetCaseList("0.9DL+SDY", 0, "SDY", 1.0)

        # Correr analysis en ETAB y guardar archivo
                print("start analyse")
        # Crear carpeta para guardar el modelo
                model_path = r"D:\PYTHON UTEC\PROYECTO\calculo_etabs"
                os.makedirs(model_path, exist_ok=True)
        # Guardar el modelo
                model_file = os.path.join(model_path, "example.edb")
                sapmodel.File.Save(model_file)
        # Ejecutar análisis estructural
                sapmodel.Analyze.RunAnalysis()

        # Results for DEAD loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetCaseSelectedForOutput('DEAD')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []


        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)

                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "DEAD" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
                print('Diccionario de dead loads')
                dead_load = {
                        "P": (P[0],P[1],P[2]),
                        "V2": (V2[0],V2[1],V2[2]),
                        "V3": (V3[0],V3[1],V3[2]),
                        "T": (T[0],T[1],T[2]),
                        "M2": (M2[0],M2[1],M2[2]),
                        "M3": (M3[0],M3[1],M3[2])
                    }
                print(dead_load)
        # Results for LIVE loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetCaseSelectedForOutput('LIVE')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []


        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)

                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "LIVE" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
                print('Diccionario de live_loads')
                live_load = {
                        "P": (P[0],P[1],P[2]),
                        "V2": (V2[0],V2[1],V2[2]),
                        "V3": (V3[0],V3[1],V3[2]),
                        "T": (T[0],T[1],T[2]),
                        "M2": (M2[0],M2[1],M2[2]),
                        "M3": (M3[0],M3[1],M3[2])
                    }
                print(live_load)
        # Results for sismic SDX loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetCaseSelectedForOutput('SDX')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []


        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)

                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "SDX" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
                print('Diccionario de SDX loads')
                SDX_load = {
                        "P": (P[0],P[1],P[2]),
                        "V2": (V2[0],V2[1],V2[2]),
                        "V3": (V3[0],V3[1],V3[2]),
                        "T": (T[0],T[1],T[2]),
                        "M2": (M2[0],M2[1],M2[2]),
                        "M3": (M3[0],M3[1],M3[2])
                    }
                print(SDX_load)
        # Results for sismic SDY loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetCaseSelectedForOutput('SDY')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []
                print('Diccionario de SDY loads')
                SDY_load = {
                        "P": (P[0],P[1],P[2]),
                        "V2": (V2[0],V2[1],V2[2]),
                        "V3": (V3[0],V3[1],V3[2]),
                        "T": (T[0],T[1],T[2]),
                        "M2": (M2[0],M2[1],M2[2]),
                        "M3": (M3[0],M3[1],M3[2])
                    }
                print(SDY_load)
        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)

                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "SDY" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
        # Results for sismic 1.4DL+1.7LL loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetComboSelectedForOutput(str('1.4DL+1.7LL'))  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []


        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)

                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "1.4DL+1.7LL" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()


        # Results for sismic 1.25(DL+LL)+SDX loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetComboSelectedForOutput('1.25(DL+LL)+SDX')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []

        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)
                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "1.25(DL+LL)+SDX" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
        # Results for sismic 1.25(DL+LL)+SDY loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetComboSelectedForOutput('1.25(DL+LL)+SDY')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []
 
        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)
                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "1.25(DL+LL)+SDY" en dicc son: ')
                print()

                case_SDX_01 = {'P' : [P[0],P[1],P[2]],
                               'V2' : [V2[0],V2[1],V2[2]],
                               'V3' : [V3[0],V3[1],V3[2]],
                               'T' : [T[0],T[1],T[2]],
                               'M2' : [M2[0],M2[1],M2[2]],
                               'M3' : [M3[0],M3[1],M3[2]]}
                case_SDX_01
        # Results for sismic 0.9DL+SDX loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetComboSelectedForOutput('0.9DL+SDX')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []

        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)
                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "0.9DL+SDX" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()
        # Results for sismic 0.9DL+SDY loads
                ret = sapmodel.Results.Setup.DeselectAllCasesAndCombosForOutput()
                ret = sapmodel.Results.Setup.SetComboSelectedForOutput('0.9DL+SDY')  # Or your actual case
        #Loads 
                NumberResults = 0
                eItemTypeElm = 0  # or use the real enum: eItemTypeElm.ObjectElm
                FrameName = str(1)
                Obj = []
                ObjSta = []
                Elm = []
                ElmSta = []
                LoadCase = []
                StepType = []
                StepNum = []
                P = []
                V2 = []
                V3 = []
                T = []
                M2 = []
                M3 = []

        # ---- CORRECT UNPACKING ----
                [NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3,ret] = sapmodel.Results.FrameForce(FrameName,eItemTypeElm,NumberResults,Obj,ObjSta,Elm,ElmSta,LoadCase,StepType,StepNum,P,V2,V3,T,M2,M3)
                if ret == 0:
                    print("Loads successfully extracted")
                print(f'Las cargas para el elemento 1 para el caso de carga "0.9DL+SDY" son: ')
                print()
                print(f'P = {P[0],P[1],P[2]}')
                print(f'V2 = {V2[0],V2[1],V2[2]}')
                print(f'V3 = {V3[0],V3[1],V3[2]}')
                print(f'T = {T[0],T[1],T[2]}')
                print(f'M2 = {M2[0],M2[1],M2[2]}')
                print(f'M3 = {M3[0],M3[1],M3[2]}')
                print()

                print('Diccionario que muestras todos los casos de carga simples: ')

                import streamlit as st

                # Junta los diccionarios
                all_loads = {
                    "DEAD": dead_load,
                    "LIVE": live_load,
                    "SDX": SDX_load,
                    "SDY": SDY_load
                }

                # Guárdalos en session_state
                st.session_state.loads = all_loads


                sapmodel.View.RefreshView()
                return True

            except Exception as e:
                print(f"Model building error: {e}")
                return False
            finally:
                if 'etabs_object' in locals() and 'sapmodel' in locals():
                    disconnect_from_etabs(etabs_object, sapmodel)

#{'coordinates': {'x_coordinates': [0, 5, 13, 21, 29, 37, 45, 53, 61, 66], 'y_coordinates': [0, 5, 10, 15, 20]}, 'balcones': [[1, 3, 5, 7], [1, 3]], 'openings': [(3, 6, 1, 3)], 'muros': [{'horizontal': (3, 1), 'vertical': (0, 1)}, {'horizontal': (3, 1), 'vertical': (8, 9)}]}

#x_coords_list = [0, 5, 13, 21, 29, 37, 45, 53, 61, 66]
#y_coords_list = [0, 5, 10, 15, 20]
#[bal_h_list, bal_v_list] = [[1, 3, 5, 7], [1, 3]]
#openings_list = [(3, 6, 1, 3)]
#muros_list = [{'horizontal': (3, 1), 'vertical': (0, 1)}, {'horizontal': (3, 1), 'vertical': (8, 9)}]

#final_data = {
#        "coordinates": {
#            "x_coordinates": x_coords_list,
#            "y_coordinates": y_coords_list
#        },
#        "balcones": [bal_h_list, bal_v_list],
#        "openings": openings_list,
#        "muros": muros_list}

#story_heights = [5, 3.5, 3.5, 3.5]  # Heights of the stories
#x_coordinates = final_data["coordinates"]["x_coordinates"]
#y_coordinates = final_data["coordinates"]["y_coordinates"]
#balcony_axis = final_data["balcones"]  # List [bal_h_list, bal_v_list]
#openings = final_data["openings"]
#cores = final_data["muros"]

#build_etabs_model_with_beams(story_heights,
#            x_coordinates,
#            y_coordinates,
#            slab_prop_name="Slab1",
#            slab_offset=0.3,
#            balcony_axis=balcony_axis,
#            balcony_width=4,
#            balcony_depth=2,
#            balcony_offset=4.0,
 #           wall_section="Wall1",
 #           column_section="ConcCol",
  #          beam_section="ConcBm",
   #         cores=cores,
    #        openings=openings)