# -*- coding: utf-8 -*-
"""

This module supports students at the Universidade Federal de Santa Catarina (UFSC - Brazil) to easily calculate
their corresponding GPA scores since the grading system used at UFSC is decimal-based. The module automatically
access the user's platform and scrape the student's transcript of records and enables a few actions, such as
grade simulation, GPA conversion using multiple scales and a transcript generation with subject descriptions
translated as well with their corresponding grade in the GPA scale selected

Example:
    The complete functionality of the module is in the `demonstration.ipynb` file
    The simple GPA conversion can be tested using the command below:

        $ python score_converter.py

Todo:
    * Find more features to implement


"""

import getpass
import pandas as pd
import warnings

from bs4 import BeautifulSoup
from dotenv import get_key, find_dotenv
from requests import session as Session


class LoginError(Exception):
    """Exception raised for errors in the login.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class GPAConverter():
    """Scraper of UFSC's Undergraduate academic control system (CAGR) to convert academic record from Decimal to GPA grading scale"""

    _LOGIN_URL = 'https://sistemas.ufsc.br/login?service=https%3A%2F%2Fcagr.sistemas.ufsc.br%2Fj_spring_cas_security_check&userType=padrao&convertToUserType=alunoGraduacao&lockUserType=1'
    _WALL_URL = 'https://collecta.sistemas.ufsc.br/restrito/confirmacaoFrame.xhtml'
    _RECORD_URL = 'https://cagr.sistemas.ufsc.br/modules/aluno/historicoEscolar/'

    # 1: http://calculadora.abroaders.com.br/
    # 2: http://www.centralia.edu/academics/earthscience/resources/dec_grd_sys.htm
    # 3: https://blog.prepscholar.com/gpa-chart-conversion-to-4-0-scale

    scale = {
        1: [
            {'decimal': 9, 'grade': 4.0},
            {'decimal': 7, 'grade': 3.0},
            {'decimal': 5, 'grade': 2},
            {'decimal': 3, 'grade': 1},
            {'decimal': 0, 'grade': 0}
        ],
        2: [
            {'decimal': 9.7, 'grade': 4.0},
            {'decimal': 9.6, 'grade': 3.9},
            {'decimal': 9.5, 'grade': 3.8},
            {'decimal': 9.3, 'grade': 3.7},
            {'decimal': 9.1, 'grade': 3.6},
            {'decimal': 9.0, 'grade': 3.5},
            {'decimal': 8.8, 'grade': 3.4},
            {'decimal': 8.7, 'grade': 3.3},
            {'decimal': 8.5, 'grade': 3.2},
            {'decimal': 8.4, 'grade': 3.1},
            {'decimal': 8.2, 'grade': 3.0},
            {'decimal': 8.0, 'grade': 2.9},
            {'decimal': 7.9, 'grade': 2.8},
            {'decimal': 7.8, 'grade': 2.7},
            {'decimal': 7.7, 'grade': 2.6},
            {'decimal': 7.6, 'grade': 2.5},
            {'decimal': 7.5, 'grade': 2.4},
            {'decimal': 7.4, 'grade': 2.3},
            {'decimal': 7.3, 'grade': 2.2},
            {'decimal': 7.2, 'grade': 2.1},
            {'decimal': 7.1, 'grade': 2.0},
            {'decimal': 7.0, 'grade': 1.9},
            {'decimal': 6.9, 'grade': 1.8},
            {'decimal': 6.8, 'grade': 1.7},
            {'decimal': 6.7, 'grade': 1.6},
            {'decimal': 6.6, 'grade': 1.5},
            {'decimal': 6.5, 'grade': 1.4},
            {'decimal': 6.4, 'grade': 1.3},
            {'decimal': 6.2, 'grade': 1.2},
            {'decimal': 6.1, 'grade': 1.1},
            {'decimal': 6.0, 'grade': 1.0},
            {'decimal': 0, 'grade': 0}
        ],
        3: [
            {'decimal': 9.3, 'grade': 4.0},
            {'decimal': 9.0, 'grade': 3.7},
            {'decimal': 8.7, 'grade': 3.3},
            {'decimal': 8.3, 'grade': 3.0},
            {'decimal': 8.0, 'grade': 2.7},
            {'decimal': 7.7, 'grade': 2.3},
            {'decimal': 7.3, 'grade': 2.0},
            {'decimal': 7.0, 'grade': 1.7},
            {'decimal': 6.7, 'grade': 1.3},
            {'decimal': 6.5, 'grade': 1.0},
            {'decimal': 0, 'grade': 0.0}
        ]
    }

    def __init__(self, username=None, password=None):
        self.__session = Session()
        # generate csrf token to include in the log-in payload
        self.__token = (
            BeautifulSoup(self.__session.get(GPAConverter._LOGIN_URL).content, 'lxml')
            .find(attrs={"name": "execution", "type": "hidden"})['value']
        )
        if not username or not password:
            self.login()
        else:
            self.__login(username, password)
            self.__bypass_wall()

    @classmethod
    def from_dotenv(cls):
        """Log-in using a .env file. The .env file must contain the variables USERNAME and PASSWORD

        Returns:
            instance (GPAConverter): a GPAConverter instance logged-in"""

        username = get_key(find_dotenv(), 'USERNAME')
        password = get_key(find_dotenv(), 'PASSWORD')
        instance = cls(username, password)
        return instance

    def login(self):
        """Log-in providing the credentials on the CLI"""
        # collect username via CLI
        username = input('Username: ')
        # use getpass to not expose password
        password = getpass.getpass('Password: ')

        self.__login(username, password)
        self.__bypass_wall()

    def __login(self, username, password):
        # generate payload to log-in
        payload = {
            'username': username,
            'password': password,
            'admin': 0,
            'execution': self.__token,
            '_eventId': 'submit'
        }

        response = self.__session.post(GPAConverter._LOGIN_URL, data=payload)
        # if HTTP 401 (Unauthorized - Wrong username or password) raise LoginError
        if response.status_code == 401:
            raise LoginError('Invalid username or password')

    def __bypass_wall(self):
        # generate standard payload to bypass a survey wall
        payload = {
            'j_id20': 'j_id20',
            'j_id20:j_id21': 'Clique aqui para voltar para o CAGR',
            'javax.faces.ViewState': 'j_id1'
        }

        self.__session.post(GPAConverter._WALL_URL, data=payload)

    def get_grade_records(self):
        """Scrape and return the transcript of records

        Returns:
        transcript (DataFrame): tabular data containing the subject code, description, credit points and grade
        """
        # transform the html content in a soup
        soup = BeautifulSoup(self.__session.get(GPAConverter._RECORD_URL).content, 'lxml')
        # find all Attributes in the table
        subjects_obj = soup.find_all('tr', attrs={'class': 'rich-table-row'})
        # subjects is used to store the subjects and all of its information
        subjects = list()

        for i in subjects_obj:
            subject = list(i)
            try:
                # divide credit points by the standard number of weeks in the academic calendar
                credits = int(subject[2].contents[0]) / 18
                grade = float(subject[3].contents[0])
            except IndexError:
                # if a subject doesn't contain credit points, do not include it into the list
                warnings.warn('Empty credit points subject', Warning)
                continue
            except ValueError:
                # if a subject do not contain a numeric grade, do not include it into the list
                warnings.warn('Concept I subject', Warning)
                continue
            subjects.append({
                'code': subject[0].contents[0],
                'subject': subject[1].contents[0],
                'credits': credits,
                'grade': grade,
            })
        # transform list of subejects in a DataFrame
        self.transcript = pd.DataFrame(subjects)
        return self.transcript

    @staticmethod
    def _gpa(grade, conversion):
        return max(conversion.loc[conversion.decimal <= grade, 'grade'])

    def get_iaa(self, transcript=None):
        """Calculates the grades' cumulative decimal average

        Attributes:
            transcript (DataFrame): tabular data cointaining the subjects, credit points and grades. If not provided, it will be scrapped out of CAGR
        """

        if transcript is None:
            try:
                transcript = self.transcript.copy()
            except AttributeError:
                warnings.warn('get_grade_records was not previously executed', Warning)
                self.get_grade_records()
                transcript = self.transcript

        print('IAA: %.2f' % (sum(transcript.credits * transcript.grade) / sum(transcript.credits)))

    def get_gpa(self, scale_id=1, transcript=None):
        """Calculates the GPA

        Attributes:
            scale_id (int): from 1 - 3, specifies the GPA scale used
                1: http://calculadora.abroaders.com.br/
                2: http://www.centralia.edu/academics/earthscience/resources/dec_grd_sys.htm
                3: https://blog.prepscholar.com/gpa-chart-conversion-to-4-0-scale

            transcript (DataFrame): tabular data cointaining the subjects, credit points and grades. If not provided, it will be scrapped out of CAGR
        """

        # creates a DataFrame of the selected scale
        conversion = pd.DataFrame(GPAConverter.scale[scale_id])

        # if a transcript is not provided, the one fetched by the module is used
        if transcript is None:
            try:
                transcript = self.transcript.copy()
            except AttributeError:
                warnings.warn('get_grade_records was not previously executed', Warning)
                self.get_grade_records()
                transcript = self.transcript

        print('GPA: %.2f' % (sum(transcript.credits * transcript.loc[:, 'grade'].apply(self._gpa, args=(conversion,))) / sum(transcript.credits)))

    def export_translated_transcript(self, scale_id=1):
        """Exports the transcript of records with GPA conversion and subject translation to a Excel Spreadsheet

        Attributes:
            scale_id (int): from 1 - 3, specifies the GPA scale used
                1: http://calculadora.abroaders.com.br/
                2: http://www.centralia.edu/academics/earthscience/resources/dec_grd_sys.htm
                3: https://blog.prepscholar.com/gpa-chart-conversion-to-4-0-scale
        """
        # creates a DataFrame of the selected scale
        conversion = pd.DataFrame(GPAConverter.scale[scale_id])

        # read translated transcript
        translated = pd.read_excel('./translated.xls', header=None, names=['code', 'subjects'])
        transcript = self.transcript.copy()

        # generate GPA and translated description columns
        transcript['translated'] = [translated.loc[translated.code == i, 'subjects'].iloc[0] if i in list(translated.code) else '' for i in transcript.code]
        transcript['gpa'] = transcript.loc[:, 'grade'].apply(self._gpa, args=(conversion,))
        transcript = transcript.loc[:, ['code', 'credits', 'grade', 'gpa', 'subject', 'translated']]

        # export file to excel and print its path
        transcript.to_excel('./exported_translated_transcript.xlsx')
        print('file saved as ./exported_translated_transcript.xlsx')


if __name__ == '__main__':
    test = GPAConverter()
    test.get_gpa()
