import os
import glob
import pandas as pd
import numpy as np
import xgboost as xgb
import graphviz
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from pyecharts.charts import Bar
from pyecharts import options as opts

class XGBoostModelVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.submit_df = None
        self.features = None
        self.model = None
        self.importance_df = None

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

        # 对 timeconsume 做对数变换
        self.submit_df["log_time"] = np.log1p(self.submit_df["timeconsume"])

        # 将 time 字段转换为日期
        self.submit_df["date"] = pd.to_datetime(self.submit_df["time"], unit="s").dt.date

    def aggregate_features(self):
        """按学员聚合特征"""
        # 聚合基本特征
        agg_features = self.submit_df.groupby("student_ID").agg(
            submission_count=("index", "count"),
            accuracy=("is_correct", "mean"),
            avg_log_time=("log_time", "mean")
        ).reset_index()

        # 计算活跃天数
        active_days = self.submit_df.groupby("student_ID")["date"].nunique().reset_index().rename(columns={"date": "active_days"})
        features = pd.merge(agg_features, active_days, on="student_ID", how="left")
        features["avg_submissions_per_day"] = features["submission_count"] / features["active_days"]

        # 计算平均得分
        score_features = self.submit_df.groupby("student_ID").agg(
            avg_score=("score", "mean")
        ).reset_index()
        features = pd.merge(features, score_features, on="student_ID", how="left")

        # 构造目标变量
        median_score = features["avg_score"].median()
        features["knowledge_mastery"] = (features["avg_score"] > median_score).astype(int)

        self.features = features

    def train_model(self, test_size=0.2, random_state=42):
        """训练 XGBoost 模型"""
        # 准备输入特征和目标变量
        input_features = ["submission_count", "accuracy", "avg_log_time", "active_days", "avg_submissions_per_day"]
        X = self.features[input_features]
        y = self.features["knowledge_mastery"]

        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, random_state=random_state)

        # 构造 DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=input_features)
        dtest = xgb.DMatrix(X_test, label=y_test, feature_names=input_features)

        # 训练模型
        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "eta": 0.1,
            "max_depth": 4,
            "seed": 42,
        }
        num_round = 100
        self.model = xgb.train(params, dtrain, num_boost_round=num_round)

        # 评估模型
        y_pred_prob = self.model.predict(dtest)
        y_pred = (y_pred_prob > 0.5).astype(int)
        acc = accuracy_score(y_test, y_pred)
        print(f"Test Accuracy: {acc * 100:.2f}%")

    def visualize_tree(self, output_path=None):
        """可视化决策树"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "xgb_tree.png")

        # 可视化第0棵树
        dot = xgb.to_graphviz(self.model, num_trees=0)
        dot.format = "png"
        dot.render(filename=os.path.splitext(output_path)[0], cleanup=True)
        return output_path

    def visualize_feature_importance(self):
        """可视化特征重要性"""
        # 获取特征重要性
        importance = self.model.get_score(importance_type="gain")
        self.importance_df = pd.DataFrame({
            "feature": list(importance.keys()),
            "importance": list(importance.values())
        }).sort_values("importance", ascending=False)

        # 创建柱状图
        color_list = ["#c23531", "#2f4554", "#61a0a8", "#d48265", "#91c7ae", "#749f83", "#ca8622"]
        bar = Bar()
        bar.add_xaxis(self.importance_df["feature"].tolist())

        # 为每个柱子设置不同颜色
        y_data_with_color = []
        for i, imp in enumerate(self.importance_df["importance"]):
            c = color_list[i % len(color_list)]
            y_data_with_color.append(
                opts.BarItem(
                    name=self.importance_df["feature"].iloc[i],
                    value=imp,
                    itemstyle_opts=opts.ItemStyleOpts(color=c)
                )
            )

        bar.add_yaxis(
            series_name="Feature Importance",
            y_axis=y_data_with_color
        )

        bar.set_global_opts(
            title_opts=opts.TitleOpts(title="XGBoost Feature Importance"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=20)),
            yaxis_opts=opts.AxisOpts(name="Importance"),
        )

        return bar.render_embed()

    def create_html(self, output_path=None):
        """创建组合的 HTML 文件"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "xgb_model_visualization.html")

        # 获取特征重要性可视化和决策树路径
        bar_html = self.visualize_feature_importance()
        tree_path = self.visualize_tree()

        # 组合 HTML 内容
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>XGBoost Model Visualization</title>
        </head>
        <body>
            <h1>XGBoost Model Visualization</h1>
            <div>{bar_html}</div>
            <hr>
            <div style="text-align:center;">
                <h2>XGBoost Tree (Tree 0)</h2>
                <img src="{os.path.basename(tree_path)}" style="max-width:100%;"/>
            </div>
        </body>
        </html>
        """

        # 保存 HTML 文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Visualization saved to: {output_path}")

    def visualize(self, output_path=None):
        """执行整个可视化流程"""
        self.load_data()
        self.preprocess_data()
        self.aggregate_features()
        self.train_model()
        self.create_html(output_path)
