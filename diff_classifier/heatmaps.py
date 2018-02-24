import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
import os
import os.path as op
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import numpy.ma as ma
import matplotlib as mpl
import matplotlib.cm as cm


def voronoi_finite_polygons_2d(vor, radius=None):
    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite
    regions.

    Parameters
    ----------
    vor : Voronoi
        Input diagram
    radius : float, optional
        Distance to 'points at infinity'.

    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.

    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    counter = 0
    for p1, region in enumerate(vor.point_region):
        try:
            vertices = vor.regions[region]

            if all(v >= 0 for v in vertices):
                # finite region
                new_regions.append(vertices)
                continue

            # reconstruct a non-finite region
            ridges = all_ridges[p1]
            new_region = [v for v in vertices if v >= 0]

            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    # finite ridge: already in the region
                    continue

                # Compute the missing endpoint of an infinite ridge

                t = vor.points[p2] - vor.points[p1] # tangent
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])  # normal

                midpoint = vor.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = vor.vertices[v2] + direction * radius

                new_region.append(len(new_vertices))
                new_vertices.append(far_point.tolist())

            # sort region counterclockwise
            vs = np.asarray([new_vertices[v] for v in new_region])
            c = vs.mean(axis=0)
            angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]

            # finish
            new_regions.append(new_region.tolist())
        except KeyError:
            counter = counter + 1
            #print('Oops {}'.format(counter))

    return new_regions, np.asarray(new_vertices)


def plot_heatmap(prefix, feature='asymmetry1', vmin=0, vmax=1, resolution=512, rows=4, cols=4):
    
    #Inputs
    #----------
    merged_ft = pd.read_csv('features_{}.csv'.format(prefix))
    string = feature
    leveler = merged_ft[string]
    t_min = vmin
    t_max = vmax
    ires = resolution
    
    #Building points and color schemes
    #----------
    zs = ma.masked_invalid(merged_ft[string])
    zs = ma.masked_where(zs <= t_min, zs)
    zs = ma.masked_where(zs >= t_max, zs)
    to_mask = ma.getmask(zs)
    zs = ma.compressed(zs)

    xs = ma.compressed(ma.masked_where(to_mask, merged_ft['X'].astype(int)))
    ys = ma.compressed(ma.masked_where(to_mask, merged_ft['Y'].astype(int)))
    points = np.zeros((xs.shape[0], 2))
    points[:, 0] = xs
    points[:, 1] = ys
    vor = Voronoi(points)

    #Plot
    #----------
    fig = plt.figure(figsize = (12, 10))
    regions, vertices = voronoi_finite_polygons_2d(vor)
    my_map = cm.get_cmap('viridis')
    norm = mpl.colors.Normalize(t_min, t_max, clip=True)
    mapper = cm.ScalarMappable(norm=norm, cmap=cm.viridis)

    test = 0
    p2 = 0
    counter = 0
    for i in range(0, points.shape[0]-1):
        try:
            polygon = vertices[regions[p2]]
            point1 = Point(points[test, :])
            poly1 = Polygon(polygon)
            check = poly1.contains(point1)
            if check:
                plt.fill(*zip(*polygon), color=my_map(norm(zs[test])), alpha=0.7)
                p2 = p2 + 1
                test = test + 1
            else:
                p2 = p2
                test = test + 1
        except IndexError:
            print('Index mismatch possible.')

    mapper.set_array(10)
    plt.colorbar(mapper)
    plt.xlim(0, ires*cols)
    plt.ylim(0, ires*rows)

    print('Plotted {} heatmap successfully.'.format(prefix))
    fig.savefig('heatmap_{}.png'.format(prefix), bbox_inches='tight')
    
    
def plot_scatterplot(prefix, feature='asymmetry1', vmin=0, vmax=1, resolution=512, rows=4, cols=4):
    
    #Inputs
    #----------
    merged_ft = pd.read_csv('features_{}.csv'.format(prefix))
    string = feature
    leveler = merged_ft[string]
    t_min = vmin
    t_max = vmax
    ires = resolution

    norm = mpl.colors.Normalize(t_min, t_max, clip=True)
    mapper = cm.ScalarMappable(norm=norm, cmap=cm.viridis)

    zs = ma.masked_invalid(merged_ft[string])
    zs = ma.masked_where(zs <= t_min, zs)
    zs = ma.masked_where(zs >= t_max, zs)
    to_mask = ma.getmask(zs)
    zs = ma.compressed(zs)
    xs = ma.compressed(ma.masked_where(to_mask, merged_ft['X'].astype(int)))
    ys = ma.compressed(ma.masked_where(to_mask, merged_ft['Y'].astype(int)))

    fig = plt.figure(figsize=(12, 10))
    plt.scatter(xs, ys, c=zs, s=10)
    mapper.set_array(10)
    plt.colorbar(mapper)
    plt.xlim(0, ires*cols)
    plt.ylim(0, ires*rows)
    
    print('Plotted {} scatterplot successfully.'.format(prefix))
    fig.savefig('scatter_{}.png'.format(prefix), bbox_inches='tight')
    

def plot_trajectories(prefix, resolution=512, rows=4, cols=4):
    
    merged = pd.read_csv('msd_{}.csv'.format(prefix))
    particles = int(max(merged['Track_ID']))
    ires = resolution

    fig = plt.figure(figsize=(12, 12))
    for part in range(0, particles):
        x = merged[merged['Track_ID']==part]['X']
        y = merged[merged['Track_ID']==part]['Y']
        plt.plot(x, y, color='k', alpha=0.7)

    plt.xlim(0, ires*cols)
    plt.ylim(0, ires*rows)
    
    print('Plotted {} trajectories successfully.'.format(prefix))
    fig.savefig('traj_{}.png'.format(prefix), bbox_inches='tight')

    
def plot_histogram(prefix, xlabel='Log Diffusion Coefficient Dist', ylabel='Trajectory Count',
                   fps=100.02, umppx=0.16, frames=651, y_range=100, frame_interval=20, frame_range=100,
                   analysis='log', theta='D'):
    
    merged = pd.read_csv('msd_{}.csv'.format(prefix))
    data = merged
    frame_range=range(frame_interval, frame_range+frame_interval, frame_interval)

    # load data

    # generate keys for legend
    bar = {}
    keys = []
    entries = []
    for i in range(0, len(list(frame_range))):
        keys.append(i)
        entries.append(str(10*frame_interval*(i+1)) + 'ms')

    set_x_limit = False
    set_y_limit = True
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    fig = plt.figure(figsize=(16, 6))

    counter = 0
    for i in frame_range:
        toi = i/fps
        if theta == "MSD":
            factor = 1
        else:
            factor = 4*toi

        if analysis == 'log':
            dist = np.log(umppx*umppx*merged.loc[merged.Frame == i, 'MSDs'].dropna()/factor)
            test_bins = np.linspace(-5, 5, 76)
        else:
            dist = umppx*umppx*merged.loc[merged.Frame == i, 'MSDs'].dropna()/factor
            test_bins = np.linspace(0, 20, 76)

        histogram, test_bins = np.histogram(dist, bins=test_bins)

        # Plot_general_histogram_code
        avg = np.mean(dist)

        plt.rc('axes', linewidth=2)
        plot = histogram
        bins = test_bins
        width = 0.7 * (bins[1] - bins[0])
        center = (bins[:-1] + bins[1:])/2
        bar[keys[counter]] = plt.bar(center, plot, align='center', width=width, color=colors[counter], label=entries[counter])
        plt.axvline(avg, color=colors[counter])
        plt.xlabel(xlabel, fontsize=30)
        plt.ylabel(ylabel, fontsize=30)
        plt.tick_params(axis='both', which='major', labelsize=20)

        counter = counter + 1
        if set_y_limit:
            plt.gca().set_ylim([0, y_range])

        if set_x_limit:
            plt.gca().set_xlim([0, x_range])

        plt.legend(fontsize=20, frameon=False)
    plt.savefig('hist_{}.png'.format(prefix), bbox_inches='tight')
    
    
def plot_particles_in_frame(prefix, x_range=600, y_range=2000):
    
    merged = pd.read_csv('msd_{}.csv'.format(prefix))
    frames = int(max(merged['Frame']))
    framespace = np.linspace(0, frames, frames)
    particles = np.zeros((framespace.shape[0]))
    for i in range(0, frames):
        particles[i] = merged.loc[merged.Frame == i, 'MSDs'].dropna().shape[0]

    fig = plt.figure(figsize=(5, 5))
    plt.plot(framespace, particles, linewidth=4)
    plt.xlim(0, x_range)
    plt.ylim(0, y_range)
    plt.xlabel('Frames', fontsize=20)
    plt.ylabel('Particles', fontsize=20)
    
    plt.savefig('in_frame_{}.png'.format(prefix), bbox_inches='tight')