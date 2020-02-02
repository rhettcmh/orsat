# Configuring ORSAT
## Random configuration
A random configuration of N bodies can be enabled with the **--random** flag.

## Custom configuration
Configurations are located in **configuration/** and can be used at startup of program execution with the flag **--config [id]**, where id is the unique identifier of the configuration. All configurations override:
- Positions
- Velocities
- Masses
- Names
- G (Universal gravitation constant)
- N (number of bodies)

Configurations are defined in a .csv file, which should maintain the structure:
Name | mass (kg) | x (m) | y (m) | z (m) | vx (m/s) | vy (m/s) | vz (m/s)
--- | --- | --- | --- | --- | --- | --- | ---
Body1 | mass | start x | start y | start z | start vx | start vy | start vz

Any new start configuration csv should be referenced in **configuration/settings.toml**, with the following structure, where **[id]** is the unique identifier which will be used to refer to the given configuration.

    [configs.[id]]
    # Description: (optional)
    file = "[configuration_filename].csv"
    G = value of G

Once included, at start of the program, the configuration can be selected using **--config [id]**.