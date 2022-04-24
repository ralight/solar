#!/usr/bin/env python3

import datetime
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Model
from givenergy_modbus.model.plant import Plant
from influxdb import InfluxDBClient
import sys
import os
import time
import subprocess
import paho.mqtt.client

def update_orb(p):
    batval = int(abs(p.inverter.p_battery)*255/2500)
    if batval > 255:
        batval = 255
    elif batval < 0:
        batval = 0
    gridval = int(abs(p.inverter.p_grid_out)*255/2500)
    if gridval > 255:
        gridval = 255
    elif gridval < 0:
        batval = 0
    if p.inverter.p_battery < 0:
        if p.inverter.p_grid_out > 3000:
            # Exporting at a high rate, battery charging = yellow
            subprocess.run(["/usr/local/bin/orb","#ff%0.2x00"%(batval)], shell=False)
        else:
            # Battery charging = green
            subprocess.run(["/usr/local/bin/orb","#00%0.2x00"%(batval)], shell=False)
    elif p.inverter.p_battery > 0:
        if p.inverter.p_grid_out < 0:
            # Battery draining and importing from grid = pink
            subprocess.run(["/usr/local/bin/orb","#%0.2x00%0.2x"%(batval,gridval)], shell=False)
        else:
            # Battery draining, no import from grid = red
            subprocess.run(["/usr/local/bin/orb","#%0.2x0000"%(batval)], shell=False)
    else:
        # Battery charged = blue
        subprocess.run(["/usr/local/bin/orb", "#0000ff"], shell=False)


mqttc = paho.mqtt.client.Client()
mqttc.connect("test.mosquitto.org", 1883, 60)
mqttc.loop_start()


while True:
    try:
        client = GivEnergyClient(host="192.168.1.4")
        p = Plant(number_batteries=1)
        client.refresh_plant(p, full_refresh=True)

        update_orb(p)

        ifclnt = InfluxDBClient(HOST, PORT, USERNAME, PASSWORD, DATABASE)
        json_body = [
            {
                "measurement": "solar",
                "fields": {
                    "battery_percent": p.inverter.battery_percent,
                    "e_battery_charge_day": p.inverter.e_battery_charge_day,
                    "e_battery_discharge_day": p.inverter.e_battery_discharge_day,
                    "e_battery_throughput_total": p.inverter.e_battery_throughput_total,
                    "e_inverter_out_day": p.inverter.e_inverter_out_day,
                    "e_inverter_out_total": p.inverter.e_inverter_out_total,
                    "e_inverter_in_day": p.inverter.e_inverter_in_day,
                    "e_inverter_in_total": p.inverter.e_inverter_in_total,
                    "e_grid_out_day": p.inverter.e_grid_out_day,
                    "e_grid_out_total": p.inverter.e_grid_out_total,
                    "e_grid_in_day": p.inverter.e_grid_in_day,
                    "e_grid_in_total": p.inverter.e_grid_in_total,
                    "e_pv1_day": p.inverter.e_pv1_day,
                    "e_pv2_day": p.inverter.e_pv2_day,
                    "e_solar_diverter": p.inverter.e_solar_diverter,
                    "f_ac1": p.inverter.f_ac1,
                    "i_ac1": p.inverter.i_ac1,
                    "i_battery": p.inverter.i_battery,
                    "i_grid_port": p.inverter.i_grid_port,
                    "i_pv1": p.inverter.i_pv1,
                    "i_pv2": p.inverter.i_pv2,
                    "p_battery": p.inverter.p_battery,
                    "p_grid_apparent": p.inverter.p_grid_apparent,
                    "p_grid_out": p.inverter.p_grid_out,
                    "p_inverter_out": p.inverter.p_inverter_out,
                    "p_load_demand": p.inverter.p_load_demand,
                    "p_pv1": p.inverter.p_pv1,
                    "p_pv2": p.inverter.p_pv2,
                    "e_pv_total": p.inverter.e_pv_total,
                    "pf_inverter_out": p.inverter.pf_inverter_out,
                    "temp_battery": p.inverter.temp_battery,
                    "temp_charger": p.inverter.temp_charger,
                    "temp_inverter_heatsink": p.inverter.temp_inverter_heatsink,
                    "v_ac1": p.inverter.v_ac1,
                    "v_battery": p.inverter.v_battery,
                    "v_pv1": p.inverter.v_pv1,
                    "v_pv2": p.inverter.v_pv2,
                    "battery_full_capacity": p.batteries[0].battery_full_capacity,
                    "battery_design_capacity": p.batteries[0].battery_design_capacity,
                    "battery_remaining_capacity": p.batteries[0].battery_remaining_capacity
                }
            }
        ]
        ifclnt.write_points(json_body)
    except Exception as e:
        print(e)
        pass
    time.sleep(10)
