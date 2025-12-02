import os
import glob
import pandas as pd
from pyecharts.charts import Graph
from pyecharts import options as opts

class NetworkGraphVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df_title = None
        self.df_student = None
        self.df_submit = None
        self.nodes = []
        self.edges = []
        self.categories = [
            {"name": "题目"},
            {"name": "知识点"}
        ]

    def load_data(self):
        """加载数据"""
        # 加载题目基本信息
        title_path = os.path.join(self.data_path, "Data_TitleInfo.csv")
        self.df_title = pd.read_csv(title_path)

        # 加载学生基本信息（可选）
        student_path = os.path.join(self.data_path, "Data_StudentInfo.csv")
        if os.path.exists(student_path):
            self.df_student = pd.read_csv(student_path)

        # 加载所有班级的提交记录
        submit_paths = glob.glob(os.path.join(self.data_path, "SubmitRecord-Class*.csv"))
        submit_list = []
        for path in submit_paths:
            temp = pd.read_csv(path)
            submit_list.append(temp)
        self.df_submit = pd.concat(submit_list, ignore_index=True)

    def calculate_submission_counts(self):
        """统计每道题目的提交次数"""
        submission_counts = self.df_submit.groupby("title_ID").size().reset_index(name="submission_count")
        self.df_title = pd.merge(self.df_title, submission_counts, on="title_ID", how="left")
        self.df_title["submission_count"] = self.df_title["submission_count"].fillna(0)

    def construct_nodes_and_edges(self):
        """构造节点和边"""
        nodes_dict = {}  # key: 节点id, value: 节点信息
        edges = []       # 列表存储边

        # 遍历每个题目记录
        for _, row in self.df_title.iterrows():
            title_id = str(row["title_ID"])
            submission_count = row["submission_count"]

            # 添加题目节点
            size = 10 if submission_count == 0 else min(30, 10 + submission_count / 10)
            if title_id not in nodes_dict:
                nodes_dict[title_id] = {
                    "id": title_id,
                    "name": f"题目 {title_id}",
                    "category": 0,
                    "symbolSize": size
                }

            # 解析 knowledge 字段
            knowledge_field = row.get("knowledge")
            if pd.notnull(knowledge_field):
                knowledge_list = [k.strip() for k in str(knowledge_field).split(",") if k.strip()]
                for know in knowledge_list:
                    # 添加知识点节点
                    if know not in nodes_dict:
                        nodes_dict[know] = {
                            "id": know,
                            "name": f"知识点 {know}",
                            "category": 1,
                            "symbolSize": 20
                        }
                    # 添加边
                    edges.append({
                        "source": title_id,
                        "target": know,
                        "value": submission_count
                    })

        self.nodes = list(nodes_dict.values())
        self.edges = edges

    def create_network_graph(self, output_path=None):
        """创建网络图"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "network_graph.html")

        graph = (
            Graph(init_opts=opts.InitOpts(width="1200px", height="800px"))
            .add(
                "",
                self.nodes,
                self.edges,
                categories=self.categories,
                repulsion=800,
                edge_length=[10, 50],
                label_opts=opts.LabelOpts(is_show=True, position="right")
            )
            .set_global_opts(title_opts=opts.TitleOpts(title="题目与知识点关联网络图"))
        )

        graph.render(output_path)
        print(f"Network graph saved to: {output_path}")

    def visualize(self, output_path=None):
        """执行整个可视化流程"""
        self.load_data()
        self.calculate_submission_counts()
        self.construct_nodes_and_edges()
        self.create_network_graph(output_path)
