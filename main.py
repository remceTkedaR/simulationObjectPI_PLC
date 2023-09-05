# //=============================================================================
# //Radosław Tecmer)
# //(c)Copyright (2023) free of copyright
# //-----------------------------------------------------------------------------
# //The program communicates with the PLC Siemens S7 1200 (300).
# //Generates a variable that simulates a PI controller.
# // Changes in the output parameter are calculated by the modified PI controller.
# // The input signal, on the basis of which the controller calculates a new value,
# // the simulated value is the current Hz on the inverter.
# //-----------------------------------------------------------------------------
# //contact:
# //https://github.com/remceTkedaR
# //radek69tecmer@gmail.com
# //=============================================================================


import time
import snap7.exceptions
import struct


class PIController:
    def __init__(self, kp, ki):
        self.kp = kp
        self.ki = ki
        self.integral = 0.0

    def update(self, setpoint, process_variable):
        error = setpoint - process_variable
        self.integral += error
        output = self.kp * error + self.ki * self.integral
        return output


class WaterPressureSimulator:
    def __init__(self):
        self.bar_out = 0.0

    def simulate(self, act_Hz):
        # Symulacja zmiany ciśnienia wody
        # Tutaj można dodać bardziej zaawansowaną logikę symulacji
        # W tym przykładzie prosty przyrost wartości "bar_out"
        self.bar_out += act_Hz * 0.01  # Przyrost w zależności od act_Hz

        # Ograniczenie wartości do zakresu od 0.0 do 7.0
        if self.bar_out < 0.0:
            self.bar_out = self.bar_out + 0.1
        elif self.bar_out > 7.0:
            self.bar_out = self.bar_out - 5.5


def data_block_read(db_number, inst_number, data):
    db_val = plc.db_read(db_number, inst_number, data)
    value_struct = struct.iter_unpack("!f", db_val[:4])
    for value_pack in value_struct:
        value_unpack = value_pack
    # Convert tuple to float
    # using join() + float() + str() + generator expression
    result = float('.'.join(str(ele) for ele in value_unpack))
    my_str_value = '%-.4f' % result
    return my_str_value


# konfiguracja połaczenie ze sterownikiem PLC S7 300
plc_ip = '192.168.3.203'
db_read = 1
offsite_read = 32
plc = snap7.client.Client()
plc.connect(plc_ip, 0, 2)

if __name__ == "__main__":
    # Parametry regulatora PI
    kp = 10.0
    ki = 1.1

    # Inicjalizacja regulatora
    controller = PIController(kp, ki)

    # Inicjalizacja symulatora ciśnienia wody
    simulator = WaterPressureSimulator()

    try:
        while True:
            # Pobranie aktualnej wartości Hz (act_Hz) bezpośrednio z kontrolera PLC
            act_Hz = data_block_read(1, 32, 4)  # ZAKŁADAMY, ŻE act_Hz JEST LICZBĄ ZMIENNOPRZECINKOWĄ

            # Pobranie aktualnej wartości ciśnienia z symulatora
            process_variable = simulator.bar_out

            # Wywołanie regulatora PI i uzyskanie sygnału sterującego
            #setpoint = float(act_Hz)  # Konwertujemy act_Hz na float
            setpoint = ((float(act_Hz) + 27648) / 27648) * 7.0 + 0.0

            # Ograniczenie wartości setpoint do zakresu od 0.0 do 7.0
            if setpoint < 0.0:
                setpoint = setpoint + 0.1
            elif setpoint > 7.0:
                setpoint = 7.0

            control_signal = controller.update(setpoint, process_variable)

            # Symulacja zmiany ciśnienia wody na podstawie sygnału sterującego
            simulator.simulate(control_signal)

            print(f"Setpoint: {setpoint}, Process Variable: {process_variable}, Control Signal: {control_signal}, act_Hz: {act_Hz}")

            # Przekazanie wartości do bloku danych sterownika PLC
            data_bytes = struct.pack("!f", process_variable)
            plc.db_write(1, 0, data_bytes)

            time.sleep(1)  # Czekaj przez sekundę przed kolejnym pomiar

    except KeyboardInterrupt:
        # Zatrzymanie programu po wciśnięciu Ctrl+C
        pass

    # Wynik działania symulacji
    final_pressure = simulator.bar_out
    print(f"Final Pressure: {final_pressure}")