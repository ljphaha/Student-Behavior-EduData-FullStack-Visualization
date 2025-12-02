import os
import glob
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, Timeline
from pyecharts.globals import ThemeType

class TimelineVisualizer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.submit_df = None

    def load_data(self):
        """加载并合并所有班级数据"""
        # 获取所有提交记录文件路径
        submitrecord_paths = glob.glob(os.path.join(self.data_path, "SubmitRecord-Class*.csv"))
        submit_df_list = []
        
        for path in submitrecord_paths:
            # 读取CSV
            temp_df = pd.read_csv(path)
            
            # 健壮性处理：如果CSV里没有'class'列，尝试从文件名解析 (e.g., "SubmitRecord-Class1.csv")
            if 'class' not in temp_df.columns:
                basename = os.path.basename(path)
                # 提取数字部分，拼凑成 'Class1' 格式
                class_num = ''.join(filter(str.isdigit, basename))
                temp_df['class'] = f"Class{class_num}" if class_num else "Unknown"
            
            submit_df_list.append(temp_df)
            
        if not submit_df_list:
             raise FileNotFoundError("未找到任何 SubmitRecord-Class*.csv 文件，请检查 data 目录。")

        self.submit_df = pd.concat(submit_df_list, ignore_index=True)

    def preprocess_data(self):
        """处理时间数据"""
        # 确保 time 列存在
        if 'time' not in self.submit_df.columns:
            return

        # 将时间戳转换为日期字符串 (YYYY-MM-DD)
        # 假设 time 是 Unix 时间戳 (秒)
        self.submit_df['date'] = pd.to_datetime(self.submit_df['time'], unit='s').dt.strftime('%Y-%m-%d')
        
        # 确保 class 列是字符串类型，方便排序
        self.submit_df['class'] = self.submit_df['class'].astype(str)

    def generate_timeline(self, output_path):
        """生成时间轮播图：按日期展示各班级的提交量"""
        # 1. 数据聚合：统计每天、每班的提交量
        data_agg = self.submit_df.groupby(['date', 'class']).size().reset_index(name='count')
        
        # 2. 准备基础数据
        dates = sorted(data_agg['date'].unique()) # 所有日期（时间轴刻度）
        
        # 获取所有班级并进行自然排序 (Class1, Class2 ... Class10)
        classes = sorted(data_agg['class'].unique(), key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 0)

        # 3. 创建时间轴组件
        tl = Timeline(init_opts=opts.InitOpts(width="100%", height="500px", theme=ThemeType.LIGHT))
        tl.add_schema(
            play_interval=1000,   # 播放速度 1000ms
            is_auto_play=True,    # 自动播放
            is_loop_play=True,    # 循环播放
            pos_bottom="-5px"     # 时间轴位置
        )

        # 4. 循环每一天，创建对应的柱状图
        for d in dates:
            day_data = data_agg[data_agg['date'] == d]
            
            # 数据补全：保证这一天的柱状图包含所有班级（没有数据的班级填0）
            counts = []
            for c in classes:
                val = day_data[day_data['class'] == c]['count'].values
                counts.append(int(val[0]) if len(val) > 0 else 0)

            # 创建当天的柱状图
            bar = (
                Bar()
                .add_xaxis(classes)
                .add_yaxis("提交次数", counts, label_opts=opts.LabelOpts(is_show=False)) # 隐藏柱上数字，保持整洁
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title=f"{d} 各班级提交活跃度",
                        subtitle="提交量趋势分析"
                    ),
                    yaxis_opts=opts.AxisOpts(name="提交量"),
                    xaxis_opts=opts.AxisOpts(
                        name="班级", 
                        axislabel_opts=opts.LabelOpts(rotate=45) # 班级名倾斜防止重叠
                    ),
                    legend_opts=opts.LegendOpts(is_show=False) # 只有一个系列，不需要图例
                )
            )
            tl.add(bar, "{}".format(d))

        # 5. 保存结果
        tl.render(output_path)
        print(f"Timeline visualization saved to: {output_path}")

    def visualize(self, output_path=None):
        """执行流程接口"""
        if output_path is None:
            output_path = os.path.join(self.data_path, "all_classes_timeline_tab.html")
            
        self.load_data()
        self.preprocess_data()
        self.generate_timeline(output_path)