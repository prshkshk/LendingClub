import airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from urllib.request import urlopen, urlretrieve, quote
from urllib.parse import urljoin
import os
import requests
import zipfile
import pandas as pd
import glob
import datetime as dt
import seaborn as sns
%matplotlib inline
import math
from datetime import datetime

accept_path = '/Users/pranaymankad/LendingClubData/LoanData/'
reject_path = '/Users/pranaymankad/LendingClubData/RejectData/'

default_args = {
    'owner': 'me',
    'start_date': dt.datetime(2017, 10, 1),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=5),
}

dag = DAG(
    'part1',
    default_args=default_args,
    schedule_interval='0 0 1 */3 *',
    description='Assignment 2 Part 1')

def print_start():
    print('Starting Process: Logging in with data.')
        
def download_LoanCSV():

    driver=webdriver.Chrome()    

    login = driver.get('https://www.lendingclub.com/auth/login')
    login_id = driver.find_element_by_name('email')
    password = driver.find_element_by_name('password')

    login_id.send_keys('deveshkandpal24@gmail.com')
    password.send_keys('devesh24') 

    driver.find_element_by_css_selector('.form-button.form-button--submit').click()
    
    r = requests.get('https://www.lendingclub.com/account/summary.action')
    if r.status_code==200:
        page = driver.get('https://www.lendingclub.com/info/download-data.action')
        select = Select(driver.find_element_by_id('loanStatsDropdown'))
        select_reject = Select(driver.find_element_by_id('rejectStatsDropdown'))
    else:
        print("Gafla hua in Main Download")
    
    for element in select.options:
        element.click()
        print(element.get_attribute("text"))
        url = driver.find_element_by_id("currentLoanStatsFileName").get_attribute("href")
        split = url.rsplit('?', 1)[-2]
        filename = os.path.join(accept_path, split.rsplit('/', 1)[-1])
        #button.click()
        print("Downloading %s to %s..." % (url, accept_path) )
        urlretrieve(url, filename)
        print(url)
    print("Done")

    for element in select_reject.options:
        element.click()
        print(element.get_attribute("text"))
        url = driver.find_element_by_id("currentRejectStatsFileName").get_attribute("href")
        filename = os.path.join(reject_path, url.rsplit('/', 1)[-1])
        #button.click()
        print("Downloading %s to %s..." % (url, reject_path) )
        urlretrieve(url, filename)
        print(url)
    print("Done")
    

def unzip_CSV():
    dir_name = accept_path
    extension = ".zip"

    os.chdir(dir_name) 

    for item in os.listdir(dir_name): 
        if item.endswith(extension): 
            file_name = os.path.abspath(item) 
            zip_ref = zipfile.ZipFile(file_name,"r") 
            zip_ref.extractall(dir_name)
            zip_ref.close()
            os.remove(file_name)

    dir_name = reject_path

    os.chdir(dir_name)

    for item in os.listdir(dir_name):
        if item.endswith(extension):
            file_name = os.path.abspath(item) 
            zip_ref = zipfile.ZipFile(file_name,"r") 
            zip_ref.extractall(dir_name)
            zip_ref.close()
            os.remove(file_name)


def frameData_CSV():
    path = accept_path
    allFiles = glob.glob(path + "*.csv")
    frame = pd.DataFrame()

    dataFrame = []
    for f in allFiles:
        df = pd.read_csv(f,index_col=None, header=1)
        dataFrame.append(df)
    frame = pd.concat(dataFrame)

    path = '/Users/pranaymankad/LendingClubData/'
    os.chdir(path)
    frame.to_csv('loan_data.csv', encoding='utf-8', index=False)

    path = reject_path
    allFiles = glob.glob(path + "*.csv")
    reject_frame = pd.DataFrame()

    dataFrame = []
    for f in allFiles:
        df = pd.read_csv(f,index_col=None, header=1)
        dataFrame.append(df)
    reject_frame = pd.concat(dataFrame)

    path = '/Users/pranaymankad/LendingClubData/'
    os.chdir(path)
    reject_frame.to_csv('rejected_data.csv', encoding='utf-8', index=False)

def cleaning_CSV():

    loan_data_df = pd.read_csv('/Users/pranaymankad/LendingClubData/loan_data.csv')

    loan_classification_df =  loan_data_df

    loan_classification_df = loan_classification_df[loan_classification_df['fico_range_low'].notnull()]
    loan_classification_df = loan_classification_df[loan_classification_df['fico_range_high'].notnull()]
    loan_classification_df = loan_classification_df[loan_classification_df['fico_range_low'] > 660]
    loan_classification_df['risk_score'] = (loan_classification_df['fico_range_low'] + loan_classification_df['fico_range_high']) / 2
    loan_classification_df['term'] = loan_classification_df['term'].map({' 36 months': 36, ' 60 months' : 60})
    loan_classification_df['int_rate'] = loan_classification_df['int_rate'].map(lambda x : x.replace('%', ''))
    loan_classification_df['int_rate'] = loan_classification_df['int_rate'].map(float)
    loan_classification_df = loan_classification_df[loan_classification_df['dti'].notnull() & loan_classification_df['loan_amnt'].notnull()]

    loan_classification_df = loan_classification_df[loan_classification_df['emp_length'].notnull()]
    loan_classification_df = loan_classification_df[loan_classification_df['emp_length'] != 'n/a']
    loan_classification_df['emp_length'] = loan_classification_df['emp_length'].map({'4 years' : 4, '8 years' : 8, '10+ years' : 10, '< 1 year' : 0, '6 years' : 6, '2 years' : 2,
        '1 year' : 1, '3 years' : 3, '5 years' : 5, '7 years' : 7, '9 years' : 9})
    loan_classification_df['emp_length'] = loan_classification_df['emp_length'].map(int)

    loan_classification_df = loan_classification_df.dropna(axis=1, thresh=0.30 * loan_classification_df.shape[0])
    loan_classification_df = loan_classification_df.dropna(axis=0, thresh = 0.30 * (loan_classification_df.shape[1]))

    loan_classification_df = loan_classification_df[loan_classification_df['loan_amnt'].notnull() & loan_classification_df['purpose'].notnull() & loan_classification_df['risk_score'].notnull() & loan_classification_df['dti'].notnull() & loan_classification_df['addr_state'].notnull() & loan_classification_df['emp_length'].notnull()]

    loan_classification_df = loan_classification_df[['loan_amnt', 'purpose', 'risk_score', 'dti', 'addr_state', 'emp_length']]
    loan_classification_df['accepted'] = 1

    rejected_data_df = pd.read_csv("/Users/pranaymankad/LendingClubData/rejected_data.csv")

    common_title = pd.Series(list(set(loan_classification_df['purpose']) & set(rejected_data_df['Loan Title'])))
    rejected_data_df = rejected_data_df.loc[rejected_data_df['Loan Title'].isin(common_title)]
    rejected_data_df = rejected_data_df[rejected_data_df['Policy Code'].notnull()]

    rejected_data_df = rejected_data_df.rename(columns = {'Amount Requested' : 'loan_amnt', 'Loan Title' : 'purpose', 'Risk_Score' : 'risk_score', 'Debt-To-Income Ratio' : 'dti', 'Zip Code' : 'zip_code', 'State' : 'addr_state', 'Employment Length' : 'emp_length', 'Policy Code' : 'policy_code'})

    rejected_data_df = rejected_data_df[rejected_data_df['emp_length'].notnull()]
    rejected_data_df = rejected_data_df[rejected_data_df['emp_length'] != 'n/a']
    rejected_data_df['emp_length'] = rejected_data_df['emp_length'].map({'4 years' : 4, '8 years' : 8, '10+ years' : 10, '< 1 year' : 0, '6 years' : 6, '2 years' : 2,
        '1 year' : 1, '3 years' : 3, '5 years' : 5, '7 years' : 7, '9 years' : 9})
    rejected_data_df['emp_length'] = rejected_data_df['emp_length'].map(int)
    rejected_data_df['dti'] = rejected_data_df['dti'].map(lambda x : x.replace('%', ''))

    rejected_data_df = rejected_data_df[rejected_data_df['loan_amnt'].notnull() & rejected_data_df['purpose'].notnull() & rejected_data_df['risk_score'].notnull() & rejected_data_df['dti'].notnull() & rejected_data_df['addr_state'].notnull() & rejected_data_df['emp_length'].notnull()]

    rejected_data_df = rejected_data_df[['loan_amnt', 'purpose', 'risk_score', 'dti', 'addr_state', 'emp_length']]
    rejected_data_df['accepted'] = 0


    data_list = [loan_classification_df, rejected_data_df]
    classification_data = pd.concat(data_list, ignore_index=True)
    classification_data = classification_data.dropna(axis=0)
    purpose_dummies = pd.get_dummies(classification_data['purpose'])
    addr_dummies = pd.get_dummies(classification_data['addr_state'])
    classification_data = classification_data.join(purpose_dummies)
    classification_data = classification_data.join(addr_dummies)
    classification_data.drop('purpose', 1, inplace=True)
    classification_data.drop('addr_state', 1, inplace=True)
    classification_data.to_csv('/Users/pranaymankad/LendingClubData/classification_data.csv', index = False)

    loan_clustering_df =  loan_data_df

    loan_clustering_df = loan_clustering_df[loan_clustering_df['fico_range_low'].notnull()]
    loan_clustering_df = loan_clustering_df[loan_clustering_df['fico_range_high'].notnull()]
    loan_clustering_df = loan_clustering_df[loan_clustering_df['fico_range_low'] > 660]
    loan_clustering_df['risk_score'] = (loan_clustering_df['fico_range_low'] + loan_clustering_df['fico_range_high']) / 2
    loan_clustering_df['term'] = loan_clustering_df['term'].map({' 36 months': 36, ' 60 months' : 60})
    loan_clustering_df['int_rate'] = loan_clustering_df['int_rate'].map(lambda x : x.replace('%', ''))
    loan_clustering_df['int_rate'] = loan_clustering_df['int_rate'].map(float)
    loan_clustering_df = loan_clustering_df[loan_clustering_df['dti'].notnull() & loan_clustering_df['loan_amnt'].notnull()]

    loan_clustering_df = loan_clustering_df[loan_clustering_df['emp_length'].notnull()]
    loan_clustering_df = loan_clustering_df[loan_clustering_df['emp_length'] != 'n/a']
    loan_clustering_df['emp_length'] = loan_clustering_df['emp_length'].map({'4 years' : 4, '8 years' : 8, '10+ years' : 10, '< 1 year' : 0, '6 years' : 6, '2 years' : 2,
        '1 year' : 1, '3 years' : 3, '5 years' : 5, '7 years' : 7, '9 years' : 9})
    loan_clustering_df['emp_length'] = loan_clustering_df['emp_length'].map(int)

    loan_clustering_df = loan_clustering_df.dropna(axis=1, thresh=0.30 * loan_clustering_df.shape[0])
    loan_clustering_df = loan_clustering_df.dropna(axis=0, thresh = 0.30 * (loan_clustering_df.shape[1]))

    loan_clustering_df = loan_clustering_df[['loan_amnt', 'purpose', 'risk_score', 'dti', 'grade', 'emp_length', 'annual_inc', 'term', 'sub_grade', 'int_rate']]

    loan_clustering_df = loan_clustering_df[loan_clustering_df['int_rate'] <=25]
    loan_clustering_df = loan_clustering_df[loan_clustering_df['loan_amnt'] <= 38000]

    purpose_dummies = pd.get_dummies(loan_clustering_df['purpose'])
    sub_grade_dummies = pd.get_dummies(loan_clustering_df['sub_grade'])
    loan_clustering_df = loan_clustering_df.join(purpose_dummies)
    loan_clustering_df = loan_clustering_df.join(sub_grade_dummies)
    loan_clustering_df.drop('purpose', 1, inplace=True)
    loan_clustering_df.drop('sub_grade', 1, inplace=True)

    loan_clustering_df = loan_clustering_df[loan_clustering_df['annual_inc'].notnull()]
    loan_clustering_df.to_csv('/Users/pranaymankad/LendingClubData/clustering_data.csv', index = False)

with DAG('assign2_part1',
         default_args=default_args
         ) as dag:

    print_hello = BashOperator(task_id='print_hello',
                               bash_command='echo "welcome"',dag=dag)
    print_start = PythonOperator(task_id='print_start',
                                 python_callable=print_start,dag=dag)
    download_LoanCSV = PythonOperator(task_id='download_LoanCSV',
                                 python_callable=download_LoanCSV,dag=dag)
    unzip_CSV = PythonOperator(task_id='unzip_CSV',
                                 python_callable=unzip_CSV,dag=dag)
    frameData_CSV = PythonOperator(task_id='frameData_CSV',
                                 python_callable=frameData_CSV,dag=dag)
    cleaning_CSV = PythonOperator(task_id='cleaning_CSV',
                                 python_callable=cleaning_CSV,dag=dag)


print_hello >> print_start >> download_LoanCSV >> unzip_CSV >> frameData_CSV >> cleaning_CSV