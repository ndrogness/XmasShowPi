#!/usr/bin/env python3

import time
import busio
import board
import digitalio
import random

# Globals
RS_CODE_DEBUG = False
COLOR_LUT = {
    'RED': (0xff, 0x00, 0x00),
    'GREEN': (0x00, 0xff, 0x00),
    'BLUE': (0x00, 0x00, 0xff),
    'WHITE': (0xff, 0xff, 0xff)
}
TLC_LOADED = False
tlc5947 = None
RSNEOPIXEL_LOADED = False
rsneopixel = None


##########################################################
class Sequence:

    def __init__(self, sequence_type, cfgopts, output_names):

        self.SequenceType = sequence_type
        self.IsOn = False
        self.IsEnabled = False
        self.outputs = []
        self.num_outputs = 0
        self.CfgOptions = {}
        self.signal_index = []
        self.signal_last = []  # last signal level
        self.num_signals = 0
        self.signal_data_len = 0

        if cfgopts is None or len(cfgopts) < 4:
            cfgopts = ['index:0', 'on_at:eq8', 'off_at:lt8', '', 'Out1']

        for copt in cfgopts:
            # print('Sequence Option:', copt)
            okey, oval = copt.split(":")
            self.CfgOptions[okey] = oval

        # Get the signals indices from the cfg fidelity

        if self.SequenceType == 'Audio':
            try:
                import RogyAudio

                ra_signals = RogyAudio.Signals()

                self.signal_data_len = len(ra_signals.fidelities)
                for i in range(0, len(ra_signals.fidelities)):
                    if ra_signals.fidelities[i] == self.CfgOptions['index']:
                        self.signal_index.append(i)
                        self.signal_last.append(0)
                        self.num_signals += 1

            except ImportError:
                print('Cant find RogyAudio module, needed for sequence type Audio')
                exit(-1)

        else:
            self.signal_data_len = 0
            for i in self.CfgOptions['index'].split("&"):
                self.signal_index.append(int(i))
                self.signal_last.append(0)
                self.num_signals += 1

        # When to turn on
        if 'on_at' not in self.CfgOptions:
            print("Sequence missing on_at value:", cfgopts)
            return
        self.on_at = {self.CfgOptions['on_at'][0:2]: int(self.CfgOptions['on_at'][2:])}

        # When to turn off
        if 'off_at' not in self.CfgOptions:
            print("Sequence missing off_at value:", cfgopts)
            return
        self.off_at = {self.CfgOptions['off_at'][0:2]: int(self.CfgOptions['off_at'][2:])}


        # Set Options for this sequence, if any specified
        #self.options = {}
        #_options_list = seq_items[3].split("&")
        #if len(_options_list) >= 2:

        #    for i in range(0, len(_options_list)):
        #        _option = _options_list[i].split(":")
        #        self.options[_option[0]] = _option[1]

        # Build participating Outputs
        if 'outputs' not in self.CfgOptions:
            print("Sequence missing outputs:", cfgopts)
            return

        for _output in self.CfgOptions['outputs'].split("&"):
            if _output not in output_names:
                print("Warning: Output not found in available outputs: ", _output)
                continue
            self.outputs.append(_output)
            self.num_outputs += 1

        if self.num_outputs > 0:
            self.IsEnabled = True

    def __str__(self):
        return self.CfgOptions

    def _check_trigger(self, signal_data, pos, check_vals):

        #for oper, val in self.on_at.items():
        for oper, val in check_vals.items():
            ival = int(val)
            if oper == 'lt' and signal_data[pos] < ival:
                return True
            elif oper == 'le' and signal_data[pos] <= ival:
                return True
            elif oper == 'eq' and signal_data[pos] == ival:
                return True
            elif oper == 'gt' and signal_data[pos] > ival:
                return True
            elif oper == 'ge' and signal_data[pos] >= ival:
                return True

        return False

    def should_trigger(self, signal_data):

        # if RS_CODE_DEBUG:
        #     print("Should trigger called with signal data:", signal_data, self.num_signals)

        on_status = False
        off_status = False
        for i in range(0, self.num_signals):
            pos = self.signal_index[i]

            # off_status |= self._check_trigger(signal_data, pos, self.off_at)
            # if self.IsOn is False:
            #     on_status |= self._check_trigger(signal_data, pos, self.on_at)
            off_status |= self._check_trigger(signal_data, pos, self.off_at)
            on_status |= self._check_trigger(signal_data, pos, self.on_at)

        '''
        if on_status is True and off_status is False:
            return True
        elif on_status is True and off_status is True:
            return False
        elif on_status is False and off_status is True:
            return False
        elif on_status is False and off_status is False:
            return False
        else:
            print('Error in branch logic', self.IsOn, on_status, off_status)
            return False
        '''
        if off_status is True:
            return False
        elif self.IsOn is True and off_status is True:
            return False
        elif self.IsOn is True and off_status is False:
            return True
        elif self.IsOn is False and on_status is True:
            return True
        elif self.IsOn is False and on_status is False:
            return False
        else:
            print('Error in branch logic', self.IsOn, on_status, off_status)
            return False

### End Sequence class
##########################################################


##########################################################
class AlwaysTrigger(Sequence):

    def __init__(self, name, sequence_type, sequence_cfg, output_names):
        super().__init__(sequence_type, sequence_cfg, output_names)
        self.name = name
        self.cur_outputs_on = []
        self.cur_outputs_off = []

    def check(self, signal_data, seq_debug=False):
        self.cur_outputs_on.clear()
        self.cur_outputs_off.clear()

        self.cur_outputs_on = self.outputs[:]
        self.cur_outputs_off.clear()

        if seq_debug is True:
            debug_msg = '{0} check: AlwaysOn -> on: {1}'.format(self.name, self.cur_outputs_on)
            print(signal_data, debug_msg)

        self.IsOn = True
        return True


### End Toggle class
##########################################################


##########################################################
class Toggle(Sequence):

    def __init__(self, name, sequence_type, sequence_cfg, output_names):
        super().__init__(sequence_type, sequence_cfg, output_names)
        self.name = name
        self.cur_outputs_on = []
        self.cur_outputs_off = []

    def check(self, signal_data, seq_debug=False):
        self.cur_outputs_on.clear()
        self.cur_outputs_off.clear()

        if self.should_trigger(signal_data):
            self.cur_outputs_on = self.outputs[:]
            self.cur_outputs_off.clear()

            if seq_debug is True:
                debug_msg = '{0} check: toggle -> on: {1}'.format(self.name, self.cur_outputs_on)
                print(signal_data, debug_msg)

            self.IsOn = True
            return True

        else:
            self.cur_outputs_on.clear()
            self.cur_outputs_off = self.outputs[:]

            # Need to shut stuff off
            if self.IsOn is True:
                if seq_debug is True:
                    debug_msg = '{0} check: toggle -> off: {1}'.format(self.name, self.cur_outputs_off)
                    print(signal_data, debug_msg)

                self.IsOn = False
                return True
            else:
                if seq_debug is True:
                    debug_msg = '{0} check: no action, already off'.format(self.name)
                    print(signal_data, debug_msg)

                return False

### End Toggle class
##########################################################


##########################################################
class Cycle(Sequence):

    def __init__(self, name, sequence_type, sequence_cfg, output_names):
        super().__init__(sequence_type, sequence_cfg, output_names)
        self.name = name
        self.cur_outputs_on = []
        self.cur_outputs_off = []
        self.next_output_index = 0
        if 'stay_on' not in self.CfgOptions:
            self.CfgOptions['stay_on'] = 'no'

    def check(self, signal_data, seq_debug=False):
        self.cur_outputs_on.clear()
        self.cur_outputs_off.clear()

        if self.should_trigger(signal_data):

            # Loop through all outputs
            for i in range(0, self.num_outputs):
                if self.CfgOptions['stay_on'] == 'yes':
                    if i <= self.next_output_index:
                        self.cur_outputs_on.append(self.outputs[i])
                    else:
                        self.cur_outputs_off.append(self.outputs[i])
                else:
                    if i == self.next_output_index:
                        self.cur_outputs_on.append(self.outputs[i])
                    else:
                        self.cur_outputs_off.append(self.outputs[i])

            self.next_output_index += 1
            if self.next_output_index >= self.num_outputs:
                self.next_output_index = 0

            if seq_debug is True:
                debug_msg = '{0} check: cycle_next -> on: {1}, off: {2}'.format(self.name, self.cur_outputs_on,
                                                                                self.cur_outputs_off)
                print(signal_data, debug_msg)

            self.IsOn = True
            return True

        else:
            # Need to shut stuff off
            if self.IsOn is True:

                if seq_debug is True:
                    debug_msg = '{0} check: cycle_off -> on: {1}, off: {2}'.format(self.name, self.cur_outputs_on,
                                                                                   self.cur_outputs_off)
                    print(signal_data, debug_msg)

                self.IsOn = False
                return True

            else:
                if seq_debug is True:
                    debug_msg = '{0} no action, already off'.format(self.name)
                    print(signal_data, debug_msg)
                return False

### End Toggle class
##########################################################


class RSOutputItem:

    # def __init__(self, cfg, relay_value_on=0, relay_value_off=1, initially_on=False, fire_gpio=True):
    def __init__(self, cfgopts=None):
        self.Name = 'Undefined'
        self.IsEnabled = False
        self.DefaultOn = False
        self.CfgOptions = {}
        if cfgopts is not None:
            for copt in cfgopts:
                # print('Output Option:', copt)
                okey, oval = copt.split(":")
                self.CfgOptions[okey] = oval

        # print(self.CfgOptions)

    @property
    def IsOn(self):
        return self._do_is_on()

    def _do_is_on(self):
        # Overload this method in subclass
        return False

    def _do_turn_on(self):
        # Overload this method in subclass
        pass

    def _do_turn_off(self):
        # Overload this method in subclass
        pass

    def _do_reset(self):
        # Overload this method in subclass
        pass

    def _do_deinit(self):
        # Overload this method in subclass
        pass

    def on(self):
        self._do_turn_on()

    def off(self):
        self._do_turn_off()

    def toggle(self):
        if self.IsOn is True:
            self.off()
        else:
            self.on()

    def reset(self):
        self._do_reset()

    def deinit(self):
        self._do_deinit()


class RSOutputAlwaysOn(RSOutputItem):

    def __init__(self, name, cfgopts):
        super().__init__(cfgopts)
        self.Name = name

        if 'gpio' not in self.CfgOptions:
            print('GPIO pin not specified for output:', name)
            return

        #try:
        rspin = getattr(board, 'D{0}'.format(self.CfgOptions['gpio']))
        self.gpio = digitalio.DigitalInOut(rspin)
        self.gpio.direction = digitalio.Direction.OUTPUT

        self.IsEnabled = True

    def _do_is_on(self):
        if self.IsEnabled is not True:
            return
        # print(self.gpio.value)
        return self.gpio.value

    def _do_turn_on(self):
        if self.IsEnabled is not True:
            return
        self.gpio.value = True

    def _do_turn_off(self):
        if self.IsEnabled is not True:
            return
        self.gpio.value = False

    def _do_reset(self):
        if self.IsEnabled is not True:
            return
        self._do_turn_off()

    def _do_deinit(self):
        if self.IsEnabled is not True:
            return
        self.gpio.deinit()


class RSOutputGpioOnOff(RSOutputItem):

    def __init__(self, name, cfgopts):
        super().__init__(cfgopts)
        self.Name = name

        if 'gpio' not in self.CfgOptions:
            print('GPIO pin not specified')
            return

        #try:
        rspin = getattr(board, 'D{0}'.format(self.CfgOptions['gpio']))
        self.gpio = digitalio.DigitalInOut(rspin)
        self.gpio.direction = digitalio.Direction.OUTPUT

        self.IsEnabled = True

    def _do_is_on(self):
        if self.IsEnabled is not True:
            return
        # print(self.gpio.value)
        return self.gpio.value

    def _do_turn_on(self):
        if self.IsEnabled is not True:
            return
        self.gpio.value = True

    def _do_turn_off(self):
        if self.IsEnabled is not True:
            return
        self.gpio.value = False

    def _do_reset(self):
        if self.IsEnabled is not True:
            return
        self._do_turn_off()

    def _do_deinit(self):
        if self.IsEnabled is not True:
            return
        self.gpio.deinit()


class RSOutputNeoPixel(RSOutputItem):

    def __init__(self, name, cfgopts):
        super().__init__(cfgopts)
        self.Name = name
        self.pixel_indexes = []
        self.pixel_values = []
        self.num_pixels = 0
        self.intensity = .1
        global RSNEOPIXEL_LOADED
        global rsneopixel
        self.pixels = rsneopixel

        self._color_keys = list(COLOR_LUT.keys())
        random.shuffle(self._color_keys)
        # print(self._color_keys)
        self.color = COLOR_LUT[self._color_keys[0]]
        self.color_mode = 'fixed'

        if 'data_pin' not in self.CfgOptions:
            print('NeoPixel data_pin not specified')
            return
        else:
            self.data_pin = getattr(board, 'D{0}'.format(self.CfgOptions['data_pin']))

        if 'num_pixels' not in self.CfgOptions:
            print('NeoPixel num_neopixels not specified')
            return
        else:
            self.num_pixels = int(self.CfgOptions['num_pixels'])

        if 'pixel_indexes' in self.CfgOptions:
            for _pini in self.CfgOptions['pixel_indexes'].split("&"):
                self.pixel_indexes.append(int(_pini))
        else:
            for _pini in range(0, self.num_pixels):
                self.pixel_indexes.append(_pini)

        for _pini in range(0, self.num_pixels):
            self.pixel_values.append(False)


        if 'color' in self.CfgOptions:
            if self.CfgOptions['color'] in COLOR_LUT:
                self.color = COLOR_LUT[self.CfgOptions['color']]

        if 'intensity_perc' not in self.CfgOptions:
            self.intensity = int(self.CfgOptions['intensity_perc']) / 100
            #self.intensity = .01

        if RSNEOPIXEL_LOADED is not True:
            import neopixel

            # latch_pin = getattr(board, 'D{0}'.format(self.CfgOptions['gpio_latch']))
            # spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
            # latch = digitalio.DigitalInOut(latch_pin)
            # tlc5947 = adafruit_tlc5947.TLC5947(spi, latch)

            # for i in range(0, 23):
            #     tlc5947[i] = 0

            # pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, pixel_order=ORDER, auto_write=False)
            self.pixels = neopixel.NeoPixel(self.data_pin, self.num_pixels, brightness=self.intensity,
                                            pixel_order=neopixel.GRB, auto_write=True)


            self.pixels.fill((0, 0, 0))
            # self.pixels.show()

            RSNEOPIXEL_LOADED = True
            #print(self.pixels)
            #self.pixels.deinit()
            #exit(-1)
            rsneopixel = self.pixels

        self.IsEnabled = True
        print("Neopixel loaded:", self.pixel_indexes)

    def _do_is_on(self):
        if self.IsEnabled is not True:
            return
        # print(self.gpio.value)
        _retval = False
        for j in self.pixel_values:
            _retval |= j
        return _retval

    def _do_turn_on(self):
        if self.IsEnabled is not True:
            return

        # print("turning pixels on:",self.pixel_indexes)
        for j in self.pixel_indexes:
            self.pixels[j] = self.color
            self.pixel_values[j] = True


    def _do_turn_off(self):
        if self.IsEnabled is not True:
            return

        #print("turning pixels off:",self.pixels)
        #self.pixels.fill((0, 0, 0))

        ###
        # print("turning pixels on:",self.pixel_indexes)
        for j in self.pixel_indexes:
            # self.pixels[j] = (255, 0, 0)
            self.pixels[j] = (0, 0, 0)
            self.pixel_values[j] = False
        # self.pixels.show()

    def _do_reset(self):
        if self.IsEnabled is not True:
            return
        # self.pixels.fill((0, 0, 0))
        self._do_turn_off()

    def _do_deinit(self):
        if self.IsEnabled is not True:
            return
        global RSNEOPIXEL_LOADED
        if RSNEOPIXEL_LOADED is True:
            self.pixels.deinit()
            RSNEOPIXEL_LOADED = False


class RSOutputTLC5947(RSOutputItem):

    def __init__(self, cfgopts):
        super().__init__(cfgopts)
        self.gpio_enable = None
        global TLC_LOADED
        global tlc5947

        if 'gpio_latch' not in self.CfgOptions:
            print('GPIO Latch pin not specified')
            return


        if TLC_LOADED is not True:
            import adafruit_tlc5947

            if 'gpio_enable' in self.CfgOptions:
                _gpio_enable_pin = getattr(board, 'D{0}'.format(self.CfgOptions['gpio_enable']))
                self.gpio_enable = digitalio.DigitalInOut(_gpio_enable_pin)
                self.gpio_enable.direction = digitalio.Direction.OUTPUT

            latch_pin = getattr(board, 'D{0}'.format(self.CfgOptions['gpio_latch']))
            spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
            latch = digitalio.DigitalInOut(latch_pin)
            tlc5947 = adafruit_tlc5947.TLC5947(spi, latch)

            for i in range(0, 23):
                tlc5947[i] = 0

            self.gpio_enable.value = 1

            TLC_LOADED = True

    def _do_reset(self):
        if self.IsEnabled is not True:
            return
        self.is_active = True
        self._do_turn_off()

    def _do_deinit(self):
        if self.IsEnabled is not True:
            return
        self.is_active = True
        self._do_turn_off()
        if self.gpio_enable is not None:
            self.gpio_enable.value = 0

        global TLC_LOADED
        TLC_LOADED = False


class RSOutputTLC5947Led(RSOutputTLC5947):

    def __init__(self, name, cfgopts):
        super().__init__(cfgopts)
        self.Name = name
        self.intensity = 4
        self.is_active = False
        self.pins = []
        global tlc5947
        self.tlc5947 = tlc5947
        # gpio_latch: 5 | rgb_indexes:0 & 1 & 2 | color: random | color_mode:fixed | intensity_perc: 25

        if 'pin_indexes' not in self.CfgOptions:
            print('Pin indexes not specified')
            return

        for _pini in self.CfgOptions['pin_indexes'].split("&"):
            self.pins.append(int(_pini))

        if 'intensity_perc' in self.CfgOptions:
            self.intensity = (int(self.CfgOptions['intensity_perc']) / 100) * 4

        self.IsEnabled = True

    def _do_is_on(self):
        if self.IsEnabled is not True:
            return False
        # print(self.gpio.value)
        return self.is_active

    def _do_turn_on(self):
        if self.IsEnabled is not True:
            return

        if self.is_active is not True:
            for _pin_index in self.pins:
                self.tlc5947[_pin_index] = int(0xff * self.intensity)

            self.is_active = True

    def _do_turn_off(self):
        if self.IsEnabled is not True:
            return

        if self.is_active is True:
            for _pin_index in self.pins:
                self.tlc5947[_pin_index] = 0
            self.is_active = False


class RSOutputTLC5947Rgb(RSOutputTLC5947):

    def __init__(self, name, cfgopts):
        super().__init__(cfgopts)
        self.Name = name
        self._color_keys = list(COLOR_LUT.keys())
        random.shuffle(self._color_keys)
        # print(self._color_keys)
        self.color = list(COLOR_LUT[self._color_keys[0]])
        self.color_mode = 'fixed'
        self.intensity = 4
        self.is_active = False
        global tlc5947
        self.tlc5947 = tlc5947
        # gpio_latch: 5 | rgb_indexes:0 & 1 & 2 | color: random | color_mode:fixed | intensity_perc: 25

        if 'rgb_indexes' not in self.CfgOptions:
            print('RGB indexes not specified')
            return

        red, green, blue = self.CfgOptions['rgb_indexes'].split("&")
        self.red_index = int(red)
        self.red_pwm = self.tlc5947.create_pwm_out(self.red_index)
        self.blue_index = int(blue)
        self.blue_pwm = self.tlc5947.create_pwm_out(self.blue_index)
        self.green_index = int(green)
        self.green_pwm = self.tlc5947.create_pwm_out(self.green_index)

        if 'color' in self.CfgOptions:
            if self.CfgOptions['color'] in COLOR_LUT:
                self.color = list(COLOR_LUT[self.CfgOptions['color']])

        if 'intensity_perc' in self.CfgOptions:
            self.intensity = (int(self.CfgOptions['intensity_perc']) / 100) * 4
            #print('Intensity:', (int(self.CfgOptions['intensity_perc'])/100)* 4)

        self.IsEnabled = True

    def _do_is_on(self):
        if self.IsEnabled is not True:
            return False
        # print(self.gpio.value)
        return self.is_active

    def _do_turn_on(self):
        if self.IsEnabled is not True:
            return

        if self.is_active is not True:
            self.tlc5947[self.red_index] = int(self.color[0] * self.intensity)
            self.tlc5947[self.green_index] = int(self.color[1] * self.intensity)
            self.tlc5947[self.blue_index] = int(self.color[2] * self.intensity)
            # self.red_pwm.duty_cycle = int(self.color[0] * 256 * (self.intensity/100))
            # self.green_pwm.duty_cycle = int(self.color[1] * 256 * (self.intensity/100))
            # self.blue_pwm.duty_cycle = int(self.color[2] * 256 * (self.intensity/100))
            self.is_active = True
            # print('Turning on', self.Name, self.red_index, self.green_index, self.blue_index)

    def _do_turn_off(self):
        if self.IsEnabled is not True:
            return

        if self.is_active is True:
            self.tlc5947[self.red_index] = 0
            self.tlc5947[self.green_index] = 0
            self.tlc5947[self.blue_index] = 0
            self.is_active = False
            # print('Turning off', self.Name, self.red_index, self.green_index, self.blue_index)


###########################################################################
def init_sequences(sequences, cfg, debug):

    sequence_dict = dict()
    # Build dict of Sequences
    for i in range(0, cfg['cfgoptions']['SEQUENCE']):

        if debug is True:
            print('CFG Sequence (vals,opts):', cfg['SEQUENCE'][i]['vals'], ',', cfg['SEQUENCE'][i]['opts'])

        # OUTPUT=Out1,on_off,RSOutputOnOff|gpio:6&default_on:no
        if cfg['SEQUENCE'][i]['num_vals'] != 3:
            print("Warning! Missing Sequence config values, skipping:", cfg['SEQUENCE'][i]['vals'])
            continue

        seq_dict = {
            'name': cfg['SEQUENCE'][i]['vals'][0],
            'module': cfg['SEQUENCE'][i]['vals'][1],
            'type': cfg['SEQUENCE'][i]['vals'][2]
        }

        if seq_dict['module'] in globals():
            seq_dict['obj'] = globals()[seq_dict['module']](seq_dict['name'],
                                                            seq_dict['type'],
                                                            cfg['SEQUENCE'][i]['opts'],
                                                            cfg['output_names'])

        else:
            print("Warning! Missing RSObject, skipping:", seq_dict['module'])
            continue

        if seq_dict['obj'].IsEnabled is True:
            sequences[seq_dict['name']] = seq_dict

    return True

### End init_sequences
###########################################################################


###########################################################################
def init_outputs(outputs, cfg, debug):

    ouput_dict = dict()
    for i in range(0, cfg['cfgoptions']['OUTPUT']):

        if debug is True:
            print('CFG Output (vals,opts):', cfg['OUTPUT'][i]['vals'], ',', cfg['OUTPUT'][i]['opts'])

        # OUTPUT=Out1,on_off,RSOutputOnOff|gpio:6&default_on:no
        if cfg['OUTPUT'][i]['num_vals'] != 3:
            print("Warning! Missing OUPUT config values, skipping:", cfg['OUTPUT'][i]['vals'])
            continue

        output_dict = {
            'name': cfg['OUTPUT'][i]['vals'][0],
            'module': cfg['OUTPUT'][i]['vals'][1],
            'type': cfg['OUTPUT'][i]['vals'][2]
        }

        if cfg['OUTPUT'][i]['vals'][1] in globals():
            # output_dict['obj'] = globals()[cfg['OUTPUT'][i]['vals'][1]](cfg['OUTPUT'][i]['vals'][0],
            #                                                             cfg['OUTPUT'][i]['opts'])
            output_dict['obj'] = globals()[output_dict['module']](output_dict['name'],
                                                                  cfg['OUTPUT'][i]['opts'])

        else:
            print("Warning! Missing RSObject, skipping:", cfg['OUTPUT'][i]['vals'][1])
            continue

        # Add output to available output names, unless it is a status output
        if output_dict['type'] != 'sequencer_status':
            cfg['output_names'].append(output_dict['name'])

        outputs[cfg['OUTPUT'][i]['vals'][0]] = output_dict
        # print(outputs[cfg['OUTPUT'][i]['vals'][0]]['obj'].IsOn)

    return True

### End init_outputs
###########################################################################


#################################################################
def read_config(cfgdata, cfgfile='RogySequencer.cfg', debug=False):

    # Defaults

    cfgdata['OUTPUT'] = []
    cfgdata['output_names'] = []
    cfgdata['SEQUENCE'] = []
    cfgdata['DEBUG'] = []

    # Available cfg options and occuranc
    cfgoptions = {
        'OUTPUT': 0,
        'SEQUENCE': 0,
        'DEBUG': 0
    }

    num_tokens = 0

    with open(cfgfile, mode='r') as f:
        configlines = f.read().splitlines()
    f.close()

    for i in range(0, len(configlines)):
        cline = configlines[i].split("=")

        if cline[0] not in cfgoptions:
            continue

        cfgoptions[cline[0]] += 1

        cline_opts = cline[1].split("|")
        cline_vals = cline_opts[0].split(",")
        cline_opts = cline_opts[1:]
        # cline_dict = {'cfgline': cline[1], 'num_vals': len(cline_vals), 'vals': cline_vals}
        cline_dict = {'num_vals': len(cline_vals), 'vals': cline_vals, 'num_opts': len(cline_opts), 'opts': cline_opts}
        if debug is True:
            print('Found CFG Token:', cline[0], '->', cline[1])
        cfgdata[cline[0]].append(cline_dict)

        num_tokens += 1

    if num_tokens < 3:
        print("Missing RogySequencer configuration information")
        return False

    cfgdata['cfgoptions'] = cfgoptions
    return True

####### end read_config
##############################################


class Sequencer:

    def __init__(self, cfgfile='RogySequencer.cfg', outputs_enable=True, debug=False):

        self.cfgfile = cfgfile
        self.outputs_enable = outputs_enable
        self.debug = debug
        self.history = []
        self.errs = 0
        self.error_dict = {'time': '', 'data': []}
        self.cfg = dict()
        retval = read_config(self.cfg, self.cfgfile, self.debug)
        if self.cfg['cfgoptions']['DEBUG'] > 0:
            if self.cfg['DEBUG'][0]['vals'][0] == 'ON':
                self.debug = True

        self.rsoutputs = dict()
        retval &= init_outputs(self.rsoutputs, self.cfg, self.debug)

        self.rssequences = dict()
        retval &= init_sequences(self.rssequences, self.cfg, self.debug)

        self.valid = retval
        if RS_CODE_DEBUG:
            print(self.rssequences)

    def check(self, signal_data, delay=0):

        debug_msg = ''
        sequence_hit_counter = 0

        if RS_CODE_DEBUG:
            print(signal_data, '****** Begin Signal Processing ******')
        # for sname, sobj in sequences.items():
        for sname, sdict in self.rssequences.items():
            '''if sobj.check(signal_data, seq_debug=cfg['debug']):
            if delay > 0:
                time.sleep(delay)

                for s_outlet in range(0, len(sobj.outlets)):
                    if sobj.outlets[s_outlet] in outlets:
                        outlets[sobj.outlets[s_outlet]].on()
            else:
                for s_outlet in range(0, len(sobj.outlets)):
                    if sobj.outlets[s_outlet] in outlets:
                        outlets[sobj.outlets[s_outlet]].off()
            '''

            #did_hit = sobj.check(signal_data, seq_debug=cfg['debug'])

            sobj = sdict['obj']
            if len(signal_data) != sobj.signal_data_len:
                print(len(signal_data), '<>', sobj.num_signals)

            do_process_sequence = sobj.check(signal_data, RS_CODE_DEBUG)
            if do_process_sequence is not True:
                continue

            sequence_hit_counter += 1
            # print("firing", sobj.cur_outlets_on)

            if self.debug is True:
                if len(sobj.cur_outputs_on) > 0:
                    debug_msg += ', ' + str(sname) + '-> ('

            # for s_output in range(0, len(sobj.outputs)):
            for s_output in sobj.outputs:

                # Is Output in dict of outputs
                # if sobj.outlets[soindex] not in self.rsoutputs:
                if s_output not in self.rsoutputs:
                    continue

                # if sobj.outlets[soindex] in sobj.cur_outlets_on:
                if s_output in sobj.cur_outputs_on:
                    if self.outputs_enable is True:
                        self.rsoutputs[s_output]['obj'].on()
                    if self.debug is True:
                        # debug_msg += ',' + str(sobj.outputs[s_output])
                        debug_msg += ',' + s_output

                else:
                    # self.rsoutputs[sobj.outputs[s_output]].off()
                    if self.outputs_enable is True:
                        self.rsoutputs[s_output]['obj'].off()

            if self.debug is True:
                if len(sobj.cur_outputs_on) > 0:
                    debug_msg += ')'

        if debug_msg != '' and self.debug is True:
            mytime = time.asctime()
            print(mytime, ':', signal_data, debug_msg)
            if len(self.history) > 0:
                if mytime == self.history[-1]['time']:
                    self.errs += 1
                    if self.errs >= 100:
                        print('Error bug reached')
                        for h in range(0, len(self.history)):
                            print(self.history[h]['time'], self.history[h]['data'])
                        self.deinit()
                        exit(-1)

                else:
                    self.errs = 0
                    self.history.clear()

            self.error_dict['time'] = mytime
            self.error_dict['data'] = signal_data.copy()
            self.history.append(self.error_dict)

    def start(self):
        for out_obj in self.rsoutputs.keys():
            if self.rsoutputs[out_obj]['type'] == 'sequencer_status':
                if self.outputs_enable is True:
                    self.rsoutputs[out_obj]['obj'].on()

    def stop(self):
        for out_obj in self.rsoutputs.keys():
            if self.rsoutputs[out_obj]['type'] == 'sequencer_status':
                if self.outputs_enable is True:
                    self.rsoutputs[out_obj]['obj'].off()

    def reset(self):
        for out_obj in self.rsoutputs.keys():
            if self.rsoutputs[out_obj]['type'] != 'sequencer_status':
                self.rsoutputs[out_obj]['obj'].reset()

    def deinit(self):
        for out_obj in self.rsoutputs.keys():
            self.rsoutputs[out_obj]['obj'].deinit()


def run():
    global RS_CODE_DEBUG
    RS_CODE_DEBUG = True
    sr = Sequencer(debug=True)

    test_signal = [8, 0, 0, 0, 0, 0, 0, 0]
    import random
    for i in range(0, 50):
        #for j in range(1, 8):
        #    test_signal[j] = random.randrange(9)
        sr.check(test_signal)
        test_signal[1] = 8
        test_signal[2] = 8
        test_signal[3] = 8
        time.sleep(10)

    sr.deinit()


if __name__ == '__main__':

    run()

