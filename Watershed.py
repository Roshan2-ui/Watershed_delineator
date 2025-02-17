import arcpy
import os
from arcpy.sa import *
arcpy.env.overwriteOutput = True
data = r'' # Define Path here
out_path = r'' # Define GDB path here
arcpy.env.workspace = data_path
#Setting Environment and Data Modification

out_path = r'E:\Courses\Fall 2024\GEOG 6460\Week 9\buncombe-DEM03\Week 9\Week 9.gdb'

#Hydrological Analysis

outFlowDirection = arcpy.sa.FlowDirection(data, "NORMAL","test_flow_Dir","D8")
outFlowDirection.save("flow_dir")

Print("Flow Direction Done !")

outFlowAccumulation = FlowAccumulation("flow_dir","#","#","D8")
outFlowAccumulation.save("flow_accu")

Print("Flow Accumulation Done !")

outCon2 = Con(Raster("flow_accu") > 120000, 1, 0) # Here change the interval value changes the precision stream and non stream raster
outCon2.save("Con_raster")

Print("Flow Accumulation Reclassification Done !")

outStreamOrder = StreamOrder("Con_raster", "flow_dir", "STRAHLER")
outStreamOrder.save("StreamOrder")

Print("Stream Order Done !")

StreamToFeature("StreamO_Con_2", "flow_dir", "Stream_network", "NO_SIMPLIFY")

Print("Stream Order to polyline Conversion done Done !")

arcpy.analysis.Intersect("Stream_network", "raw_pour_points", "All", "#", "POINT")

arcpy.management.Dissolve("raw_pour_points", "raw_pour_points_dissolved")

arcpy.management.MultipartToSinglepart("raw_pour_points_dissolved", "raw_pour_points_explode")

arcpy.management.AddField("raw_pour_points_explode", "UID","LONG")

arcpy.management.CalculateField("raw_pour_points_explode", "UID", "!OBJECTID!", "PYTHON3")

arcpy.analysis.SpatialJoin("raw_pour_points", "raw_pour_points_explode", "raw_pour_points_att", "JOIN_ONE_TO_MANY", 
                           "KEEP_ALL","#", "INTERSECT")
arcpy.management.Dissolve( "raw_pour_points_att", "raw_pour_points_att_diss", "UID",
                          statistics_fields=[["grid_code", "MAX"]])

arcpy.conversion.ExportFeatures("raw_pour_points_att_diss", "Pour_points","MAX_grid_code > 2") # change the MAX grid code level to define the watershed size. Larger the number, bigger the size

Print("Pour Points Creation Done !")

outSnapPour = SnapPourPoint("Pour_points", "flow_accu", "5", "OBJECTID")
outSnapPour.save("Snappour_raster")

Print("Pour Points Snap Raster Creation Done !")

outWatershed = Watershed("flow_dir", "Snappour_raster")
outWatershed.save("Watershed")

arcpy.conversion.RasterToPolygon("Watershed", "Watershed_Poly")

Print("Watershed into Polygon Creation Done !")

#Remove Silver Polygons by Merging

arcpy.MakeFeatureLayer_management("Watershed_Poly", "Watershed_Poly_layer")
arcpy.management.SelectLayerByAttribute("Watershed_Poly_layer", "NEW_SELECTION", "Shape_Area < 1051")
arcpy.Eliminate_management("Watershed_Poly_layer", "Final_Watershed_Poly","AREA")

Print("Watershed editing and Silver Polygon removing Done !")
