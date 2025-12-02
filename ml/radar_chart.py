import os
import glob
import pandas as pd
import numpy as np
from pyecharts.charts import Radar
from pyecharts import options as opts
from pyecharts.globals import ThemeType

class ClassRadarVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.student_df = None
        self.title_df = None
        self.submit_df = None
        self.grouped_class = None

    def load_data(self):
        """加载数据"""
        # 加载学生信息和题目信息
        student_info_path = os.path.join(self.data_path, "Data_StudentInfo.csv")
        title_info_path = os.path.join(self.data_path, "Data_TitleInfo.csv")
        self.student_df = pd.read_csv(student_info_path)
        self.title_df = pd.read_csv(title_info_path)

        # 加载所有班级的提交记录
        submitrecord_paths = glob.glob(os.path.join(self.data_path, "SubmitRecord-Class*.csv"))
        submit_df_list = []
        for path in submitrecord_paths:
            temp_df = pd.read_csv(path)
            submit_df_list.append(temp_df)
        self.submit_df = pd.concat(submit_df_list, ignore_index=True)

    def preprocess_data(self):
        """数据预处理"""
        # 判断答题是否完全正确
        self.submit_df["is_correct"] = self.submit_df["state"].apply(
            lambda x: 1 if "Absolutely_Correct" in x.strip() else 0
        )

        # 将答题用时从毫秒转换为秒
        self.submit_df["time_sec"] = self.submit_df["timeconsume"] / 1000.0

    def aggregate_data(self):
        """按班级聚合数据"""
        grouped_class = self.submit_df.groupby("class").agg(
            total_submissions=("index", "count"),      # 总提交次数
            avg_score=("score", "mean"),               # 平均得分
            accuracy=("is_correct", "mean"),           # 完全正确比例（准确率）
            avg_time_sec=("time_sec", "mean"),         # 平均答题时长（秒）
            unique_students=("student_ID", "nunique")  # 班级内独立学生数量
        ).reset_index()

        # 计算人均提交次数
        grouped_class["avg_submissions"] = grouped_class["total_submissions"] / grouped_class["unique_students"]
        self.grouped_class = grouped_class

    def normalize_data(self):
        """对指标进行归一化处理"""
        self.grouped_class["norm_avg_score"] = self.grouped_class["avg_score"] / self.grouped_class["avg_score"].max()
        self.grouped_class["norm_accuracy"] = self.grouped_class["accuracy"] / self.grouped_class["accuracy"].max()
        self.grouped_class["norm_avg_time_sec"] = self.grouped_class["avg_time_sec"] / self.grouped_class["avg_time_sec"].max()
        self.grouped_class["norm_avg_submissions"] = self.grouped_class["avg_submissions"] / self.grouped_class["avg_submissions"].max()
        self.grouped_class["norm_total_submissions"] = self.grouped_class["total_submissions"] / self.grouped_class["total_submissions"].max()

    def create_radar_chart(self, output_path=None):
        """创建雷达图"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "class_radar_5dims_normalized.html")

        # 定义雷达图指标
        schema = [
            {"name": "平均得分", "max": 1},
            {"name": "准确率", "max": 1},
            {"name": "平均答题时长", "max": 1},
            {"name": "人均提交数", "max": 1},
            {"name": "总提交数", "max": 1},
        ]

        # 初始化雷达图
        radar = Radar(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.LIGHT))
        radar.add_schema(
            schema=[opts.RadarIndicatorItem(name=item["name"], max_=item["max"]) for item in schema],
            splitarea_opt=opts.SplitAreaOpts(is_show=True)
        )

        # 定义颜色板
        color_palette = [
            "#c23531", "#2f4554", "#61a0a8", "#d48265", "#91c7ae",
            "#749f83", "#ca8622", "#bda29a", "#6e7074", "#546570",
            "#c4ccd3", "#f05b72", "#ef5b9c", "#f47920", "#905a3d"
        ]

        # 为每个班级添加数据系列
        for idx, row in self.grouped_class.iterrows():
            data_item = [
                row["norm_avg_score"],
                row["norm_accuracy"],
                row["norm_avg_time_sec"],
                row["norm_avg_submissions"],
                row["norm_total_submissions"]
            ]
            radar.add(
                series_name=f"Class{row['class']}",
                data=[data_item],
                areastyle_opts=opts.AreaStyleOpts(opacity=0),
                linestyle_opts=opts.LineStyleOpts(color=color_palette[idx % len(color_palette)]),
                symbol="circle"
            )

        # 设置提示和全局选项
        radar.set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(
                formatter=lambda params: 
                f"{params['seriesName']}<br/>"
                f"{schema[0]['name']}: {params['value'][0]:.2f}<br/>"
                f"{schema[1]['name']}: {params['value'][1]:.2f}<br/>"
                f"{schema[2]['name']}: {params['value'][2]:.2f}<br/>"
                f"{schema[3]['name']}: {params['value'][3]:.2f}<br/>"
                f"{schema[4]['name']}: {params['value'][4]:.2f}"
            )
        )

        radar.set_global_opts(
            title_opts=opts.TitleOpts(title="按班级对比的归一化学习行为雷达图 (5指标)"),
            legend_opts=opts.LegendOpts(pos_top="5%")
        )

        # 保存雷达图
        radar.render(output_path)
        print(f"Radar chart saved to: {output_path}")

    def visualize(self, output_path=None):
        """执行整个可视化流程"""
        self.load_data()
        self.preprocess_data()
        self.aggregate_data()
        self.normalize_data()
        self.create_radar_chart(output_path)
