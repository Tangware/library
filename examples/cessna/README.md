Cessna: the retracting main landing gear of a Cessna 337, at one-sixth scale, on a desk stand. One gearmotor turns a pinion, a long-radius rack, the output shaft, a clevis at each end, the side tubes, the spring legs and the wheels, from standing on the desk to tucked beside the plate. Four AA cells in the stand power it.

Build it in Tangware Studio, which runs the checks.

The stress build stops at the gear's drive case: the library cannot solve a spherical joint loop under motor torque, so a test checks the teeth by hand instead. The rack is a 60 mm radius sector, not a straight rack and hydraulic actuator: the library meshes gears between turning joints. Lengths from https://github.com/elvarofficial/teardown, `sims/cessna-shared/gear.js`, scaled; the clevis sits wider there to clear the printed forks. Motor and holder: Pololu 3069 and 1159; the motor's maker CAD is downloaded on the first build.
