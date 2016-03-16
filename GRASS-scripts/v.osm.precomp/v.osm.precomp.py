#!/usr/bin/env python
#  -*- coding:utf-8 -*-
##############################################################################
# MODULE:    v.osm.precomp
# AUTHOR(S): Monia Molinari, Marco Minghini
# PURPOSE:   Tool for the comparison of two road datasets
# COPYRIGHT: (C) 2015 by the GRASS Development Team
#
# This program is free software under the GNU General Public
# License (>=v2). Read the file COPYING that comes with GRASS
# for details.
# ############################################################################
#%Module
#%  description: Tool for the preliminary comparison between OSM and reference datasets
#%  keywords: vector, OSM, comparison
#%End

#%option
#% key: osm
#% type: string
#% gisprompt: old,vector,vector
#% description: OpenStreetMap dataset
#% required: yes
#%end

#%option
#% key: ref
#% type: string
#% gisprompt: old,vector,input
#% description: Reference dataset
#% required: yes
#%end

#%option
#% key: buffers
#% type: string
#% description: List of buffer values around reference and OpenStreetMap dataset (map units)
#% required: yes
#%end

#%option
#% key: roi
#% type: string
#% gisprompt: old,vector,vector
#% description: Clipping mask
#% required: no
#%end

#%option
#% key: out_graphs
#% type: string
#% description: Folder for output graphs
#% required: no
#%end

#%option G_OPT_F_OUTPUT
#% description: Name for output file
#% required: yes
#%end

import sys
import time
import grass.script as grass
import os


def checkPath(path):
    if os.path.exists(path):
        return
    else:
        try:
            os.mkdir(path)
        except:
            grass.errors(_("The path '{st}' doesn't exists".format(st=path)))


def GetStat(osm, ref, buff, processid):
    ref_buffer = "ref_buffer_" + processid
    osm_buffer = "osm_buffer_" + processid
    ref_in = "ref_in_" + processid
    ref_out = "ref_out_" + processid
    osm_in = "osm_in_" + processid
    osm_out = "osm_out_" + processid

    # Calculate REF data in and out OSM buffer
    grass.run_command("v.buffer", input=osm, output=osm_buffer, distance=buff,
                      type="line", overwrite=True, quiet=True)
    grass.run_command("v.overlay", ainput=ref, binput=osm_buffer,
                      operator="and", output=ref_in, atype="line", flags="t",
                      overwrite=True, quiet=True)
    grass.run_command("v.overlay", ainput=ref, binput=osm_buffer,
                      operator="not", output=ref_out, atype="line", flags="t",
                      overwrite=True, quiet=True)
    s_ref_in = length(ref_in)
    s_ref_out = length(ref_out)

    # Calculate OSM data in and out REF buffer
    grass.run_command("v.buffer", input=ref, output=ref_buffer, distance=buff,
                      type="line", overwrite=True, quiet=True)
    grass.run_command("v.overlay", ainput=osm, binput=ref_buffer,
                      operator="and", output=osm_in, atype="line", flags="t",
                      overwrite=True, quiet=True)
    grass.run_command("v.overlay", ainput=osm, binput=ref_buffer,
                      operator="not", output=osm_out, atype="line", flags="t",
                      overwrite=True, quiet=True)
    s_osm_in = length(osm_in)
    s_osm_out = length(osm_out)

    # Remove temporary data
    grass.run_command("g.remove", type="vect", flags="fr",
                      pattern="{st}*".format(st=processid), quiet=True)

    return (s_ref_in, s_ref_out, s_osm_in, s_osm_out)


def Plot(buff, osm_in, ref_in, REF_tot, OSM_tot, out):
    import pylab

    ref_in = pylab.array(ref_in)
    ref_out = REF_tot - ref_in
    ref_in_perc = (ref_in / float(REF_tot)) * 100
    ref_out_perc = 100 - ref_in_perc
    osm_in = pylab.array(osm_in)
    osm_out = OSM_tot - osm_in
    osm_in_perc = (osm_in / float(OSM_tot)) * 100
    osm_out_perc = 100 - osm_in_perc

    REF_tot_km = REF_tot / float(1000)
    ref_in_km = ref_in / float(1000)
    ref_out_km = ref_out / float(1000)
    OSM_tot_km = OSM_tot / float(1000)
    osm_in_km = osm_in / float(1000)
    osm_out_km = osm_out / float(1000)

    # Plot of the length of OSM in the buffer around REF
    pylab.figure()
    pylab.plot(buff, osm_in_km, 'ro-',
               label='OSM total length = {st} km'.format(st=OSM_tot_km))
    pylab.title('Similarity of OSM compared to REF')
    pylab.xlabel('Buffer width around REF dataset [m]')
    pylab.ylabel('OSM length included in the buffer [km]')
    pylab.axis([0, buff[-1] * 1.05, 0, OSM_tot_km * 1.05])
    pylab.legend(loc="lower right")
    pylab.grid()
    pylab.savefig("{st}/osm_in_km.png".format(st=out))

    # Plot of the percentage of OSM in the buffer around REF
    pylab.figure()
    pylab.plot(buff, osm_in_perc, 'ro-',
               label='OSM total length = {st} km'.format(st=OSM_tot_km))
    pylab.title('Similarity of OSM compared to REF')
    pylab.xlabel('Buffer width around REF dataset [m]')
    pylab.ylabel('OSM length included in the buffer [%]')
    pylab.axis([0, buff[-1] * 1.05, 0, 100])
    pylab.legend(loc="lower right")
    pylab.grid()
    pylab.savefig("{st}/osm_in_perc.png".format(st=out))

    # Plot of the length of OSM outside the buffer around REF
    pylab.figure()
    pylab.plot(buff, osm_out_km, 'ro-',
               label='OSM total length = {st} km'.format(st=OSM_tot_km))
    pylab.title('Similarity of OSM compared to REF')
    pylab.xlabel('Buffer width around REF dataset [m]')
    pylab.ylabel('OSM length not included in the buffer [km]')
    pylab.axis([0, buff[-1] * 1.05, 0, OSM_tot_km * 1.05])
    pylab.legend(loc="upper right")
    pylab.grid()
    pylab.savefig("{st}/osm_out_km.png".format(st=out))

    # Plot of the percentage of OSM outside the buffer around REF
    pylab.figure()
    pylab.plot(buff, osm_out_perc, 'ro-',
               label='OSM total length = {st} km'.format(st=OSM_tot_km))
    pylab.title('Similarity of OSM compared to REF')
    pylab.xlabel('Buffer width around REF dataset [m]')
    pylab.ylabel('OSM length not included in the buffer [%]')
    pylab.axis([0, buff[-1] * 1.05, 0, 100])
    pylab.legend(loc="upper right")
    pylab.grid()
    pylab.savefig("{st}/osm_out_perc.png".format(st=out))

    # Plot of the length of REF in the buffer around OSM
    pylab.figure()
    pylab.plot(buff, ref_in_km, 'bo-',
               label='REF total length = {st} km'.format(st=REF_tot_km))
    pylab.title('Similarity of REF compared to OSM')
    pylab.xlabel('Buffer width around OSM dataset [m]')
    pylab.ylabel('REF length included in the buffer [km]')
    pylab.axis([0, buff[-1] * 1.05, 0, REF_tot_km * 1.05])
    pylab.legend(loc="lower right")
    pylab.grid()
    pylab.savefig("{st}/ref_in_km.png".format(st=out))

    # Plot of the percentage of REF in the buffer around OSM
    pylab.figure()
    pylab.plot(buff, ref_in_perc, 'bo-',
               label='REF total length = {st} km'.format(st=REF_tot_km))
    pylab.title('Similarity of REF compared to OSM')
    pylab.xlabel('Buffer width around OSM dataset [m]')
    pylab.ylabel('REF length included in the buffer [%]')
    pylab.axis([0, buff[-1] * 1.05, 0, 100])
    pylab.legend(loc="lower right")
    pylab.grid()
    pylab.savefig("{st}/ref_in_perc.png".format(st=out))

    # Plot of the length of REF outside the buffer around OSM
    pylab.figure()
    pylab.plot(buff, ref_out_km, 'bo-',
               label='REF total length = {st} km'.format(st=REF_tot_km))
    pylab.title('Similarity of REF compared to OSM')
    pylab.xlabel('Buffer width around OSM dataset [m]')
    pylab.ylabel('REF length not included in the buffer [km]')
    pylab.axis([0, buff[-1] * 1.05, 0, REF_tot_km * 1.05])
    pylab.legend(loc="upper right")
    pylab.grid()
    pylab.savefig("{st}/ref_out_km.png".format(st=out))

    # Plot of the percentage of REF outside the buffer around OSM
    pylab.figure()
    pylab.plot(buff, ref_out_perc, 'bo-',
               label='REF total length = {st} km'.format(st=REF_tot_km))
    pylab.title('Similarity of REF compared to OSM')
    pylab.xlabel('Buffer width around OSM dataset [m]')
    pylab.ylabel('REF length not included in the buffer [%]')
    pylab.axis([0, buff[-1] * 1.05, 0, 100])
    pylab.legend(loc="upper right")
    pylab.grid()
    pylab.savefig("{st}/ref_out_perc.png".format(st=out))


def length(data):
    feat_osm = int(((grass.read_command("v.info", map=data, flags="t",
                                        quiet=True)).split("\n")[2]).split("=")[1])
    if feat_osm > 0:
        length_data = grass.read_command("v.to.db", map=data, option="length",
                                         flags="p")
        s_data = 0
        l_data = length_data.split("\n")
        for item in l_data[1:-1]:
            s_data += float(item.split("|")[1])
    else:
        s_data = 0
    return s_data


def GetInfo(fileName):
    lines = [line.strip() for line in open(fileName)]
    ref_in = lines[3].split(': ')[1].split(' ')[0]
    osm_in = lines[5].split(': ')[1].split(' ')[0]
    return (float(ref_in), float(osm_in))


def main():
    processid = str(time.time()).replace(".", "_")
    osm = options["osm"]
    ref = options["ref"]
    buff = options["buffers"]
    roi = options["roi"]
    out_graphs = options["out_graphs"]
    out = options["output"]

    # Check if input files exist
    if not grass.find_file(name=osm, element='vector')['file']:
        grass.fatal(_("Vector map <%s> not found") % osm)

    if not grass.find_file(name=ref, element='vector')['file']:
        grass.fatal(_("Vector map <%s> not found") % ref)

    if len(roi) > 0:
        if not grass.find_file(name=roi, element='vector')['file']:
            grass.fatal(_("Vector map <%s> not found") % roi)

    # OSM and REF length
    s_ref = length(ref)
    s_osm = length(osm)

    if s_ref == 0:
        grass.run_command("g.remove", type="vect", flags="fr",
                          pattern="{st}*".format(st=processid), quiet=True)
        grass.fatal(_("No reference data for comparison"))

    if s_osm == 0:
        grass.run_command("g.remove", type="vect", flags="fr",
                          pattern="{st}*".format(st=processid), quiet=True)
        grass.fatal(_("No OSM data for comparison"))

    diff = s_ref - s_osm
    diff_p = diff / s_ref * 100

    # Temporary names
    processid = str(time.time()).replace(".", "_")
    ref_roi = "ref_roi_" + processid
    osm_roi = "osm_roi_" + processid

    # Apply mask
    if len(roi) > 0:
        grass.run_command("v.overlay", ainput=ref, atype="line", binput=roi,
                          operator="and", output=ref_roi, flags="t", quiet=True)
        grass.run_command("v.overlay", ainput=osm, atype="line", binput=roi,
                          operator="and", output=osm_roi, flags="t", quiet=True)
        ref = ref_roi
        osm = osm_roi

    # Extract list of buffer values
    list_buff = map(float, buff.split(","))

    # Calculate list of statistics
    l_osm_out = []
    l_var_osm_out = []
    l_ref_out = []
    l_var_ref_out = []
    l_osm_in = []
    l_var_osm_in = []
    l_ref_in = []
    l_var_ref_in = []

    # Print statistics
    checkPath(os.path.split(out)[0])
    fil = open(out, "w")
    fil.write("REF length: {rl} m\n".format(rl=round(s_ref, 1)))
    fil.write("OSM length: {ol} m\n".format(ol=round(s_osm, 1)))
    fil.write("REF-OSM difference: {di} m ({dp}%)\n".format(di=round(diff, 1),
                                                            dp=round(diff_p, 1)))
    fil.write("\n")
    fil.write("BUFFER(m)|OSM_IN(m)|OSM_IN(%%)|OSM_OUT(m)|OSM_OUT(%%)|REF_IN(m)"
              "|REF_IN(%%)|REF_OUT(m)|REF_OUT(%%)\n")

    for b in list_buff:
        (s_ref_in, s_ref_out, s_osm_in, s_osm_out) = GetStat(osm, ref, b,
                                                             processid)
        osm_in = round(s_osm_in, 1)
        l_osm_in.append(osm_in)
        var_osm_in = round(s_osm_in / s_osm * 100, 1)
        l_var_osm_in.append(var_osm_in)
        ref_in = round(s_ref_in, 1)
        l_ref_in.append(ref_in)
        var_ref_in = round(s_ref_in / s_ref * 100, 1)
        l_var_ref_in.append(var_ref_in)
        osm_out = round(s_osm_out, 1)
        l_osm_out.append(osm_out)
        var_osm_out = round(s_osm_out / s_osm * 100, 1)
        l_var_osm_out.append(var_osm_out)
        ref_out = round(s_ref_out, 1)
        l_ref_out.append(ref_out)
        var_ref_out = round(s_ref_out / s_ref * 100, 1)
        l_var_ref_out.append(var_ref_out)

        fil.write("{bi}|{oi}|{voi}|{oo}|{voo}|{ri}|{vri}|{ro}|{vro}"
                  "\n".format(bi=b, oi=osm_in, voi=var_osm_in, oo=osm_out,
                              voo=var_osm_out, ri=ref_in, vri=var_ref_in,
                              ro=ref_out, vro=var_ref_out))

    fil.close()

    # Remove temporary data
    grass.run_command("g.remove", type="vect", flags="fr",
                      pattern="{st}*".format(st=processid), quiet=True)

    # Graphs
    checkPath(out_graphs)
    if out_graphs:
        Plot(list_buff, l_osm_in, l_ref_in, s_ref, s_osm, out_graphs)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
