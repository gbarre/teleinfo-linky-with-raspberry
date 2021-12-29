#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "Sébastien Reuiller"
# __licence__ = "Apache License 2.0"
"""Send teleinfo standard to influxdb."""

# Python 3, prerequis : pip install pySerial influxdb
#
# Exemple de trame:
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



import logging
import time
from datetime import datetime
import requests
import serial
from influxdb import InfluxDBClient
MODE = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# clés téléinfo
CHAR_MEASURE_KEYS = ['DATE', 'NGTF', 'LTARF', 'MSG1', 'NJOURF', 'NJOURF+1',
                     'PJOURF', 'PJOURF+1', 'EASD02', 'STGE', 'RELAIS']

KEYS_FILE = "/opt/teleinfo-linky-with-raspberry/liste_champs_mode_standard.txt"
DICO_FILE = "/opt/teleinfo-linky-with-raspberry/liste_fabriquants_linky.txt"

# création du logguer
logging.basicConfig(filename='/var/log/teleinfo/releve.log',
                    level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("Teleinfo starting..")

# connexion a la base de données InfluxDB
CLIENT = InfluxDBClient('localhost', 8086)
DB = "teleinfo2"
CONNECTED = False
while not CONNECTED:
    try:
        logging.info("Database %s exists?", DB)
        if {'name': DB} not in CLIENT.get_list_database():
            logging.info("Database %s creation..", DB)
            CLIENT.create_database(DB)
            logging.info("Database %s created!", DB)
        CLIENT.switch_database(DB)
        logging.info("Connected to %s !", DB)
    except requests.exceptions.ConnectionError:
        logging.info('InfluxDB is not reachable. Waiting 5 seconds to retry.')
        time.sleep(5)
    else:
        CONNECTED = True


def add_measures(measures):
    """Add measures to array."""
    points = []
    for measure, value in measures.items():
        point = {
            "measurement": measure,
            "tags": {
                # identification de la sonde et du compteur
                "host": "raspberry",
                "region": "linky"
            },
            "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": {
                "value": value
                }
            }
        points.append(point)

    CLIENT.write_points(points)


def verif_checksum(line_str, checksum):
    """Check data checksum."""
    data_unicode = 0
    data = line_str[0:-2] #chaine sans checksum de fin
    for caractere in data:
        data_unicode += ord(caractere)
    sum_unicode = (data_unicode & 63) + 32
    sum_chain = chr(sum_unicode)
    return bool(checksum == sum_chain)


def keys_from_file(file):
    """Get keys from file."""
    labels = []
    #"available_linky_standard_keys.txt"
    with open(file) as keys_file:
        for line in keys_file:
            information = line.split("\t")
            labels.append(information[1])
    return labels


def dico_from_file(file):
    """Get info from file."""
    information = {}
    with open(file) as dico_file:
        for line in dico_file:
            line = line.replace("\n", "")
            decoupage = line.split("\t")
            code_fabricant = int(decoupage[0])
            nom_fabricant = decoupage[1]
            information[code_fabricant] = nom_fabricant
    return information


def main():
    """Main function to read teleinfo."""
    with serial.Serial(port='/dev/ttyAMA0', 
                       baudrate=9600,
                       parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.SEVENBITS,
                       timeout=1) as ser:
        logging.info("Teleinfo is reading on /dev/ttyAMA0..")
        logging.info("Mode standard")

        labels_linky = keys_from_file(KEYS_FILE)
        liste_fabriquants = dico_from_file(DICO_FILE)
        #liste_modeles = keys_from_file("/opt/teleinfo-linky-with-raspberry/modeles_linky.txt")

        trame = dict()

        # boucle pour partir sur un début de trame
        line = ser.readline()
        while b'\x02' not in line:  # recherche du caractère de début de trame
            line = ser.readline()

        # lecture de la première ligne de la première trame
        line = ser.readline()

        while True:
            logging.debug(line)
            line_str = line.decode("utf-8")
            ar_split = line_str.split("\t") # separation sur tabulation

            try:
                key = ar_split[0]
                #checksum = ar[-1] #dernier caractere
                #verification = verif_checksum(line_str,checksum)
                #logging.debug("[debug]verification checksum :  s%" % str(verification))

                if key in labels_linky:
                    # typer les valeurs connus sous forme de chaines en "string"
                    if key in CHAR_MEASURE_KEYS:
                        value = ar_split[-2]
                    else:
                        try:
                            # typer les autres valeurs en "integer"
                            value = int(ar_split[-2])
                        except Exception:
                            logging.error("erreur de conversion en nombre entier %s", key)
                            value = 0

                    trame[key] = value   # creation du champ pour la trame en cours
                else:
                    trame['verification_error'] = "1"
                    logging.error("[erreur] etiquette inconnue %s", key)

                if b'\x03' in line:  # si caractère de fin de trame, on insère la trame dans influx
                    time_measure = time.time()

                    # ajout nom fabriquant
                    numero_compteur = str(trame['ADSC'])
                    id_fabriquant = int(numero_compteur[2:4])
                    trame['OEM'] = liste_fabriquants[id_fabriquant]

                    # ajout du CosPhi calculé
                    if (trame["IRMS1"] and trame["URMS1"] and trame["SINSTS"]):
                        trame["COSPHI"] = (trame["SINSTS"] / (trame["IRMS1"] * trame["URMS1"]))
                    logging.debug(trame["COSPHI"])
                    # ajout timestamp pour debugger
                    trame["timestamp"] = int(time_measure)

                    # insertion dans influxdb
                    add_measures(trame)
                    logging.info("------")
                    logging.info("------ add frame in database")
                    
                    trame = dict()  # on repart sur une nouvelle trame
            except Exception:
                logging.error("[erreur] traitement etiquette: %s", key)
                logging.debug("Ligne brut: %s \n" % line)
            line = ser.readline()


if __name__ == '__main__':
    if CONNECTED:
        main()
