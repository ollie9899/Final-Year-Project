import neo
import numpy as np
import dill
from scipy.signal import butter, filtfilt


def lowest(a_list):
    low = a_list[0]
    for i in range(len(a_list)):
        if a_list[i] < low:
            low = a_list[i]

    return low


def generate_sequence(open_time, close_time):

    closed_per_ms_open = close_time // open_time
    remainder = close_time % open_time
    predicted_sequence = []

    # most common case where close time is greater than opening time
    if closed_per_ms_open >= 1:
        temp = int(open_time)
        for i in range(0, temp):
            if remainder > 0:
                predicted_sequence.append((1, closed_per_ms_open + 1))
                remainder = remainder - 1
            else:
                predicted_sequence.append((1, closed_per_ms_open))

    # handle case of a peak that needs max gradient, avoids div 0 error
    elif close_time == 0:
        predicted_sequence.append((open_time, 0))

    # handle case where there is more opening time than closing time
    else:
        open_per_ms_closed = open_time // close_time
        remainder = open_time % close_time
        temp = int(open_time)
        for i in range(0, temp):
            if remainder > 0:
                predicted_sequence.append((open_per_ms_closed + 1, 1))
                remainder = remainder - 1
            else:
                predicted_sequence.append((open_per_ms_closed, 1))

    return predicted_sequence


def calc_expected_change(starting_lvl, sequence):

    current_lvl = starting_lvl
    for cmd in sequence:
        # y = 0.00976911x + 0.007046358927684328
        current_lvl = current_lvl + (0.145*cmd[0])
        temp = int(cmd[1])
        for i in range(0, temp):
            if current_lvl <= 0:
                break
            current_lvl = current_lvl - (0.00976911*current_lvl + 0.007046358927684328)

    return current_lvl - starting_lvl


class Compiler:

    def __init__(self, input_path, input_name, destination, input_type):
        self.input_path = input_path
        self.input_name = input_name
        self.input_type = input_type
        self.destination = destination
        self.block = None
        self.segments = None
        self.analog_sig = None
        self.sample_rate = 10000
        self.filtered_data = None
        self.lines = None
        self.data = []
        self.output_string = ""
        self.load_data()
        self.reset_output_str()

    def reset_output_str(self):
        self.output_string = '#include <SerialCommand.h>\n\nint temp = 0;\nint main1 = 16;\nint relieve1 = 19;' \
                             '\nint main2 = 21;\nint relieve2 = 17;\nint trigger1 = 22;\nint trigger2 = 23;' \
                             '\nint incoming = 0;\nint boardLed = 2;\n\nSerialCommand sCmd;\n\nvoid setup() {' \
                             '\n  Serial.begin(115200);\n  pinMode(boardLed,OUTPUT);\n  pinMode(main1,OUTPUT);' \
                             '\n  pinMode(relieve1,OUTPUT);\n  pinMode(main2,OUTPUT);\n  pinMode(relieve2,OUTPUT);' \
                             '\n  pinMode(trigger1,OUTPUT);\n  pinMode(trigger2,OUTPUT);' \
                             '\n  sCmd.addCommand("m11",    main1_on);\n  sCmd.addCommand("m10",    main1_off);' \
                             '\n  sCmd.addCommand("r11",    relieve1_on);\n  sCmd.addCommand("r10",    relieve1_off);' \
                             '\n  sCmd.addCommand("p1",     plume);\n}\nvoid loop() {\n  sCmd.readSerial();\n}' \
                             '\nvoid main1_on(){\n  Serial.println("main1 on");\n  digitalWrite(main1,HIGH);' \
                             '\n  digitalWrite(trigger1,HIGH);\n}\nvoid main1_off(){\n  Serial.println("main1 off");' \
                             '\n  digitalWrite(trigger1,LOW);\n  digitalWrite(main1,LOW);\n}\nvoid relieve1_on(){' \
                             '\n  Serial.println("relieve1 on");\n  digitalWrite(relieve1,HIGH);\n}\n void relieve1_off(){' \
                             '\n  Serial.println("relieve1 off");\n  digitalWrite(relieve1,LOW);\n}\nvoid main1_on_plume(){' \
                             '\n  digitalWrite(main1, HIGH);\n  digitalWrite(relieve1, LOW);\n}\nvoid main2_off_plume(){' \
                             '\n  digitalWrite(main1, LOW);\n  digitalWrite(relieve1, HIGH);\n}\n' \
                             'void open_for(int openTime, int closeTime) {\n  digitalWrite(main1, HIGH);\n  ' \
                             'digitalWrite(relieve1, LOW);\n  delay(openTime);\n  digitalWrite(main1, LOW);\n  ' \
                             'digitalWrite(relieve1, HIGH);\n  delay(closeTime);\n}\nvoid plume(){' \
                             '\n  digitalWrite(relieve1, HIGH);\n  digitalWrite(relieve2, HIGH);\n  delay(1000);' \
                             '\n  digitalWrite(trigger1,HIGH);\n'

    def load_data(self):
        if self.input_type == "smr":
            try:
                reader = neo.io.Spike2IO(filename=self.input_path)
                self.block = reader.read()[0]
                self.segments = self.block.segments[0]
                self.analog_sig = self.segments.analogsignals[0]
                self.sample_rate = int(self.analog_sig.sampling_rate)
                temp_data = np.array(self.analog_sig)

                for i in range(len(temp_data)):
                    self.data.append(temp_data[i][0])
                self.data = np.array(self.data)

            except FileNotFoundError:
                print("Error file not found")

        elif self.input_type == 'dill':
            try:
                with open(self.input_path, 'rb') as fH:
                    self.block = dill.load(fH)
                    self.segments = self.block.segments[0]
                    self.analog_sig = self.segments.analogsignals[0]
                    self.sample_rate = int(self.analog_sig.sampling_rate)
                    temp_data = np.array(self.analog_sig)

                    for i in range(len(temp_data)):
                        self.data.append(temp_data[i][0])
                    self.data = np.array(self.data)
            except FileNotFoundError:
                print("Error file not found")
        else:
            print("Error")

    def low_pass_filter_normalise(self, order=4):

        low = lowest(self.data)
        for i in range(len(self.data)):
            self.data[i] = self.data[i] - low

        nyq = 0.5 * self.sample_rate
        cutoff = self.sample_rate / 10
        normal_cutoff = cutoff / nyq
        b, a = butter(N=order, Wn=3, btype='lowpass', analog=False, output='ba', fs=self.sample_rate)

        self.filtered_data = filtfilt(b, a, self.data)

    def gen_lines(self):
        lines = []
        current = self.filtered_data[0]
        current_index = 0
        i = 1
        increase = True
        total = 0

        while i < len(self.filtered_data) - 1:

            if self.filtered_data[i] > self.filtered_data[i + 1] and increase is True:
                lines.append((self.filtered_data[i] - current, round((i - current_index) / 10)))
                total = total + ((i - current_index) / 10)
                current = self.filtered_data[i + 1]
                current_index = i + 1
                increase = False

            if self.filtered_data[i] < self.filtered_data[i + 1] and increase is False:
                lines.append((self.filtered_data[i] - current, round((i - current_index) / 10)))
                total = total + ((i - current_index) / 10)
                current = self.filtered_data[i + 1]
                current_index = i + 1
                increase = True
            i = i + 1
        self.lines = lines
        print(lines)
        print(total)
        return lines

    def gen_arduino2(self):

        estimated_in_system = 0
        total_time = 0
        total_peaks = 0
        arduino_cmds = []

        for i in range(0, len(self.lines)):

            if estimated_in_system < 0:
                estimated_in_system = 0
            command = []
            con_change = self.lines[i][0]
            time = self.lines[i][1]

            if time < 1:
                continue

            # equilibrium
            if -0.08 < con_change < 0.08:
                # change depending on current levels in machine relationship between concentration levels is logarithmic
                # created a linear regression model in colab so apply log to y values
                # y = -0.02562987x + 0.5876971058204313
                # X = (Y - c) / m
                # only going to work up to about relative concentration of 3 at the moment
                if estimated_in_system > 0:
                    opening_rate = round((np.log(estimated_in_system) - 0.5876971058204313) / (-0.02562987), 0)

                    print(opening_rate)
                    print(estimated_in_system)
                    while time > 0:
                        time = time - opening_rate - 1
                        if time >= 0:
                            arduino_cmds.append("  open_for(1, " + str(int(opening_rate)) + ");\n")
                        else:
                            time2 = str(round((time*(-1))-1, 0))
                            if len(time2) > 1 and time2[-2] == '.':
                                time2 = time2[:-2]

                            if time2[0] == '-':
                                time2 = time2[1:]

                            arduino_cmds.append("  open_for(1, " + time2 + ");\n")
                else:
                    arduino_cmds.append("  delay(" + str(time) + ");\n")

                estimated_in_system = estimated_in_system + con_change
            # for increase
            elif con_change >= 0.08:

                open_time = round(con_change/0.145, 1)
                close_time = time - open_time
                current_sequence = generate_sequence(open_time, close_time)
                expected_change = calc_expected_change(estimated_in_system, current_sequence)
                expected_needed_diff = expected_change - con_change
                # negative predicted to be too small, positive too big
                iterations = 0
                while (expected_needed_diff < -0.1 or expected_needed_diff > 0.1) and iterations < 20:

                    if expected_needed_diff < -0.1:

                        while expected_needed_diff < -0.1:
                            open_time = open_time + 1
                            close_time = close_time - 1
                            expected_needed_diff = expected_needed_diff + 0.145

                    elif expected_needed_diff > 0.1:

                        while expected_needed_diff > 0.1:
                            open_time = open_time - 1
                            close_time = close_time + 1
                            expected_needed_diff = expected_needed_diff - 0.145

                    current_sequence = generate_sequence(open_time, close_time)
                    expected_change = calc_expected_change(estimated_in_system, current_sequence)
                    expected_needed_diff = expected_change - con_change
                    iterations = iterations + 1

                estimated_in_system = estimated_in_system + con_change
                for item in current_sequence:
                    arduino_cmds.append("  open_for(" + str(int(item[0])) + ", " + str(int(item[1])) + ");\n")

            # decrease
            else:
                gradient = (con_change / time)*-1
                expected_current_gradient = 0.00976911*estimated_in_system + 0.007046358927684328
                # y = 0.00976911x + 0.007046358927684328
                if time <= 60 or estimated_in_system + con_change <= 0.2 or gradient > expected_current_gradient:
                    arduino_cmds.append("  delay(" + str(time) + ");\n")
                    estimated_in_system = estimated_in_system + con_change
                else:
                    arduino_cmds.append("  delay(" + str(time) + ");\n")
                    estimated_in_system = estimated_in_system + con_change

        for cmd in arduino_cmds:
            self.output_string = self.output_string + cmd

        self.output_string += 'digitalWrite(trigger1, LOW);\n'
        self.output_string += '}'
        print(total_time)
        print(total_peaks)

    def save_to_file(self):
        if self.input_type == "smr":
            output_name = self.destination + "/" + self.input_name[:-3] + "ino"
            f = open(output_name, "x")
            f = open(output_name, "a")
            f.write(self.output_string)
            f.close()
        else:
            output_name = self.destination + "/" + self.input_name[:-4] + "ino"
            with open(output_name, 'w') as f:
                f.write(self.output_string)




