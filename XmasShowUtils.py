##############################################
def read_config(cfgfile='XmasShowPi.cfg'):

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
            outlets[num_outlets]['cfgline'] = cline[1]
            outlet_line = cline[1].split(",")
            outlets[num_outlets]['name'] = outlet_line[0]
            outlets[num_outlets]['GPIO'] = outlet_line[1]
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

    config_data['Outlets'] = outlets
    return config_data

####### end read_config
##############################################
