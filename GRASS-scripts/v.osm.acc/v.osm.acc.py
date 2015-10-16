#!/usr/bin/env python 
#  -*- coding:utf-8 -*-
############################################################################## 
# MODULE: v.osm.acc
# AUTHOR(S): Monia Elisa Molinari, Marco Minghini
# PURPOSE: Tool for accuracy assessment of OSM data
# COPYRIGHT: (C) 2015 by the GRASS Development Team 
# 
# This program is free software under the GNU General Public 
# License (>=v2). Read the file COPYING that comes with GRASS 
# for details. 
# ############################################################################
#%Module
#% description: Tool for accuracy assessment of OSM data
#% keywords: vector
#% keyword: OSM
#% keyword: accuracy
#%End
#%option G_OPT_V_INPUT
#% key: osm
#% label: OpenStreetMap dataset
#% required : yes
#%end
#%option G_OPT_V_INPUT
#% key: ref
#% label: Reference dataset
#% required : yes
#%end
#%option G_OPT_V_INPUT
#% key: grid
#% label: Vector grid for comparison
#% guisection: Grid
#% required: no
#%end
#%option
#% key: ul_grid
#% type: string
#% guisection: Grid
#% description: Coordinates of the upper left grid corner (x,y)
#% required: no
#%end
#%option
#% key: lr_grid
#% type: string
#% guisection: Grid
#% description: Coordinates of the lower right grid corner (x,y)
#% required: no
#%end
#%option
#% key: box_grid
#% type: string
#% guisection: Grid
#% description: Width and height for boxes in grid (map units)
#% required: no
#%end
#%option G_OPT_V_INPUT
#% key: output
#% type: string
#% guisection: Grid
#% label: Name for the grid vector output map
#% required: no
#%end
#%option
#% key: tol_max
#% type: double
#% guisection: Deviation analysis
#% description: Upper bound value for automated accuracy evaluation (map units)
#% required: no
#%end
#%option
#% key: perc
#% type: double
#% guisection: Deviation analysis
#% description: Length percentage of OSM dataset to be considered for automated accuracy evaluation (%)
#% required: no
#% answer: 100
#%end
#%option
#% key: tol_eval
#% type: string
#% guisection: Deviation analysis
#% description: Threshold values for accuracy evaluation, separated by comma (map units)
#% required: no
#%end

import sys
import math
import time
import grass.script as grass

def GetList(vect):
    list_vect = grass.read_command("v.db.select",map=vect,columns="cat",flags="c",quiet=True)
    list_v = list_vect.split("\n")[0:-1]  
    return list_v 
     
def MakeGrid(n,w,s,e,nsres,ewres,out):
    rows = math.ceil(float((n-s)/nsres))   
    cols = math.ceil(float((e-w)/ewres))   
    grass.run_command("g.region",n=n,s=n-nsres*rows,e=w+ewres*cols,w=w,quiet=True)    
    grass.run_command("v.mkgrid",map=out,grid="%s,%s"%(rows,cols),quiet=True)

def GetRefBox(ref,ref_box,k_box,processid):    
    N = grass.region()['n']
    S = grass.region()['s']
    E = grass.region()['e']
    W = grass.region()['w']
    grass.run_command("g.region",vect=k_box,quiet=True)
    ns_ext = (math.ceil(grass.region()['n']-grass.region()['s']))*10/100
    ew_ext = (math.ceil(grass.region()['e']-grass.region()['w']))*10/100
    grass.run_command("g.region",n=grass.region()['n']+ns_ext/2,s=grass.region()['s']-ns_ext/2,w=grass.region()['w']-ew_ext/2,e=grass.region()['e']+ew_ext/2,quiet=True)
    grass.run_command("v.in.region",output="new_box_%s"%processid,quiet=True)
    grass.run_command("v.overlay",ainput=ref,atype="line",binput="new_box_%s"%processid,btype="area",operator="and",output=ref_box,quiet=True)
    grass.run_command("g.remove",type="vect", name="new_box_%s"%processid,flags="f",quiet=True)
    grass.run_command("g.region",n=N,s=S,e=E,w=W,quiet=True)
    
def AddCol(vect,t):
    list_c = []
    list_col = ((grass.read_command("db.describe",table=vect,flags="c",quiet=True)).split("\n"))[2:-1]
    for c in list_col:
        list_c.append((c.split(":")[1]).lstrip())
    if not "%s"%t in list_c:
        grass.run_command("v.db.addcolumn",map=vect,columns="%s double"%t,quiet=True)
        
def length(data):
    feat_data = int(((grass.read_command("v.info", map=data,flags="t")).split("\n")[2]).split("=")[1])
    if feat_data>0:
        length_data = grass.read_command("v.to.db",map=data,option="length",flags="p")
        s_data=0 
        l_data = length_data.split("\n")
        for item in l_data[1:-1]:
            s_data+=float(item.split("|")[1])         
    else:
        s_data=0
    return s_data
   
def CalcTol(data1,data2,value):
    processid = str(time.time()).replace(".","_")
    grass.run_command("v.buffer",input=data1,output="data1_buf_"+processid,distance=value,quiet=True)
    grass.run_command("v.overlay",ainput=data2,binput="data1_buf_"+processid,atype="line",btype="area",operator="and",output="data2_in_"+processid,quiet=True)
    val = length("data2_in_"+processid)
    grass.run_command("g.remove",type="vect", pattern=processid,flags="fr",quiet=True)
    return val

def main():
    osm = options["osm"]
    ref =  options["ref"] 
    grid = options["grid"]
    ul_grid = options["ul_grid"]
    lr_grid = options["lr_grid"]
    box_grid = options["box_grid"]
    output = options["output"]
    tol_eval = options["tol_eval"]
    tol_max = options["tol_max"]
    perc = float(options["perc"])

    

    ## Check if input files exist
    if not grass.find_file(name=osm,element='vector')['file']:
        grass.fatal(_("Vector map <%s> not found") % osm)

    if not grass.find_file(name=ref,element='vector')['file']:
        grass.fatal(_("Vector map <%s> not found") % ref)

    if grass.find_file(name=output,element='vector')['file']:
        grass.fatal(_("Vector map <%s> already exists") % output)

    if len(grid)>0:
        if not grass.find_file(name=grid,element='vector')['file']:
            grass.fatal(_("Vector map <%s> not found") % grid)

    # Check length OSM and REF
    check_ref = length(ref)
    check_osm = length(osm)

    if check_ref == 0:
        grass.run_command("g.remove", type="vect", pattern="%s"%processid,flags="fr",quiet=True)
        grass.fatal(_("No reference data for comparison"))

    if check_osm == 0:
        grass.run_command("g.remove", type="vect", pattern="%s"%processid,flags="fr",quiet=True)
        grass.fatal(_("No OSM data for comparison"))


    ## Check tolerance parameters
    if (len(tol_eval)>0 and len(str(tol_max))>0):
        grass.fatal("Please specify only one between <tol_eval> or <tol_max> parameters")
    
    if (len(tol_eval)==0 and len(str(tol_max))==0):  
        grass.fatal("Please specify almost one between <tol_eval> or <tol_max> parameters")
    
    
    ## Check grid parameters
    if (len(grid)>0 and (len(ul_grid)>0 or len(lr_grid)>0 or len(box_grid)>0 or len(output)>0)):
        grass.warning("A <grid> vector has been specified. All the others parameters will be ignored")    
    
    if len(grid)==0:
        if (len(ul_grid)>0 or len(lr_grid)>0 or len(box_grid)>0) and (len(ul_grid)==0 or len(lr_grid)==0 or len(box_grid)==0 or len(output)==0):
            grass.fatal("Please specify all the required parameters for grid generation: <ul_grid>,<lr_grid>,<box_grid> and <output>.")  
        
    if (len(grid)==0 and len(ul_grid)==0 and len(lr_grid)==0 and len(box_grid)==0 and len(output)==0):
        grass.fatal("No grid specified. The accuracy will be calculated on the whole current region. Please specify the name for the grid output vector map")
        

    # Prepare temporary map raster names
    processid = str(time.time()).replace(".","_")  
    k_box = "k_box_"+processid
    osm_box = "osm_box_"+processid
    ref_box = "ref_box_"+processid
    tmp_output = "tmp_out_"+processid
    
    # Get or create grid #    
    if (len(grid)>0):
        tmp_output = grid
        grass.run_command("g.region",vect=grid,quiet=True) 
    if (len(grid)==0 and len(ul_grid)>0 and len(lr_grid)>0 and len(box_grid)>0 and len(output)>0):
        n = float(ul_grid.split(",")[0])
        w = float(ul_grid.split(",")[1])
        s = float(lr_grid.split(",")[0])
        e = float(lr_grid.split(",")[1])
        nsres = float(box_grid.split(",")[1])
        ewres = float(box_grid.split(",")[0])    
        MakeGrid(n,w,s,e,nsres,ewres,tmp_output)        
    if (len(grid)==0 and len(ul_grid)==0 and len(lr_grid)==0 and len(box_grid)==0 and len(output)>0):
        grass.run_command("g.region",vect=ref,quiet=True)
        grass.run_command("v.in.region",output=output,quiet=True)  
        grass.run_command("v.db.addtable", map=output,quiet=True) 
    
    # Extract box id with where OSM data exists
    if not (len(grid)==0 and len(ul_grid)==0 and len(lr_grid)==0 and len(box_grid)==0 and len(output)>0):
        grass.run_command("v.select",ainput=tmp_output,binput=osm,operator="overlap",output=output,quiet=True)
        list_box = GetList(output)
    
    # Get tolerance values and evaluate #       
    if len(tol_eval)>0:
        list_tol = tol_eval.split(",")
        AddCol(output,"OSM")
        for item in list_tol:
            AddCol(output,"t_%s"%item)
            AddCol(output,"p_%s"%item)
        
        for k in list_box:
            grass.run_command("v.extract",input=output,output=k_box,where="cat=%s"%k,quiet=True)
            grass.run_command("v.overlay",ainput=osm,atype="line",binput=k_box,btype="area",operator="and",output=osm_box,quiet=True)
	    l_osm = length(osm_box)
            grass.run_command("v.db.update",map=output,column="OSM",value=l_osm,where="cat=%s"%k,quiet=True)   
            grass.run_command("v.overlay",ainput=ref,atype="line",binput=k_box,btype="area",operator="and",output=ref_box,quiet=True)
	    feat_ref_box = int(((grass.read_command("v.info", map=ref_box,flags="t")).split("\n")[2]).split("=")[1])
            if feat_ref_box>0:
                for item in list_tol:
                    val = CalcTol(ref_box,osm_box,float(item))
                    grass.run_command("v.db.update",map=output,column="t_%s"%item,value=val,where="cat=%s"%k,quiet=True) 
                    grass.run_command("v.db.update",map=output,column="p_%s"%item,value=val*100.0/l_osm,where="cat=%s"%k,quiet=True) 
            grass.run_command("g.remove",type="vect", pattern=processid,flags="fr",quiet=True)
                

    # Automated evaluation #    
    if len(str(tol_max))>0:
        acc = 0.005
        AddCol(output,"OSM")
        AddCol(output,"TOL")
       
        for k in list_box:
            grass.run_command("v.extract",input=output,output=k_box,where="cat=%s"%k,quiet=True)
            grass.run_command("v.overlay",ainput=osm,atype="line",binput=k_box,btype="area",operator="and",output=osm_box,quiet=True)
            real_l_osm = length(osm_box)
            if perc == 100.0:
                l_osm = real_l_osm
            else:
                l_osm = real_l_osm*float(perc)/100.0

            grass.run_command("v.db.update",map=output,column="OSM",value=real_l_osm,where="cat=%s"%k,quiet=True)   
            # Get REF_BOX data in slightly bigger box
            GetRefBox(ref,ref_box,k_box,processid)
	    if length(ref_box)>0:
                x = 0
                val = 0
                UP = float(tol_max)
                DOWN = 0.0    
                up = float(tol_max)
                down = 0.0
                mid = down + (up-down)/2
                exit = 0      
                while exit==0:
                    val = CalcTol(ref_box,osm_box,mid)
                    
                    if val >= l_osm: # all in
                        new_mid = down + (mid-down)/2
                        up = mid
                        mid = new_mid                     
                                       
                    elif val < l_osm: # not all in 
                        
                        if not down < mid + acc < up:
                            if up!=UP:
                                x = up
                                exit = 1
                            else:
                                exit = 2
                        else:
                            val = CalcTol(ref_box,osm_box,mid + acc)
                        
                        if val >= l_osm:  # all in (considering epsilon)
                            x = mid + acc
                            exit = 1
                        elif val < l_osm:  # not all in (considering epsilon)
                            new_mid =(mid+acc) + (up-(mid+acc))/2
                            down = mid + acc
                            mid = new_mid                                                    
                if exit == 1:
                    grass.run_command("v.db.update",map=output,column="TOL",value=(math.ceil(x*100))/100,where="cat=%s"%k)
                grass.run_command("g.remove",type="vect",pattern=processid,flags="fr")
	    grass.run_command("g.remove",type="vect",pattern=processid,flags="fr")
                        

if __name__ == "__main__":
    options,flags = grass.parser()
    sys.exit(main())
