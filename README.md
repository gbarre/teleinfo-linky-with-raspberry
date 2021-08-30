# Téléinfo Linky avec un Raspberry Pi
Surveiller sa consommation électrique en temps réel avec un compteur Linky et un Raspberry 

![grafana_std](https://github.com/Charlymd/teleinfo-linky-with-raspberry/blob/master/documentation/grafana_linky_standard.png)
![grafana_std2](https://github.com/Charlymd/teleinfo-linky-with-raspberry/blob/master/documentation/grafana%20info%20compteur%20floute.png)

Basé sur le travail de Sebastien Reuiller qui m'a permis d'appréhender rapidement le fonctionnement de la prise de Télé Information Client (TIC)
J'ai rajouté quelques fonctions telles que le calcul du checksum des valeurs d'index et la prise en charge de la tarification de base.
Merci à gizmo15 pour l'amélioration du code avec une mise en conformité PEP8
# Mode historique et standard
Les compteurs d'énergie électronique mis à disposition par Enedis disposent quasiment tous d'une prise TIC dont la connectique peut varié.
Deux modes de communication sont disponibles : 
- Historique 
Le mode de communication des anciens compteurs électroniques.
Les compteurs Linky sont livrés par défaut en mode historique pour permettre une rétrocompatibilité avec les équipements de bascule heures creuses /  heures pleines tels que les ballons d'eau chaude.
- Standard (plus complet)
Il est possible de les basculer en mode standard via l'espace client de votre fournisseur d'énergie (section configuration TIC) ou en appelant Enedis.

Le mode standard permet d'accéder à plus d'informations dont la liste exaustive est ici :
https://github.com/Charlymd/teleinfo-linky-with-raspberry/blob/master/documentation/liste_champs_mode_standard.txt

Exemple :
- Tension instantanée et moyennée par phase
- Energie réactive
- Courbe de charge active
- Point de reférence de mesure Enedis
- Registre des statuts 
- Profil et calendrier fournisseur

# Caracteristiques techniques
|Tech. "Historique"|Tech. "Standard"  |
|--|--|
| Tous les compteurs avec TIC| Uniquement "Linky", paramétré dans ce mode |
|Porteuse de 50kHz|Porteuse de 50kHz|
|UART - Async Serial|UART - Async Serial|
|Async Serial Vitesse : 1200 Bauds|Vitesse : 9600 Bauds|
|Caractéristique de transmission : logique négative (0 = présence porteuse, 1 = absence porteuse), LSB First, "0" start bit, 7 bit ASCII (Donc 8 bit par transfert, "1" bit stop, bit parité paire (even)  |Caractéristique de transmission : logique négative (0 = présence porteuse, 1 = absence porteuse), LSB First, "0" start bit, 7 bit ASCII (Donc 8 bit par transfert, "1" bit stop, bit parité paire (even)|
|Trame : 7 éléments|Trame : 7 ou 9 éléments (Horodate en plus selon champ)|
|Début de transmission < STX > (0x02)|Début de transmission < STX > (0x02)|
|< LF > (0x0A) Label < SP > (0x20) Data < SP > Checksum < CR > (0x0D)|< LF > (0x0A) Label [< HT > (0x09) Heure] < HT > Data < HT > Checksum < CR > (0x0D)|
|Fin de transmission : < ETX > (0x03)|Fin de transmission : < ETX > (0x03)|

## Documentation

Tuto pas à pas sur le blog de Sebastien Reuiller : [Monitorer son compteur Linky avec Grafana, c’est possible.. et ça tourne sur un Raspberry Pi!](https://sebastienreuiller.fr/blog/monitorer-son-compteur-linky-avec-grafana-cest-possible-et-ca-tourne-sur-un-raspberry-pi/)

## Sources diverses
https://github.com/colloc-ahgm/linky-collector
https://hallard.me/pitinfov12/
https://linuxfr.org/forums/linux-general/posts/configurer-ttys0
