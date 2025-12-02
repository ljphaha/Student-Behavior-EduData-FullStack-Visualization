import os
import glob
import pandas as pd
import dash
from dash import html
from flask import Flask, send_from_directory

# 获取当前项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(project_root, "data")
result_dir = os.path.join(project_root, "results")

# 初始化 Flask 应用
server = Flask(__name__, static_folder=os.path.join(project_root, 'frontend', 'public'), template_folder=os.path.join(project_root, 'frontend', 'public'))

# 生成可视化文件
def generate_visualizations():
    # 加载数据
    student_info_path = os.path.join(data_dir, 'Data_StudentInfo.csv')
    title_info_path = os.path.join(data_dir, 'Data_TitleInfo.csv')
    submitrecord_paths = glob.glob(os.path.join(data_dir, "SubmitRecord-Class*.csv"))
    
    # 检查文件是否存在
    if not os.path.exists(student_info_path):
        raise FileNotFoundError(f"文件 {student_info_path} 不存在，请检查路径。")
    if not os.path.exists(title_info_path):
        raise FileNotFoundError(f"文件 {title_info_path} 不存在，请检查路径。")
    if not submitrecord_paths:
        raise FileNotFoundError(f"没有找到提交记录文件，请检查路径。")

    print(f"学生信息文件路径: {student_info_path}")
    print(f"题目信息文件路径: {title_info_path}")
    print(f"提交记录文件路径: {submitrecord_paths}")

    student_df = pd.read_csv(student_info_path)
    title_df = pd.read_csv(title_info_path)
    submit_df_list = []
    for path in submitrecord_paths:
        if os.path.exists(path):
            print(f"加载文件: {path}")
            temp_df = pd.read_csv(path)
            if temp_df.empty:
                print(f"警告：文件 {path} 为空，跳过。")
            else:
                submit_df_list.append(temp_df)
        else:
            print(f"警告：文件 {path} 不存在，跳过。")
    submit_df = pd.concat(submit_df_list, ignore_index=True)
    
    # 检查提交记录数据是否为空
    if submit_df.empty:
        raise ValueError("提交记录数据为空，请检查文件路径和内容。")
    
    # 1. 知识点热力图
    from ml.knowledge_heatmap import DataVisualizer
    visualizer = DataVisualizer(student_df, title_df, submit_df, data_dir)
    output_path = os.path.join(result_dir, "knowledge_heatmap.html")
    visualizer.visualize(output_path=output_path)
    
    # 检查文件是否生成
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"文件 {output_path} 未生成，请检查代码逻辑。")
    print(f"热力图已成功生成并保存到 {output_path}")

    # 2. 雷达图
    from ml.radar_chart import ClassRadarVisualizer
    radar_visualizer = ClassRadarVisualizer(data_dir)
    radar_output_path = os.path.join(result_dir, "class_radar_5dims_normalized.html")
    radar_visualizer.visualize(output_path=radar_output_path)
    
    # 3. 3D 散点图
    from ml._3d_scatter import StudentBehaviorClusterVisualizer
    cluster_visualizer = StudentBehaviorClusterVisualizer(data_dir)
    cluster_output_path = os.path.join(result_dir, "student_behavior_3d_clusters.html")
    cluster_visualizer.visualize(output_path=cluster_output_path)
    
    # 4. XGBoost 模型可视化
    from ml.Xgboost import XGBoostModelVisualizer
    xgboost_visualizer = XGBoostModelVisualizer(data_dir)
    xgboost_output_path = os.path.join(result_dir, "xgb_model_visualization.html")
    xgboost_visualizer.visualize(output_path=xgboost_output_path)
    
    # 5. 网络图
    from ml.network import NetworkGraphVisualizer
    network_visualizer = NetworkGraphVisualizer(data_dir)
    network_output_path = os.path.join(result_dir, "network_graph.html")
    network_visualizer.visualize(output_path=network_output_path)

    # 6. 生成时间线图表 
    from ml.timeline import TimelineVisualizer
    timeline_visualizer = TimelineVisualizer(data_dir)
    timeline_output_path = os.path.join(result_dir, "all_classes_timeline_tab.html")
    timeline_visualizer.visualize(output_path=timeline_output_path)

# 初始化 Dash 应用
dash_app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dash/'
)

# 设置 Dash 布局
# 设置 Dash 布局
def setup_dash_layout():
    # 确保文件已生成
    required_files = [
        "knowledge_heatmap.html",
        "class_radar_5dims_normalized.html",
        "student_behavior_3d_clusters.html",
        "xgb_model_visualization.html",
        "network_graph.html",
        "all_classes_timeline_tab.html"  
    ]
    for file_name in required_files:
        file_path = os.path.join(result_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 未生成，请检查代码逻辑。")
    
    dash_app.layout = html.Div([
        html.H1("可视化大屏", style={"textAlign": "center", "marginBottom": "30px"}),
        
        # 第一行：3 个图表
        html.Div([
            # 图表 1：知识点热力图
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "knowledge_heatmap.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'}),
            
            # 图表 2：雷达图
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "class_radar_5dims_normalized.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'}),
            
            # 图表 3：3D 散点图
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "student_behavior_3d_clusters.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}),
        
        # 第二行：3 个图表
        html.Div([
            # 图表 4：XGBoost 模型可视化
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "xgb_model_visualization.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'}),
            
            # 图表 5：网络图
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "network_graph.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'}),
            
            # 图表 6：时间线标签图
            html.Div([
                html.Iframe(srcDoc=open(os.path.join(data_dir, "all_classes_timeline_tab.html"), "r", encoding="utf-8").read(), width="100%", height="400px")
            ], style={'flex': '1', 'margin': '10px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ])
# Flask 路由
@server.route('/')
def serve_vue():
    return send_from_directory(os.path.join(project_root, 'frontend', 'public'), 'index.html')

# 运行 Flask 应用
if __name__ == '__main__':
    generate_visualizations()
    setup_dash_layout()
    server.run(debug=True)