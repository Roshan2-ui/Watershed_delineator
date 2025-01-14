import arcpy
import os
from arcpy.sa import *
arcpy.env.overwriteOutput = True
data_path = r'' # Define Path here
out_path = r'' # Define GDB path here
arcpy.env.workspace = data_path
#Setting Environment and Data Modification

wkt = """PROJCS["NAD_1983_2011_StatePlane_North_Carolina_FIPS_3200",
         GEOGCS["GCS_NAD_1983_2011",DATUM["D_NAD_1983_2011",
         SPHEROID["GRS_1980",6378137.0,298.257222101]],
         PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],
         PROJECTION["Lambert_Conformal_Conic"],
         PARAMETER["False_Easting",609601.2192024384],
         PARAMETER["False_Northing",0.0],
         PARAMETER["Central_Meridian",-79.0],
         PARAMETER["Standard_Parallel_1",34.33333333333334],
         PARAMETER["Standard_Parallel_2",36.16666666666666],
         PARAMETER["Latitude_Of_Origin",33.75],
         UNIT["Meter",1.0]]"""

arcpy.management.ProjectRaster( "buncombe-DEM03.tif", "E:/Courses/Fall 2024/GEOG 6460/Week 9/buncombe-DEM03/Week 9/Week 9.gdb/Prj_raster",
                               wkt, "BILINEAR", "1", "#", "#", "#", "#")

out_path = r'E:\Courses\Fall 2024\GEOG 6460\Week 9\buncombe-DEM03\Week 9\Week 9.gdb'
arcpy.env.workspace = out_path

prj_raster = arcpy.Raster("Prj_raster")
raster_meter2 = prj_raster * 0.3048
raster_meter2.save(r"raster_meter2")

outFill = Fill("raster_meter2")
outFill.save(r"raster_meter_f")

#Hydrological Analysis

outFlowDirection = arcpy.sa.FlowDirection("raster_meter_f", "NORMAL","test_flow_Dir","D8")
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

Print("Watershed editing Creation and Silver Polygon removing Done !")
