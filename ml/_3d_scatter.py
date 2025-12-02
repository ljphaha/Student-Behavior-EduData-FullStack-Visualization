import os
import glob
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from pyecharts.charts import Scatter3D
from pyecharts import options as opts
from pyecharts.globals import ThemeType

class StudentBehaviorClusterVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.submit_df = None
        self.features = None
        self.student_info = None
        self.cluster_centers = None

    def load_data(self):
        """加载所有班级的提交记录数据"""
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
            lambda x: 1 if "Absolutely_Correct" in str(x).strip() else 0
        )

    def aggregate_features(self):
        """按学员聚合特征"""
        self.features = self.submit_df.groupby("student_ID").agg(
            submission_count=("index", "count"),  # 提交次数
            avg_score=("score", "mean"),          # 平均得分
            accuracy=("is_correct", "mean")       # 正确率
        ).reset_index()

        # 如果有学员基本信息，可以合并
        student_info_path = os.path.join(self.data_path, "Data_StudentInfo.csv")
        if os.path.exists(student_info_path):
            self.student_info = pd.read_csv(student_info_path)
            self.features = pd.merge(self.features, self.student_info, on="student_ID", how="left")

    def standardize_features(self):
        """对特征进行标准化"""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.features[["submission_count", "avg_score", "accuracy"]])
        return X_scaled

    def perform_clustering(self, n_clusters=3, random_state=42):
        """执行KMeans聚类"""
        X_scaled = self.standardize_features()
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
        self.features["cluster"] = kmeans.fit_predict(X_scaled)
        self.cluster_centers = kmeans.cluster_centers_

    def prepare_3d_data(self):
        """准备3D散点图数据"""
        data_3d = []
        for _, row in self.features.iterrows():
            data_3d.append([
                row["submission_count"], 
                row["avg_score"], 
                row["accuracy"], 
                row["cluster"],
                row["student_ID"]
            ])
        return data_3d

    def create_3d_scatter(self, data_3d, output_path=None):
        """创建3D散点图"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "student_behavior_3d_clusters.html")

        # 定义颜色板
        color_palette = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]

        scatter3d = Scatter3D(
            init_opts=opts.InitOpts(width="1000px", height="700px", theme=ThemeType.LIGHT, bg_color="white")
        )

        # 将数据按照聚类分组添加
        for cl in sorted(self.features["cluster"].unique()):
            cluster_data = [d for d in data_3d if d[3] == cl]
            data_points = [[d[0], d[1], d[2]] for d in cluster_data]

            scatter3d.add(
                series_name=f"Cluster {cl}",
                data=data_points,
                xaxis3d_opts=opts.Axis3DOpts(name="提交次数"),
                yaxis3d_opts=opts.Axis3DOpts(name="平均得分"),
                zaxis3d_opts=opts.Axis3DOpts(name="正确率"),
                itemstyle_opts=opts.ItemStyleOpts(color=color_palette[cl % len(color_palette)])
            )

        # 设置全局配置
        scatter3d.set_global_opts(
            title_opts=opts.TitleOpts(title="基于代表性指标的 3D 聚类图"),
            tooltip_opts=opts.TooltipOpts(
                formatter="{a} <br/>{b}: ({c})"
            )
        )

        # 保存图表
        scatter3d.render(output_path)
        print(f"3D scatter plot saved to: {output_path}")

    def visualize(self, n_clusters=3, output_path=None):
        """执行整个可视化流程"""
        self.load_data()
        self.preprocess_data()
        self.aggregate_features()
        self.perform_clustering(n_clusters=n_clusters)
        data_3d = self.prepare_3d_data()
        self.create_3d_scatter(data_3d, output_path)
