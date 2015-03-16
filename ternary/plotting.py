import math

import matplotlib
import matplotlib.pyplot as pyplot
from matplotlib.lines import Line2D

from hexagonal_heatmap import hex_coordinates

"""Matplotlib Ternary plotting utility."""

# # Constants ##

SQRT3OVER2 = math.sqrt(3) / 2.

## Default colormap, other options here: http://www.scipy.org/Cookbook/Matplotlib/Show_colormaps
DEFAULT_COLOR_MAP = pyplot.get_cmap('jet')

## Helpers ##

def unzip(l):
    return zip(*l)

def normalize(xs):
    """Normalize input list."""
    s = float(sum(xs))
    return [x / s for x in xs]

## Ternary Projections ##

def project_point(p):
    """Maps (x,y,z) coordinates to planar-simplex."""
    a = p[0]
    b = p[1]
    c = p[2]
    #x = 0.5 * (2 * b + c)
    x = b + c/2.
    y = SQRT3OVER2 * c
    return (x, y)

def project(s):
    """Maps (x,y,z) coordinates to planar-simplex."""
    # Is s an appropriate sequence or just a single point?
    try:
        return unzip(map(project_point, s))
    except TypeError:
        return project_point(s)
    except IndexError:  # for numpy arrays
        return project_point(s)

## Boundary, Gridlines, Sizing ##

def resize_drawing_canvas(ax, scale):
    """Makes sure the drawing surface is large enough to display projected content."""
    ax.set_ylim((-0.05 * scale, .90 * scale))
    ax.set_xlim((-0.05 * scale, 1.05 * scale))

def draw_line(ax, p1, p2, **kwargs):
    ax.add_line(Line2D((p1[0], p2[0]), (p1[1], p2[1]), **kwargs))

def draw_horizontal_line(ax, steps, i,   **kwargs):
    p1 = project_point((0, steps-i, i))
    p2 = project_point((steps-i, 0, i))
    draw_line(ax, p1, p2, **kwargs)

def draw_left_parallel_line(ax, steps, i,  **kwargs):
    p1 = project_point((0, i, steps-i))
    p2 = project_point((steps-i, i, 0))
    draw_line(ax, p1, p2, **kwargs)

def draw_right_parallel_line(ax, steps, i, **kwargs):
    p1 = project_point((i, steps-i, 0))
    p2 = project_point((i, 0, steps-i))
    draw_line(ax, p1, p2, **kwargs)

def draw_boundary(scale=1.0, ax=None, **kwargs):
    """Plots the boundary of the simplex. Creates and returns matplotlib axis if none given."""
    if not ax:
        ax = pyplot.subplot()
    scale = float(scale)
    resize_drawing_canvas(ax, scale)
    draw_horizontal_line(ax, scale, 0, **kwargs)
    draw_left_parallel_line(ax, scale, 0, **kwargs)
    draw_right_parallel_line(ax, scale, 0, **kwargs)
    return ax

def draw_gridlines(steps=10, ax=None, **kwargs):
    """Plots grid lines excluding boundary. Creates and returns matplotlib axis if none given."""
    if not ax:
        ax = pyplot.subplot()
    resize_drawing_canvas(ax, steps)
    ## Draw lines
    # Parallel to horizontal axis
    for i in range(1, steps):
        draw_horizontal_line(ax, steps, i, **kwargs)

    # Parallel to left and right axes
    for i in range(1, steps+1):
        draw_left_parallel_line(ax, steps, i, **kwargs)
        draw_right_parallel_line(ax, steps, i, **kwargs)

    return ax

## Curve Plotting ##

def plot(t, steps=1., ax=None, **kwargs):
    """Plots trajectory points where each point satisfies x + y + z = steps. First argument is a list or numpy array of tuples of length 3."""
    if not ax:
        ax = pyplot.subplot()
    xs, ys = project(t)
    ax.plot(xs, ys, **kwargs)
    return ax


## Heatmaps##

def simplex_points(steps=100, boundary=True):
    """Systematically iterate through a lattice of points on the 2 dimensional
    simplex."""
    start = 0
    if not boundary:
        start = 1
    for x1 in range(start, steps + (1 - start)):
        for x2 in range(start, steps + (1 - start) - x1):
            x3 = steps - x1 - x2
            yield (x1, x2, x3)


def colormapper(x, a=0, b=1, cmap=None):
    """Maps color values to [0,1] and obtains rgba from the given color map for triangle coloring."""
    if not cmap:
        cmap = DEFAULT_COLOR_MAP
    if b - a == 0:
        rgba = cmap(0)
    else:
        rgba = cmap((x - a) / float(b - a))
    #rgba = numpy.array(rgba)
    #rgba = rgba.flatten()
    hex_ = matplotlib.colors.rgb2hex(rgba)
    return hex_


def triangle_coordinates(i, j, alt=False):
    """Returns the ordered coordinates of the triangle vertices for i + j + k = N. Alt refers to the averaged triangles;
    the ordinary triangles are those with base  parallel to the axis on the lower end (rather than the upper end)"""
    # N = i + j + k
    if not alt:
        return [(i / 2. + j, i * SQRT3OVER2), (i / 2. + j + 1, i * SQRT3OVER2),
                (i / 2. + j + 0.5, (i + 1) * SQRT3OVER2)]
    else:
        # Alt refers to the inner triangles not covered by the default case
        return [(i/2. + j + 1, i * SQRT3OVER2), (i/2. + j + 1.5, (i + 1) * SQRT3OVER2), (i/2. + j + 0.5, (i + 1) * SQRT3OVER2)]

def heatmap_hexagonal(d, steps, cmap_name=None, boundary=True, ax=None, scientific=False, min_max_scale=None):
    """Plots values in the dictionary d as a heatmap. d is a dictionary of (i,j) --> c pairs where N = steps = i + j + k. Uses hexagonals for heatmap."""
    if not ax:
        ax = pyplot.subplot()
    if not cmap_name:
        cmap = DEFAULT_COLOR_MAP
    else:
        cmap = pyplot.get_cmap(cmap_name)
    if min_max_scale is None:
        a = min(d.values())
        b = max(d.values())
    else:
        a = min_max_scale[0]
        b = min_max_scale[1]
    # Color data triangles.

    for k, v in d.items():
        i, j = k
        vertices = hex_coordinates(i, j, steps)
        if vertices is not None:
            x, y = unzip(vertices)
            color = colormapper(d[i, j], a, b, cmap=cmap)
            ax.fill(x, y, facecolor=color, edgecolor=color)

    # Colorbar hack
    # http://stackoverflow.com/questions/8342549/matplotlib-add-colorbar-to-a-sequence-of-line-plots
    sm = pyplot.cm.ScalarMappable(cmap=cmap, norm=pyplot.Normalize(vmin=a, vmax=b))

    # Fake up the array of the scalar mappable. Urgh...
    sm._A = []
    cb = pyplot.colorbar(sm, ax=ax, format='%.4f')
    cb.locator = matplotlib.ticker.LinearLocator(numticks=7)
    if scientific:
        cb.formatter = matplotlib.ticker.ScalarFormatter()
        cb.formatter.set_powerlimits((0, 0))
    cb.update_ticks()
    return ax

def heatmap_triangular(d, steps, cmap_name=None, boundary=True, ax=None, scientific=False):
    """Plots values in the dictionary d as a heatmap. d is a dictionary of (i,j) --> c pairs where N = steps = i + j + k. Uses triangles for heatmap and blends surrounding triangles to fill the unspecified triangles."""
    if not ax:
        ax = pyplot.subplot()
    if not cmap_name:
        cmap = DEFAULT_COLOR_MAP
    else:
        cmap = pyplot.get_cmap(cmap_name)
    a = min(d.values())
    b = max(d.values())
    # Color data triangles.
    for k, v in d.items():
        i, j = k
        vertices = triangle_coordinates(i,j)
        x,y = unzip(vertices)
        color = colormapper(d[i,j],a,b,cmap=cmap)
        ax.fill(x, y, facecolor=color, edgecolor=color)
    # Color smoothing triangles.
    offset = 0
    if not boundary:
        offset = 1
    for i in range(offset, steps+1-offset):
        for j in range(offset, steps -i -offset):
            try:
                alt_color = (d[i,j] + d[i, j + 1] + d[i + 1, j])/3.
                color = colormapper(alt_color, a, b, cmap=cmap)
                vertices = triangle_coordinates(i,j, alt=True)
                x,y = unzip(vertices)
                pyplot.fill(x, y, facecolor=color, edgecolor=color)
            except KeyError:
                # Allow for some portions to have no color, such as the boundary
                pass
    # Colorbar hack
    # http://stackoverflow.com/questions/8342549/matplotlib-add-colorbar-to-a-sequence-of-line-plots
    sm = pyplot.cm.ScalarMappable(cmap=cmap, norm=pyplot.Normalize(vmin=a, vmax=b))
    # Fake up the array of the scalar mappable. Urgh...
    sm._A = []
    cb = pyplot.colorbar(sm, ax=ax, format='%.3f')
    if scientific:
        cb.formatter = matplotlib.ticker.ScalarFormatter()
        cb.formatter.set_powerlimits((0, 0))
        cb.update_ticks()
    return ax

def heatmap(*args, **kwargs):
    try:
        style = kwargs['style']
    except KeyError:
        style = "triangular"
    finally:
        del kwargs['style']
        if style is None:
            style = "triangular"
    style = style.lower()
    if style.startswith('tri'):
        return heatmap_triangular(*args, **kwargs)
    if style.startswith('hex'):
        return heatmap_hexagonal(*args, **kwargs)

## Convenience Functions ##

def plot_heatmap(func, steps=40, boundary=True, cmap_name=None, ax=None, style=None):
    """Computes func on heatmap coordinates and plots heatmap. In other words, computes the function on sample points of the simplex (normalized points) and creates a heatmap from the values."""
    d = dict()
    for x1, x2, x3 in simplex_points(steps=steps, boundary=boundary):
        d[(x1, x2)] = func(normalize([x1, x2, x3]))
    ax = heatmap(d, steps, cmap_name=cmap_name, ax=ax, style=style)
    return ax

def plot_multiple(trajectories, linewidth=2.0, ax=None):
    """Plots multiple trajectories and the boundary."""
    if not ax:
        ax = pyplot.subplot()
    for t in trajectories:
        plot(t, linewidth=linewidth, ax=ax)
    draw_boundary(ax=ax)
    return ax
