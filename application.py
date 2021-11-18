from flask import Flask, jsonify, request, render_template
import numpy as np
import pandas as pd
import os
import uuid 
import json
import re
import time
from datetime import datetime


# To configure MySQL DB
from flask_mysqldb import MySQL
import yaml

# For model dumping
import joblib

application = Flask(__name__)

basepath = "/var/flask-app/" # os.path.abspath(".")  | "./"
# basepath = "./"

# Configure db
db = yaml.load(open(basepath +'database.yaml'))
application.config['MYSQL_HOST'] = db['mysql_host']
application.config['MYSQL_USER'] = db['mysql_user']
application.config['MYSQL_PASSWORD'] = db['mysql_password']
application.config['MYSQL_DB'] = db['mysql_db']
application.config['MYSQL_PORT'] = db['mysql_port']
mysql = MySQL(application)

classes = []
list_most_prob_soc = []
list_most_prob_desc = []

# Results for RF and NB models respectively
result_rf = []
result_nb = []
json_soc = [{}]

@application.route('/')
@application.route('/index.html')
# @application.route('/index.html')
def index():
    # Creating Classes List
    try:
        
        if(len(classes) == 0):
            print('Classes : ')
            cur = mysql.connection.cursor()
            resultValue = cur.execute("SELECT SOC FROM AYJ_SOCAvailableClasses")
            print(resultValue)
            if resultValue > 0:
                availableSOC = cur.fetchall()
                for i in range(0, len(availableSOC)):
                    classes.append(availableSOC[i][0])
            cur.close()
        print('Classes : ', classes)
        return render_template('index.html')
    
    except Exception as e:
        return render_template('error.html', error=e)

# 2 decorators same function
@application.route('/', methods=['POST'])
@application.route('/results/<id>', methods=['POST'])
def findSOC(id='findSOC'):
    if(request.form.get('salcal') == "salcal"):
        salCalculate()
        id = 'report'
        message = "Done"
        return message, id
    else:
        print('The program is here.')
        if request.method == "POST":
            print(request.form)
            msg = 'pending'
            JD = request.form.get('jd')
            back = request.form.get('jd2')
    
            dict_back_soc = {
                'SOC1' : request.form.get('SOC1'),
                'SOC2' : request.form.get('SOC2'),
                'SOC3' : request.form.get('SOC3'),
                'SOC4' : request.form.get('SOC4'),
                'SOC5' : request.form.get('SOC5'),
                'SOC6' : request.form.get('SOC6'),
            }

            dict_model_soc = {
                'M1' : request.form.get('M1'),
                'M2' : request.form.get('M2'),
                'M3' : request.form.get('M3'),
                'M4' : request.form.get('M4'),
                'M5' : request.form.get('M5'),
                'M6' : request.form.get('M6'),
            }

            # result = request.form.get('suggestions')
            result_radio = request.form.get('radio')
            result_manual = request.form.get('manual')
            prediction = {}

            print(result_radio, result_manual)
            print('dict_back_soc : ', dict_back_soc)
            
            # Dataframe for Available Classes - ML models are trained for these
            df_prob = pd.DataFrame({"SOC": classes})
            df_prob.sort_values(by='SOC', ascending=True, inplace=True)

            def modelProbability(userJD, model):
                # Probabilities for RF
                list_model_prob = []
                dict_model_prob = {}
                y_proba = model.predict_proba(userJD)
                # print(y_proba)
                df_prob['model_prob'] = y_proba[0]
                df_prob.sort_values(by='model_prob', ascending=False, inplace=True)
                
                list_model_prob.append(df_prob['SOC'].iloc[0])
                list_model_prob.append(df_prob['SOC'].iloc[1])
                list_model_prob.append(df_prob['SOC'].iloc[2])
                
                dict_model_prob[1] = [df_prob['SOC'].iloc[0], df_prob['model_prob'].iloc[0]]
                dict_model_prob[2] = [df_prob['SOC'].iloc[1], df_prob['model_prob'].iloc[1]]
                dict_model_prob[3] = [df_prob['SOC'].iloc[2], df_prob['model_prob'].iloc[2]]

                # Reset Probability Dataframe
                df_prob.drop(['model_prob'], axis=1, inplace=True)
                df_prob.sort_values(by='SOC', ascending=True, inplace=True)

                return list_model_prob, dict_model_prob

            def mergeResults(dict_rf, dict_nb):
                main_dict_data = {}
                count = 1
                
                for k1, v1 in dict_rf.items():
                    for k2, v2 in dict_nb.items():
                        if(v2[0] not in main_dict_data.values() and v1[0] not in main_dict_data.values()):
                            if(v1[0] == v2[0]):
                                main_dict_data[count] = v1[0]
                                break
                            else:
                                if(k1 == k2):
                                    if(v1[1] > v2[1]):
                                        main_dict_data[count] = v1[0]
                                        count += 1
                                        main_dict_data[count] = v2[0]
                                        break
                                    else:
                                        main_dict_data[count] = v2[0]
                                        count += 1
                                        main_dict_data[count] = v1[0]
                                        break
                    count += 1
                main_list_data = list(main_dict_data.values())
                return main_dict_data, main_list_data

            def modelPredict(data):
                
                # Unseen JD from the User
                df_data = pd.DataFrame({"JD": [data]})

                # load, no need to initialize the loaded_rf
                loaded_model_rf = joblib.load(basepath + "static/models/random_forest.joblib")
                loaded_model_nb = joblib.load(basepath + "static/models/naive_baeyes.joblib")

                # pred = loaded_model.predict(df_data['JD'])

                # Fetching results for ML models
                result_rf, dict_rf = modelProbability(df_data['JD'], loaded_model_rf)
                result_nb, dict_nb = modelProbability(df_data['JD'], loaded_model_nb)
                result_nb.extend(result_rf)
                list_most_prob_soc = result_nb
                dict_data, list_data = mergeResults(dict_rf, dict_nb)
                # print('dict_data : ', dict_data)

                cur = mysql.connection.cursor()
                list_desc = []
                list_phd = []
                list_ict_icgt = []
                list_eligiblity = []
                list_rqf = []
                list_so = []
                list_note = []
                # Salary addition
                list_rate = []
                list_90B = []
                list_80CD = []
                list_70E = []
                list_hours = []
                list_tab = []

                for soc in list_data:
                    resultValue = cur.execute("select Description, PhD, ICT_ICGT,Eligible, Skill_Level, Shortage_Occ, Note, Going_rate_A, 90_B, 80_C_and_D, 70_E, Hours, TabNo from AYJ_SOCDescription where SOC = %d;" %soc)
                    if resultValue > 0:
                        # print(cur.fetchall())
                        availableSOC = cur.fetchall()
                        print(availableSOC)
                        for i in range(0, len(availableSOC)):
                            list_desc.append(availableSOC[i][0])
                            list_phd.append(availableSOC[i][1])
                            list_ict_icgt.append(availableSOC[i][2])
                            list_eligiblity.append(availableSOC[i][3])
                            list_rqf.append(availableSOC[i][4])
                            list_so.append(availableSOC[i][5])
                            list_note.append(availableSOC[i][6])
                            list_rate.append(availableSOC[i][7])
                            list_90B.append(availableSOC[i][8])
                            list_80CD.append(availableSOC[i][9])
                            list_70E.append(availableSOC[i][10])
                            list_hours.append(availableSOC[i][11])
                            list_tab.append(availableSOC[i][12])
                        
                cur.close()
                
                return list_most_prob_soc, list_data, list_desc, list_phd, list_ict_icgt, list_eligiblity, list_rqf, list_so, list_note, list_rate, list_90B, list_80CD, list_70E, list_hours, list_tab
            
            try:
                if(JD != None):
                    print('inside if')
                    json_dict_soc = {}
                    list_all_soc, list_merged_data, list_merged_desc, list_merged_phd, list_merged_ict_icgt, list_merged_eligiblity, list_merged_rqf, list_merged_so, list_merged_note, list_merged_rate, list_merged_90B, list_merged_80CD, list_merged_70E, list_merged_hours, list_merged_tabs  = modelPredict(JD)
                    
                    if(len(list_merged_data) == len(list_merged_desc)):
                        for i in range(1, len(list_merged_data)+1):
                            key = "SOC" + str(i)
                            key_d = key + "_desc_" + str(i)
                            json_dict_soc[key] = str(list_merged_data[i-1])
                            json_dict_soc[key_d] = list_merged_desc[i-1]
                            json_dict_soc[key + "_phd_" + str(i)] = list_merged_phd[i-1]
                            json_dict_soc[key + "_ict_icgt_" + str(i)] = list_merged_ict_icgt[i-1]
                            json_dict_soc[key + "_eligible_" + str(i)] = list_merged_eligiblity[i-1]
                            json_dict_soc[key + "_rqf_" + str(i)] = list_merged_rqf[i-1]
                            json_dict_soc[key + "_so_" + str(i)] = list_merged_so[i-1]
                            json_dict_soc[key + "_note_" + str(i)] = list_merged_note[i-1]
                            json_dict_soc[key + "_rate_" + str(i)] = list_merged_rate[i-1]
                            json_dict_soc[key + "_90B_" + str(i)] = list_merged_90B[i-1]
                            json_dict_soc[key + "_80CD_" + str(i)] = list_merged_80CD[i-1]
                            json_dict_soc[key + "_70E_" + str(i)] = list_merged_70E[i-1]
                            json_dict_soc[key + "_hours_" + str(i)] = list_merged_hours[i-1]
                            json_dict_soc[key + "_tab_" + str(i)] = list_merged_tabs[i-1]

                        # json_dict_soc['pid'] = p_id

                    for i in range(1, len(list_all_soc)+1):
                        key = "M" + str(i)
                        json_dict_soc[key] = str(list_all_soc[i-1])
                    
                    print('json_dict_soc : ', json_dict_soc)

                    json_soc = [json_dict_soc]

                    print('first')
                    # print(jsonify(jobD))

                    # return render_template('findSOC.html', data = json_soc, jobD = jobD) # {'JD' : JD})
                    # return render_template('findSOC.html', data = json_soc, jobD = jobD) # {'JD' : JD})
                    # return render_template('error.html')
                    # return jsonify(json_soc)
                    return json_dict_soc
                
                elif(result_manual != None or result_radio != None):
                    
                    print('inside elif')
                    list_model_soc = [dict_model_soc['M1'], 
                    dict_model_soc['M2'], dict_model_soc['M3'], dict_model_soc['M4'], dict_model_soc['M5'], dict_model_soc['M6']]
                    flag = True 

                    if(result_radio != None):
                        result = result_radio
                    else:
                        result = result_manual

                    if(result not in dict_model_soc.values()):
                        flag = False

                    print(result, flag)

                    p_id = uuid.uuid1()
                    print('p_id with results :', p_id)
                    current_Date = datetime.now().date()
                    # formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cur = mysql.connection.cursor()
                    insert_socdata_query = """INSERT INTO AYJ_SOCData(ID, JD, Date_Of_Entry, M1_SOC_1, M1_SOC_2, M1_SOC_3,
                    M2_SOC_1, M2_SOC_2, M2_SOC_3) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s) """ 
                    socdata_records = (p_id, back, current_Date, dict_model_soc['M1'], 
                    dict_model_soc['M2'], dict_model_soc['M3'], dict_model_soc['M4'], dict_model_soc['M5'], dict_model_soc['M6'])
                    cur.execute(insert_socdata_query, socdata_records)
                    mysql.connection.commit()
                    # cur.close()

                    # cur = mysql.connection.cursor()
                    insert_soctrue_query = """INSERT INTO AYJ_SOCTrue(SOC_ID, SOC, Flag) VALUES ( %s, %s, %s) """ 
                    soctrue_records = (p_id, result, flag)
                    cur.execute(insert_soctrue_query, soctrue_records)
                    mysql.connection.commit()
                    cur.close()

                    msg = 'success'
                    print(msg)

                    return({'msg' : msg})

            except Exception as e:
                print("An exception occurred: ", e) 
                return render_template('error.html', error=e) 

@application.route('/results/#salcal', methods=['POST'])
def salCalculate():
    print('salCal Python')

@application.route('/templates/findSOC.html', methods=['GET'])
def findSOC2():
    return render_template('findSOC.html')

if __name__ == '__main__':
    application.run(debug=True)
