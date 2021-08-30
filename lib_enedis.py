"""
Library from ENEDIS specification of french energy meter
"""
class energy_meter():

    def register_analyze(registre_hexa):
        """
        Transform and split hexadecimal register from ENEDIS energy meter
        """
        registre={}
        # format 32 bits
        registre_bin="{:032b}".format(int(registre_hexa))
        # décalage de 1 en lecture inversée
        # print(registre_bin)

        # contact sec :0
        registre["contact"]=registre_bin[-1]
        ##print("contact sec", registre_bin[-1])

        # Organe de coupure : 1 - 3
        LIST_COUPURE=('fermé','ouvert sur surpuissance','ouvert sur surtension','ouvert sur délestage','ouvert sur ordre CPL','ouvert surchauffe avec courant supérieur','ouvert avec surchauffe sans dépassement courant')
        registre["coupure"]=LIST_COUPURE[eval(registre_bin[-4:-2])]
        ##print("Organe de coupure : ", LIST_COUPURE[eval(registre_bin[-4:-2])])

        # etat cache borne : 4
        LIST_CACHE_BORNE=('fermé','ouvert')
        registre["borne"]=LIST_CACHE_BORNE[eval(registre_bin[-5])]
        ##print("etat cache borne : ", LIST_CACHE_BORNE[eval(registre_bin[-5])])

        # non utilisé : 5

        # surtension sur une des phases : 6
        LIST_SURTENSION=('pas de surtension','surtension en cours')
        registre["surtension"]=LIST_SURTENSION[eval(registre_bin[-7])]
        ##print("surtension sur une des phases : ",LIST_SURTENSION[eval(registre_bin[-7])])

        # depassement de puissance de reference 7
        LIST_DEPASSEMENT=('pas de dépassement','dépassement en cours')
        registre["depassement"]=LIST_DEPASSEMENT[eval(registre_bin[-8])]
        ##print("depassement de puissance de reference : ", LIST_DEPASSEMENT[eval(registre_bin[-8])])

        # fonctionnement producteur consommateur 8
        LIST_PRODUCTEUR_CONSOMMATEUR=('consommateur','producteur')
        registre["prodconso"]=LIST_PRODUCTEUR_CONSOMMATEUR[eval(registre_bin[-9])]
        ##print("fonctionnement producteur consommateur : ", LIST_PRODUCTEUR_CONSOMMATEUR[eval(registre_bin[-9])])

        # sens de l'energie active 9
        LIST_ENERGIE_ACTIVE=('positive','négative')
        registre["active"]=LIST_ENERGIE_ACTIVE[eval(registre_bin[-10])]
        ##print("sens de l'energie active : ", LIST_ENERGIE_ACTIVE[eval(registre_bin[-10])])

        # tarif en cours sur le contrat de fourniture 10 - 13
        LIST_TARIF_FOURNITURE=('index1','index2','index3','index4','index5','index6','index7','index8','index9','index10')
        registre["fourniture"]=LIST_TARIF_FOURNITURE[eval(registre_bin[-14:-11])]
        ##print("tarif en cours sur le contrat de fourniture : ", LIST_TARIF_FOURNITURE[eval(registre_bin[-14:-11])])

        # tarif en cours sur le contrat distributeur 14 - 15
        LIST_TARIF_DISTRIBUTEUR=('index1','index2','index3','index4')
        registre["distributeur"]=LIST_TARIF_DISTRIBUTEUR[eval(registre_bin[-16:-15])]
        ##print("tarif en cours sur le contrat distributeur : ", LIST_TARIF_DISTRIBUTEUR[eval(registre_bin[-16:-15])])

        # mode dégradé de l'horloge 16
        LIST_HORLOGE=('horloge correcte','horloge mode dégradé')
        registre["horloge"]=LIST_HORLOGE[eval(registre_bin[-17])]
        ##print("mode dégradé de l'horloge : ", LIST_HORLOGE[eval(registre_bin[-17])])

        # état de la sortie téléinformation 17
        LIST_TIC=('mode historique','mode standard')
        registre["tic"]=LIST_TIC[eval(registre_bin[-18])]
        ##print("état de la sortie TIC : ", LIST_TIC[eval(registre_bin[-18])])

        # non utilisé 18

        # etat de la communication Euridis 19 - 20
        DICT_COM_EURIDIS={'00':'désactivé','01':'activé sans sécurité','11':'activé avec sécurité'}
        STATUT_EURIDIS=registre_bin[-21]+registre_bin[-20]
        registre["euridis"]=DICT_COM_EURIDIS[STATUT_EURIDIS]
        ##print("Etat de la communication Euridis : ", DICT_COM_EURIDIS[STATUT_EURIDIS])

        # statut CPL 21 -22
        DICT_STATUT_CPL = {'00':'New Unlock','01':'New Lock','10':'Registered'}
        STATUT_CPL=registre_bin[-23]+registre_bin[-22]
        registre["cpl"]=DICT_STATUT_CPL[STATUT_CPL]
        ##print("statut CPL : ", DICT_STATUT_CPL[STATUT_CPL])

        # Synchronisation CPL 23
        LIST_SYNCHRO=('compteur non synchronisé','compteur synchronisé')
        registre["synchro"]=LIST_SYNCHRO[eval(registre_bin[-24])]
        ##print("Synchronisation CPL : ", LIST_SYNCHRO[eval(registre_bin[-24])])

        # couleur du jour pour les contrats historique tempo 24-25
        LIST_COULEUR=['pas d\'annonce','bleu','blanc','rouge']
        JOUR_TEMPO = int(registre_bin[-26:-25])
        registre["tempo"]=LIST_COULEUR[JOUR_TEMPO]
        ##print("couleur du jour pour les contrats historique tempo : ", LIST_COULEUR[JOUR_TEMPO])

        # Couleur du lendemain pour contrat historique tempo 26-27
        LENDEMAIN_TEMPO = int(registre_bin[-28:-25])
        registre["lendemain"]=LIST_COULEUR[LENDEMAIN_TEMPO]
        ##print("Couleur du lendemain pour contrat historique tempo :", LIST_COULEUR[LENDEMAIN_TEMPO])

        # préavis pointes mobiles 28-29
        LIST_PREAVIS_POINTES_MOBILES=('pas de préavis','préavis PM1','préavis PM2','préavis PM3')
        registre["preavis"]=LIST_PREAVIS_POINTES_MOBILES[eval(registre_bin[-30:-29])]
        ##print("préavis pointes mobiles : ", LIST_POINTES_MOBILES[eval(registre_bin[-30:-29])])

        # pointe mobile 30-31
        LIST_POINTES_MOBILES=('pas de pointe','PM1 en cours','PM2 en cours''PM3 en cours')
        registre["pointe"]=LIST_POINTES_MOBILES[eval(registre_bin[-32:-31])]
        ##print("pointe mobile : ", LIST_POINTES_MOBILES[eval(registre_bin[-32:-31])])
        return(registre)


if __name__ == "__main__":
    # execute only if run as a script for test functions
    dict_register=energy_meter.register_analyze(0x003A0001)
    for key,value in dict_register.items():
        print(key+':'+value)
