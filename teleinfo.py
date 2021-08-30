#!/usr/bin/python3
# -*- coding: utf-8 -*-
# __author__ = "Charles Peltier"
# __credit__ = "Sébastien Reuiller, gizmo15"
# __licence__ = "Apache License 2.0"
"""Send teleinfo to influxdb."""

# Python 3, prerequis : pip install pySerial influxdb
#
# Exemple de trame contenant plusieurs groupes d'information :
# {
#  'BASE': '123456789'       # Index heure de base en Wh
#  'OPTARIF': 'HC..',        # Option tarifaire HC/BASE
#  'IMAX': '007',            # Intensité max
#  'HCHC': '040177099',      # Index heure creuse en Wh
#  'IINST': '005',           # Intensité instantanée en A
#  'PAPP': '01289',          # Puissance Apparente, en VA
#  'MOTDETAT': '000000',     # Mot d'état du compteur
#  'HHPHC': 'A',             # Horaire Heures Pleines Heures Creuses
#  'ISOUSC': '45',           # Intensité souscrite en A
#  'ADCO': '000000000000',   # Adresse du compteur
#  'HCHP': '035972694',      # index heure pleine en Wh
#  'PTEC': 'HP..'            # Période tarifaire en cours
# }

# Library
import os
import logging
import time
from datetime import datetime

import requests
import serial
from influxdb import InfluxDBClient
from lib_enedis import energy_meter

# Config
LOGGING_MODE = "INFO"	  # DEBUG, WARNING, INFO
TIC_MODE = "HISTORIQUE"  # STANDARD, HISTORIQUE
TIC_PORT = '/dev/ttyS0' # Not use for the moment
PROBE_NAME = 'Raspberry' # Not use for the moment
DUT = 'Linky' # Device under test - Not use for the moment
LOGGER_FILE = "/var/log/teleinfo/releve.log"	# Not use for the moment
INFLUXDB_HOST = "localhost"
DB = "teleinfo"

# dictionaries and keys
LABELS_HISTORIQUE_FILE = "liste_champs_mode_historique.txt"
LABELS_STANDARD_FILE = "liste_champs_mode_standard.txt"
DICT_OEM_FILE = "dictionnaire_fabriquants_linky.txt"
DICT_MODEL_FILE = "dictionnaire_type_linky.txt"

## type of key char, not integer
CHAR_MEASURE_KEYS = ['OPTARIF', 'HHPHC', 'PTEC', 'MOTDETAT', 'DATE', 'NGTF', 'LTARF', 'MSG1', 'NJOURF', 'NJOURF+1',
                     'PJOURF', 'PJOURF+1', 'EASD02', 'STGE', 'RELAIS']


# Creation of directory for log
directory = os.path.dirname("/var/log/teleinfo/")
if not os.path.exists(directory):
   os.makedirs(directory)

# creation of logguer
numeric_level = getattr(logging, LOGGING_MODE.upper(), None)
logging.basicConfig(filename=LOGGER_FILE,level=numeric_level, format='%(asctime)s %(message)s')
logging.info('\n')
logging.info(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
logging.info("Teleinfo starting..")

# connexion to InfluxDB database
CLIENT = InfluxDBClient(INFLUXDB_HOST, 8086)
CONNECTED = False
while not CONNECTED:
    try:
        logging.info("Check if database %s exist", DB)
        if {'name': DB} not in CLIENT.get_list_database():
            logging.info("Database %s creation..", DB)
            CLIENT.create_database(DB)
            logging.info("Database %s created!", DB)
        CLIENT.switch_database(DB)
        logging.info("Connected to %s!", DB)
    except requests.exceptions.ConnectionError:
        logging.info('InfluxDB is not reachable. Waiting 5 seconds to retry.')
        time.sleep(5)
    else:
        logging.info("Database %s exist", DB)
        CONNECTED = True


# add a measure point in frame
def add_measures(measures):
    """Add measures to array."""
    points = []
    for measure, value in measures.items():
        point = {
            "measurement": measure,
            "tags": {
                # identification of device
                "device": 'raspberry'
                #"dut": 'compteur_buanderie'
            },
            "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": {
                "value": value
                }
            }
        points.append(point)

    CLIENT.write_points(points)
    logging.debug("add measure")

# Check checksum of the line
def verif_checksum(line_str, checksum):
    """Check data checksum."""
    data_unicode = 0
    data = line_str[0:-2] #chaine sans checksum de fin
    for caractere in data:
        data_unicode += ord(caractere)
    sum_unicode = (data_unicode & 63) + 32
    sum_chain = chr(sum_unicode)
    return bool(checksum == sum_chain)


# Label from ENEDIS specifications normally send by the Linky
## Name/ID/length/Unit
def know_labels_from_file(file):
    """Get valid labels from file."""
    labels = []
    with open(file) as keys_file:
        for line in keys_file:
            information = line.split("\t")
            labels.append(information[1])
    return labels


# ID and name of manufacturer of Linky authorized by ENEDIS
def oem_from_file(file):
    """Get OEM name from file."""
    information = {}
    with open(file) as dico_file:
        for line in dico_file:
            line = line.replace("\n", "")
            decoupage = line.split("\t")
            code_fabricant = int(decoupage[0])
            nom_fabricant = decoupage[1]
            information[code_fabricant] = nom_fabricant
    return information


# ID and name of know Linky models 
# ID/linky/Phasage/Ampérage/description
def models_from_file(file):
    """Get Linky model name from file."""
    information = {}
    with open(file) as dico_file:
        for line in dico_file:
            line = line.replace("\n", "")
            decoupage = line.split("\t")
            code_modele = int(decoupage[0])
            nom_modele = decoupage[1]
            information[code_modele] = nom_modele
    return information


# Configuration of serial port speed and dictionnary of label
def mode_config(mode):
    global TIC_SPEED 
    global LABELS_LINKY
    global SPLIT_CHAR
    global ADDRESS_LINKY

    if (mode == "STANDARD"):
        TIC_SPEED = '9600'
        LABELS_LINKY = know_labels_from_file(LABELS_STANDARD_FILE)
        SPLIT_CHAR = "\t"
        ADDRESS_LINKY = 'ADSC'
    else:
        TIC_SPEED = '1200'
        LABELS_LINKY = know_labels_from_file(LABELS_HISTORIQUE_FILE)
        SPLIT_CHAR = " "
        ADDRESS_LINKY = 'ADCO'
    logging.debug("\n\nKnow labels: %s", LABELS_LINKY)
 




# find OEM from serial number of linky
def oem_linky(serial):
    manufacturer_id = int(serial[2:4])
    return manufacturer_id


# Add calcultate CosPhi for standard mode
# puissance apparente / courant efficace phase 1 * tension effice phase 1
def calculate_cosphi():
    #if (trame["IRMS1"] and trame["URMS1"] and trame["SINSTS"]):
    #    trame["COSPHI"] = (trame["SINSTS"] / (trame["IRMS1"] * trame["URMS1"]))
    logging.debug(trame["COSPHI"])


def main():
    """Main function to read teleinfo."""

    mode_config(TIC_MODE)

    with serial.Serial(port=TIC_PORT, baudrate=TIC_SPEED, parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.SEVENBITS, timeout=1) as tic:
        logging.info("Teleinfo is reading on %s", TIC_PORT)
        logging.info("Mode %s", TIC_MODE)
        logging.info("parameters of serial :%s", tic)
       
        dict_linky_oem = oem_from_file(DICT_OEM_FILE)
        logging.debug("\n\nKnow manufacturer: %s",dict_linky_oem)
        
        dict_linky_models = models_from_file(DICT_MODEL_FILE)
        #logging.debug("\n\nKown linky models: s%",dict_linky_models)

        # create new frame
        logging.debug("\n\ncreate first frame")
        trame = dict()

        # Read information from serial
        line = tic.readline()
        logging.info("Start of frames analysis")
	
        # loop and search beginning of frame
        while b'\x02' not in line:
            line = tic.readline()
        
	# Read first frame find after last step
        logging.debug("Start of frame")
        line = tic.readline()
        while True:
            #logging.info("ligne %s:", line)
            line_str = line.decode("utf-8")
            try:
                line_split = line_str.split(SPLIT_CHAR)
                label = line_split[0]
                #checksum = line_str[-1] #dernier caractere
                #verification = verif_checksum(line_str,checksum)
                #logging.debug("verification checksum :  s%" % str(verification))

		# check if value is integer or character
                if label in LABELS_LINKY:
                    # type as string if variable is in this list
                    if label in CHAR_MEASURE_KEYS:
                        #value = line_split[-2]
                        value = line_split[1]
                    else:
                        try:
                            # type other values as integer
                            #value = int(line_split[-2])
                            value = int(line_split[1])
                        except Exception:
                            logging.info("erreur de conversion en nombre entier")
                            value = 0
                    # creation of label for this frame
                    trame[label] = value
                    logging.debug("-> %s %s", label, value)
                    logging.debug("|_> know label")
                else:
                    trame['verification_error'] = "1"
                    logging.debug("erreur etiquette inconnue")


                # if end of frame \x03, insert it in influxdb
                if b'\x03' in line:
                    logging.debug("End of frame")

                    # decode Linky serial to find OEM ID
                    trame['OEM'] = oem_linky(str(trame[ADDRESS_LINKY]))

                    # decode register statut form STGE
                    try:
                        STGE=trame['STGE']
                        dict_register=energy_meter.register_analyze('STGE')
                        for key,value in dict_register.items():
                            logging.debug(key+':'+value)
                            trame[key]=value
                    except:
                        logging.debug('STGE absent')

                    # insert in influxdb
                    logging.debug("\n\ntrying to add measure : %s", trame)
                    add_measures(trame)

                    # New Frame
                    trame = dict()

            # exeption of try
            except Exception as error:
                logging.error("Exception : %s", error, exc_info=True)
                #logging.error("Ligne brut: %s \n" % line)
            
	    # read line and loop on while
            line = tic.readline()

if __name__ == '__main__':
    if CONNECTED:
        main()
