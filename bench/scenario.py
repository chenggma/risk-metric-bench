"""Generate the benchmark's SUMO scenario: a two-road priority intersection.

East-west is the major road (priority); north-south is the minor road whose
drivers must yield. A fraction of minor-road drivers ignores the foe check
(jmIgnoreFoeProb), which produces right-angle conflicts and, in a fraction
of runs, real collisions - SUMO is run with --collision.action warn so
collisions are logged rather than teleported away.

All files are plain XML written by this module; netconvert compiles the
node/edge files into the .net.xml.
"""

import os
import subprocess

NODES = """<nodes>
    <node id="C" x="0" y="0" type="priority"/>
    <node id="W" x="-250" y="0" type="dead_end"/>
    <node id="E" x="250" y="0" type="dead_end"/>
    <node id="S" x="0" y="-250" type="dead_end"/>
    <node id="N" x="0" y="250" type="dead_end"/>
</nodes>
"""

EDGES = """<edges>
    <edge id="WC" from="W" to="C" priority="10" numLanes="1" speed="16.7"/>
    <edge id="CE" from="C" to="E" priority="10" numLanes="1" speed="16.7"/>
    <edge id="EC" from="E" to="C" priority="10" numLanes="1" speed="16.7"/>
    <edge id="CW" from="C" to="W" priority="10" numLanes="1" speed="16.7"/>
    <edge id="SC" from="S" to="C" priority="2" numLanes="1" speed="13.9"/>
    <edge id="CN" from="C" to="N" priority="2" numLanes="1" speed="13.9"/>
    <edge id="NC" from="N" to="C" priority="2" numLanes="1" speed="13.9"/>
    <edge id="CS" from="C" to="S" priority="2" numLanes="1" speed="13.9"/>
</edges>
"""

ROUTES = """<routes>
    <vType id="major" accel="2.6" decel="4.5" sigma="0.6" length="4.5"
           width="2.0" maxSpeed="19" speedFactor="normc(1.0,0.12,0.7,1.4)"
           jmIgnoreJunctionFoeProb="{major_blind_prob}" jmIgnoreFoeSpeed="50"/>
    <vType id="minor" accel="2.6" decel="4.5" sigma="0.8" length="4.5"
           width="2.0" maxSpeed="17" speedFactor="normc(1.05,0.15,0.7,1.5)"
           jmIgnoreFoeProb="{ignore_prob}" jmIgnoreFoeSpeed="50"
           impatience="0.8"/>

    <flow id="we" type="major" begin="0" end="{end}" vehsPerHour="{major_flow}"
          from="WC" to="CE" departSpeed="max"/>
    <flow id="ew" type="major" begin="0" end="{end}" vehsPerHour="{major_flow}"
          from="EC" to="CW" departSpeed="max"/>
    <flow id="sn" type="minor" begin="0" end="{end}" vehsPerHour="{minor_flow}"
          from="SC" to="CN" departSpeed="max"/>
    <flow id="ns" type="minor" begin="0" end="{end}" vehsPerHour="{minor_flow}"
          from="NC" to="CS" departSpeed="max"/>
</routes>
"""

CONFIG = """<configuration>
    <input>
        <net-file value="net.net.xml"/>
        <route-files value="routes.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="{end}"/>
        <step-length value="0.25"/>
    </time>
    <processing>
        <collision.action value="warn"/>
        <collision.check-junctions value="true"/>
        <time-to-teleport value="-1"/>
    </processing>
    <random_number>
        <seed value="{seed}"/>
    </random_number>
</configuration>
"""


def write_scenario(
    outdir,
    end_s=300,
    major_flow=700,
    minor_flow=500,
    ignore_prob=0.30,
    major_blind_prob=0.50,
    netconvert_bin="netconvert",
):
    """Write nodes/edges/routes and compile the network. Returns the dir."""
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "net.nod.xml"), "w") as f:
        f.write(NODES)
    with open(os.path.join(outdir, "net.edg.xml"), "w") as f:
        f.write(EDGES)
    with open(os.path.join(outdir, "routes.rou.xml"), "w") as f:
        f.write(
            ROUTES.format(
                end=end_s,
                major_flow=major_flow,
                minor_flow=minor_flow,
                ignore_prob=ignore_prob,
                major_blind_prob=major_blind_prob,
            )
        )
    subprocess.run(
        [
            netconvert_bin,
            "-n", os.path.join(outdir, "net.nod.xml"),
            "-e", os.path.join(outdir, "net.edg.xml"),
            "-o", os.path.join(outdir, "net.net.xml"),
            "--no-turnarounds",
            "--offset.disable-normalization",
        ],
        check=True,
        capture_output=True,
    )
    return outdir


def write_config(outdir, seed, end_s=300):
    path = os.path.join(outdir, "run_%05d.sumocfg" % seed)
    with open(path, "w") as f:
        f.write(CONFIG.format(end=end_s, seed=seed))
    return path
