##############################################
def read_config(cfgfile='XmasShowPi.cfg', debug=False):

    config_data = {}
    outlets = []
    num_tokens = 0
    num_outlets = 0

    with open(cfgfile, mode='r') as f:
        configlines = f.read().splitlines()
    f.close()

    for i in range(0, len(configlines)):
        cline = configlines[i].split("=")

        if cline[0] == 'OUTLET':
            print("Found Outlet:", cline[1])
            outlet_line = cline[1].split(",")
            outlet_cfg = {}

            outlet_cfg['cfgline'] = cline[1]
            outlet_cfg['name'] = outlet_line[0]
            outlet_cfg['GPIO'] = outlet_line[1]

            outlets.append(outlet_cfg)
            num_tokens += 1
            num_outlets += 1

        if cline[0] == 'RF_GPIO':
            print("Found RF Transmitter:", cline[1])
            config_data['RF_GPIO'] = cline[1]
            num_tokens += 1

        if cline[0] == 'RF_FREQ':
            print("Found RF Frequency:", cline[1])
            config_data['RF_FREQ'] = cline[1]
            num_tokens += 1

    if num_tokens < 3:
        print("Missing XmasShowPi configuration information")
        exit(-2)

    config_data['outlets'] = outlets
    config_data['num_outlets'] = num_outlets
    return config_data

####### end read_config
##############################################