#!/usr/bin/env python
#
# ----------------------------------------------------------------------
#
#                           Brad T. Aagaard
#                        U.S. Geological Survey
#
# <LicenseText>
#
# ----------------------------------------------------------------------
#

cell = "quad4"
dx = 100
dt = 0.05

outputRoot = "output/%s_%3dm_%s" % (cell,dx,"refine")
outdir = "scecfiles/%s_%3dm_%s/" % (cell,dx,"refine")

# ----------------------------------------------------------------------

import numpy
import time

from pylith.utils.VTKDataReader import VTKDataReader

# ----------------------------------------------------------------------
timestamps = numpy.arange(50,12001,50)
targets = numpy.array([[+3000.0, -2000.0, 0.0],
                       [-3000.0, -2000.0, 0.0],
                       [+3000.0, +2000.0, 0.0],
                       [ -600.0, +2000.0, 0.0],
                       [-4200.0, +2000.0, 0.0],
                       [+3000.0, +5000.0, 0.0],
                       [-1400.0, +5000.0, 0.0],
                       [-5900.0, +5000.0, 0.0],
                       [+3000.0, +8000.0, 0.0],
                       [-2300.0, +8000.0, 0.0],
                       [-7600.0, +8000.0, 0.0]])

targets[:,1] = targets[:,1] + 2000

reader = VTKDataReader()
tolerance = 1.0e-6

# Get vertices and find indices of target locations
filename = "%s_t%05d.vtk" % (outputRoot,timestamps[0])
data = reader.read(filename)

vertices = numpy.array(data['vertices'])
ntargets = targets.shape[0]
indices = []
indices1 = []
for target in targets:
    dist = ( (vertices[:,0]-target[0])**2 + 
             (vertices[:,1]-target[1])**2 +
             (vertices[:,2]-target[2])**2 )**0.5
    min = numpy.min(dist)
    indices.append(numpy.where(dist <= min+tolerance)[0])
    indices1.append(numpy.where(dist <= min+tolerance)[0][0])

print "Indices", indices
print "Coordinates of selected points:",vertices[indices1,:]

# Extract values
nsteps = timestamps.shape[0]
disp = numpy.zeros((nsteps,ntargets,3))  # 3-D array (time, targets, components)
vel = numpy.zeros((nsteps,ntargets,3))
itime = 0
for timestamp in timestamps:
    filename = "%s_t%05d.vtk" % (outputRoot,timestamp)
    data = reader.read(filename)
    fields = data['vertex_fields']
    disp[itime,0:ntargets,:] = fields['displacement'][indices1,:].squeeze()
    vel[itime,0:ntargets,:] = fields['velocity'][indices1,:].squeeze()
    itime += 1


# Write data
headerA = \
    "# problem = TPV14-2D\n" + \
    "# author = Surendra N. Somala\n" + \
    "# code = PyLith\n" + \
    "# code_version = 1.5.1\n" + \
    "# element_size = %s\n" % dx
headerB = \
    "# Time series in 7 columns of E14.6:\n" + \
    "# Column #1 = time (s)\n" + \
    "# Column #2 = horizontal fault-parallel displacement (m)\n" + \
    "# Column #3 = horizontal fault-parallel velocity (m/s)\n" + \
    "# Column #4 = vertical displacement (m)\n" + \
    "# Column #5 = vertical velocity (m/s)\n" + \
    "# Column #6 = horizontal fault-normal displacement (m)\n" + \
    "# Column #7 = horizontal fault-normal velocity (m/s)\n" + \
    "#\n" + \
    "# Data fields\n" + \
    "t h-disp h-vel v-disp v-vel n-disp n-vel\n" + \
    "#\n"

locHeader = "# location = %3.1f km off fault, %3.1f km along strike " \
    "and %3.1f km depth\n"
locName = "%+04dst%+04ddp%03d"

lengthScale = 1000.0
timeScale = 1000.0
dip = 7.5
body = targets[:,0] / lengthScale
strike = (targets[:,1] - 2000) / lengthScale
time = timestamps / timeScale

for iloc in xrange(ntargets):
    pt = locName % (round(10*body[iloc]), 
                    round(10*strike[iloc]),
                    round(10*dip))
    filename = "%sbody%s.dat" % (outdir, pt)
    fout = open(filename, 'w')
    fout.write(headerA)
    fout.write("# time_step = %14.6E\n" % dt)
    fout.write("# num_timesteps = %8d\n" % nsteps)
    fout.write(locHeader % (body[iloc], 
                             strike[iloc], 
                             dip))
    fout.write(headerB)
    data = numpy.transpose((time,
                            -disp[:,iloc,1],
                            -vel[:,iloc,1],
                            +disp[:,iloc,2],
                            +vel[:,iloc,2],
                            -disp[:,iloc,0],
                            -vel[:,iloc,0]))
    numpy.savetxt(fout, data, fmt='%14.6e')
    fout.close()


