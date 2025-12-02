import pandas as pd
import os

class DataQualityChecker:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.student_info = None
        self.title_info = None
        self.submit_records = []

    def load_student_info(self):
        """加载学生信息数据"""
        student_info_path = os.path.join(self.data_dir, 'Data_StudentInfo.csv')
        self.student_info = pd.read_csv(student_info_path)

    def load_title_info(self):
        """加载题目信息数据"""
        title_info_path = os.path.join(self.data_dir, 'Data_TitleInfo.csv')
        self.title_info = pd.read_csv(title_info_path)

    def load_submit_records(self):
        """加载所有班级的提交记录数据"""
        submit_record_files = [f for f in os.listdir(self.data_dir) 
                              if f.startswith('SubmitRecord-Class') and f.endswith('.csv')]
        for file in submit_record_files:
            file_path = os.path.join(self.data_dir, file)
            submit_record = pd.read_csv(file_path)
            self.submit_records.append(submit_record)

    def check_missing_values(self):
        """检查数据的缺失值"""
        print("学生信息数据缺失值情况：")
        print(self.student_info.isnull().sum())
        print("\n题目信息数据缺失值情况：")
        print(self.title_info.isnull().sum())
        for i, record in enumerate(self.submit_records):
            print(f"\n班级提交记录数据({i+1})缺失值情况：")
            print(record.isnull().sum())
            print("\n")

    def load_and_check_all(self):
        """加载所有数据并检查缺失值"""
        self.load_student_info()
        self.load_title_info()
        self.load_submit_records()
        self.check_missing_values()
