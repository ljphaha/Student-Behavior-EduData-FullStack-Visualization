import pandas as pd
import plotly.express as px
import os

class DataVisualizer:
    def __init__(self, student_df, title_df, submit_df, data_path):
        self.student_df = student_df
        self.title_df = title_df
        self.submit_df = submit_df
        self.data_path = data_path  # 添加 data_path 属性
        self.merged = None

    def load_data(self):
        """加载数据"""
        # 初始化 submit_df 为一个空的 DataFrame
        submit_df = pd.DataFrame()

        # 加载提交记录数据（合并所有班级的CSV文件）
        for class_num in range(1, 16):
            file_path = os.path.join(self.data_path, f'SubmitRecord-Class{class_num}.csv')
            print(f"尝试加载文件: {file_path}")  # 添加调试信息
            if os.path.exists(file_path):
                class_df = pd.read_csv(file_path)
                # 检查class列是否存在
                if 'class' not in class_df.columns:
                    raise KeyError(f"文件 {file_path} 中缺少 'class' 列，请检查数据结构。")
                submit_df = pd.concat([submit_df, class_df], ignore_index=True)
            else:
                print(f"警告：文件 {file_path} 不存在，跳过。")
    
        # 检查 submit_df 是否为空
        if submit_df.empty:
            raise ValueError("提交记录数据为空，请检查文件路径和内容。")
    
        self.submit_df = submit_df

    def clean_data(self):
        """清洗数据"""
        # 清洗无效专业
        valid_majors = self.student_df['major'].str.match(r'^J\d{5}$', na=False)
        self.student_df = self.student_df[valid_majors].copy()

        # 处理班级排序
        self.submit_df['class'] = pd.Categorical(
            self.submit_df['class'], 
            categories=[f'Class{i}' for i in range(1, 16)], 
            ordered=True
        )

    def merge_data(self):
        """合并数据"""
        # 避免列名冲突：仅保留submit_df的score
        self.merged = (
            self.submit_df.merge(self.student_df, on='student_ID', how='left')
            .merge(self.title_df[['title_ID', 'knowledge', 'sub_knowledge']], 
                   on='title_ID', how='left')
        )

    def extract_knowledge_hierarchy(self):
        """提取知识点层级"""
        # 从sub_knowledge中拆分主知识点
        self.merged[['knowledge_main', 'sub_knowledge_detail']] = (
            self.merged['sub_knowledge'].str.split('_', n=1, expand=True)
        )

    def filter_invalid_data(self):
        """过滤无效数据"""
        # 移除无知识点或得分异常的记录
        self.merged = self.merged[
            (self.merged['knowledge_main'].notna()) & 
            (self.merged['sub_knowledge_detail'].notna()) & 
            (self.merged['score'] > 0)  # 过滤0分记录
        ]

    def aggregate_data(self):
        """按班级、专业、知识点聚合平均得分"""
        agg_df = (
            self.merged.groupby(['class', 'major', 'knowledge_main', 'sub_knowledge_detail'])
            ['score'].mean()
            .reset_index()
        )
        return agg_df

    def generate_heatmap(self, agg_df, output_path):
        """生成分面热力图"""
        fig = px.density_heatmap(
            agg_df,
            x='sub_knowledge_detail',
            y='knowledge_main',
            z='score',
            facet_row='class',  # 纵向分面：班级
            facet_col='major',  # 横向分面：专业
            color_continuous_scale='RdYlGn',
            range_color=[0, self.merged['score'].max()],
            category_orders={
                'class': [f'Class{i}' for i in range(1, 16)],  # 强制班级顺序
                'major': sorted(self.merged['major'].unique())  # 专业按字母排序
            },
            labels={
                'sub_knowledge_detail': '子知识点',
                'knowledge_main': '主知识点',
                'score': '平均得分'
            },
            height=3000  # 根据班级数量调整
        )

        # 优化布局
        fig.update_layout(
            title_text='各班级-专业知识点掌握热力图',
            margin=dict(l=150, r=50, t=100, b=50),
            xaxis=dict(tickangle=45, automargin=True),
            yaxis=dict(automargin=True)
        )

        # 保存为HTML
        fig.write_html(output_path)

    def visualize(self, output_path="knowledge_heatmap.html"):
        """执行整个可视化流程"""
        self.load_data()
        self.clean_data()
        self.merge_data()
        self.extract_knowledge_hierarchy()
        self.filter_invalid_data()
        agg_df = self.aggregate_data()
        self.generate_heatmap(agg_df, output_path)

# 使用示例
if __name__ == "__main__":
    try:
        # 创建可视化对象并生成热力图
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        visualizer = DataVisualizer(
            pd.read_csv(os.path.join(data_dir, 'Data_StudentInfo.csv')),
            pd.read_csv(os.path.join(data_dir, 'Data_TitleInfo.csv')),
            pd.DataFrame(),
            data_dir  # 传递 data_dir 作为 data_path
        )
        output_path = os.path.join(data_dir, "knowledge_heatmap.html")
        visualizer.visualize(output_path=output_path)
        
        # 检查文件是否生成
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"文件 {output_path} 未生成，请检查代码逻辑。")
        print(f"热力图已成功生成并保存到 {output_path}")
    except Exception as e:
        print(f"发生错误：{e}")