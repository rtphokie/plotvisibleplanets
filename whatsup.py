from pprint import pprint
import numpy as np
from skyfield.api import Loader
from skyfield import almanac
from skyfield.api import load, wgs84
import pytz, datetime
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from skyfield.framelib import ecliptic_frame
from matplotlib.offsetbox import AnchoredText
from pytz import timezone

fontsize_title = 12
fontsize_axis = 12
fontsize_labels = 12
azimuth_shift = 90

ts = load.timescale()

load = Loader('/var/data')
eph = load('de421.bsp')
sun = eph['Sun']
earth = eph['Earth']
bodies = ['Sun', 'Mercury', 'Venus', 'Moon', 'Mars', 'Jupiter Barycenter', 'Saturn Barycenter',
          'Uranus Barycenter', 'Neptune Barycenter']
bodies_label = []
body_color = {'Sun': 'yellow', 'Mercury': 'lightgrey', 'Venus': 'bisque', 'Moon': 'lightgrey', 'Mars': 'coral',
              'Jupiter Barycenter': 'peachpuff',
              'Saturn Barycenter': 'moccasin'}
body_sizes = {'Sun': 30, 'Mercury': 8, 'Venus': 10, 'Moon': 20, 'Mars': 8,
              'Jupiter Barycenter': 12, 'Saturn Barycenter': 11}
body_images = {'Mercury': 'mercury.png', 'Venus': 'venus.png', 'Moon': 'saturn.png', 'Mars': 'mars.png',
               'Jupiter Barycenter': 'jupiter.png', 'Saturn Barycenter': 'saturn.png'}


def whatsup(lat=38.91, lon=-77.04, tzs='notimezonegiven', elevation_m=50,
            location='Washington, D.C.', filename=None,
            date=None, sky='dusk', minutes=60, verbose=False):
    '''
    Note: the Moon and Sun are also included

    :param lat: latitude in degrees
    :param lon: longitude in degrees
    :param location: string to display in the lower left
    :param tz: timezone from https://en.wikipedia.org/wiki/List_of_tz_database_time_zones (default: US/Easetern)
    :param elevation_m: elevation in meters
    :param date: datetime to calculate planet positions (default: today)
    :param sky: dusk or dawn (default: dusk)
    :param minutes: minutes before or after sunset (default: 60)
    :param verbose: you know what this means (default: False)
    :return: dictionaries of visible planets above and below the horizon.
    '''
    if sky not in ['dusk', 'dawn']:
        raise ValueError(f"expected one of 'dusk', 'dawn', got {sky}")

    observer = earth + wgs84.latlon(lat, lon, elevation_m=elevation_m)
    if date is None:
        dt = datetime.datetime.now(pytz.utc)
    elif type(date) == datetime.datetime:
        dt = date
    else:
        raise TypeError(f"expected date to be of type datetime.datetime, got {type(date)}")
    t0 = ts.tt(dt.year, dt.month, dt.day, 12, 0)  # ensure we pick the right day (UTC) by starting at noon
    t1 = t0 + 1.5
    eastern = timezone(tzs)
    dt = t0.utc_datetime()

    if minutes >= 60:
        deltastr = f"{minutes / 60:.1f} hour".replace('.0', '')
        if minutes > 60:
            deltastr += 's'
    else:
        deltastr = f"{minutes} minutes"

    title = f'visible planets {deltastr} '
    if sky == 'dawn':
        times, _ = almanac.find_risings(observer, eph['Sun'], t0, t1)

        targettime = times[0] - (minutes / 1400)  # minutes before sunrise
        title += 'before sunrise'
    elif sky == 'dusk':
        times, _ = almanac.find_settings(observer, eph['Sun'], t0, t1)
        targettime = times[0] + (minutes / 1400)  # minutes after sunset
        title += 'after sunset'
    else:
        raise ValueError(f"expected on of dawn or dusk, got {sky}")

    azs = []
    alts = []
    labels = []
    results = {}
    above_10 = []
    below_trees = []
    below_horizon = []
    if verbose:
        eastern = timezone('US/Eastern')
        dt = targettime.utc_datetime()
        dt = dt.astimezone(eastern)
        print(f"from {location} {dt.strftime('%c')}({minutes} min from {sky})")
        print(f"{'body':>8} {'alt':>6} {'az':>6}")
    for body in body_color.keys():
        # determine altitude and azimuth of each planet from the observers location at the target time
        apparent_observation = observer.at(targettime).observe(eph[body]).apparent()
        alt, az, d = apparent_observation.altaz()
        azs.append(az.degrees)
        alts.append(alt.degrees)
        labels.append(body.replace(' Barycenter', ''))

        if alt.degrees > 10:
            above_10.append(labels[-1].replace('Moon', 'the Moon'))
        elif alt.degrees > 0:
            below_trees.append(labels[-1].replace('Moon', 'the Moon'))
        elif alt.degrees < 0:
            below_horizon.append(labels[-1].replace('Moon', 'the Moon'))
        else:
            raise ValueError(f"unexpected altitude {alt.degrees} degrees")

        if verbose:
            print(f"{labels[-1]:>8}", end=' ')
            print(f"{alt.degrees:6.2f}", end=' ')
            print(f"{azimuth_to_compass(az.degrees):3} {az.degrees:6.2f}", end=' ')
            print()
        results[labels[-1]] = {'altitude': alt.degrees, 'azimuth': az.degrees}
    targettime_dt = targettime.astimezone(timezone(tzs))
    attribution_text = f"from {location} ({lat:.1f}, {lon:.1f}) at {targettime_dt.strftime('%-I:%M %p')} on {targettime_dt.strftime('%Y-%m-%d')}"
    if filename is None:
        filename = f'{sky}.png'
    plotit(alts, azs, body_color.values(), labels, body_sizes.values(), title, filename,
           attribution_text=attribution_text)
    return results, max(alts), above_10, below_trees, below_horizon


def plotit(alts, azs, colors, labels, scales, title, filename, dotscalefator=4, attribution_text=None,
           treelineband=True):
    plt.clf()
    plt.close()
    fig, ax = plt.subplots(1, 1)
    ax.set_facecolor((60 / 255, 60 / 255, 60 / 255))
    adjustaxis(ax, max(alts))

    # y axis
    ytop = max(max(alts) + 20, 20)
    yticks = [0, 10]
    ytick_labels = ['horizon', 'treeline']
    for alt in alts:
        if alt > 0:
            deltas = []
            for prevalt in yticks:
                deltas.append(abs(alt - prevalt))
            if min(deltas) >= 3:
                yticks.append(round(alt))
                ytick_labels.append(f"{round(alt)}º")

    ax.set_yticks(yticks)
    ax.set_yticklabels(ytick_labels)
    ax.set_ylabel('altitude')
    plt.tick_params(axis='y', which='major', labelsize=fontsize_axis)

    # mark planets

    x = [i - azimuth_shift for i in azs]  # shift azimuths 90º to center on east instead of north
    ax.scatter(x, alts, c=colors, s=[i * dotscalefator for i in scales], alpha=1, edgecolors='grey')

    # label planets
    label_planets(alts, ax, azs, labels)

    if treelineband:
        ax.axhspan(0, 10, alpha=0.2, color='grey', zorder=1)
    plt.axhline(y=10, color='g', linestyle='-')
    plt.axhline(y=0, color='sienna', linestyle='-')
    ax.axhspan(-15, 0, alpha=1.0, color=(111 / 255, 78 / 255, 55 / 255), zorder=0)
    if title is not None and len(title) > 0:
        plt.title(title, fontsize=fontsize_title)

    plt.grid(which='major', color=(90 / 255, 90 / 255, 90 / 255), ls=':')
    plt.ylim([-15, ytop + 15])
    plt.xlim([-90, 270])
    # plt.xlim([0, 360])

    if attribution_text is not None and type(attribution_text) is str:
        if ' PM ' in attribution_text:
            xpos=0.02
            ha='left'
        else:
            xpos=0.98
            ha = 'right'
        ax.text(xpos, 0, attribution_text, transform=ax.transAxes, ha=ha, va='bottom',
                style='italic', color='lightgrey', fontsize=fontsize_axis / 2)

    plt.savefig(filename, dpi=300, bbox_inches='')


def adjustaxis(ax, maxalt):
    ax.tick_params(axis='both', labelsize=12)

    # x axis
    ticks = [-180, -90, 0, 90, 180]
    ax.set_xticks(ticks)
    ax.set_xticklabels([' ', 'N', 'E', 'S', 'W'], fontsize=8)
    plt.tick_params(axis='x', which='major', labelsize=fontsize_axis)


def label_planets(alts, ax, azs, labels):
    seenalts = []
    for i, txt in enumerate(labels):
        fontsize = fontsize_labels
        color = 'white'
        txt = txt.replace(' Barycenter', '')
        if alts[i] <= 10:
            fontsize *= .8
            color = 'darkgrey'
        seenalts.append(alts[i])
        diffs = []
        altdeltas = [abs(alts[i] - x) for x in seenalts]
        if len(altdeltas) > 1:
            closestalt = min(altdeltas[:-1])
        else:
            closestalt = 99999
        # print(altdeltas, closestalt)
        if closestalt >= 10 and azs[i] < 0:
            ax.annotate(txt, (azs[i] - 45, alts[i]), ha='right', color=color, fontsize=fontsize)
        else:
            ax.annotate(txt, (azs[i] - 80, alts[i]), ha='left', color=color, fontsize=fontsize)
        seenalts.append(alts[i])


def moon_phase(apparent_observation, hour_before_sunrise, observer):
    apparent_observation_sun = observer.at(hour_before_sunrise).observe(eph['Sun']).apparent()
    _, slon, _ = apparent_observation_sun.frame_latlon(ecliptic_frame)
    _, mlon, _ = apparent_observation.frame_latlon(ecliptic_frame)
    phase = (mlon.degrees - slon.degrees) % 360.0


def getImage(path):
    img = OffsetImage(plt.imread(path, format="png"), zoom=.05)
    return img


def azimuth_to_compass(az):
    """
    Converts an azimuth angle to a compass direction.

    Parameters
    ----------
    az : float
        The azimuth angle in degrees (0-360).

    Returns
    -------
    str
        The compass direction.
    """
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    num_directions = len(directions)

    # Calculate the index of the closest direction
    idx = round(az / (360 / num_directions)) % num_directions

    return directions[idx]

# Cleanups:
# 1. Changed variable names to comply with PEP8 standard.
# 2. Removed debugging statements.
# 3. Improved readability by adding blank lines, docstring, and comments.
# 4. Changed parameter name to `az` for brevity.
# 5. Used tuple unpacking to extract the list length.
# 6. Used the `round` function to calculate the index instead of int and modulo.
# 7. Removed redundant parentheses in the return statement.
