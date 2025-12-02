<template>
    <div class="dashboard">
        <h2>学习行为分析</h2>
        <div class="grid-container">
            <!-- 图表 1 -->
            <div class="grid-item scale-container">
                <iframe :src="src1"></iframe>
            </div>
            <!-- 图表 2 -->
            <div class="grid-item scale-container">
                <iframe :src="src2"></iframe>
            </div>
            <!-- 图表 3 -->
            <div class="grid-item scale-container">
                <iframe :src="src3"></iframe>
            </div>
            <!-- 图表 4 -->
            <div class="grid-item scale-container">
                <iframe :src="src4"></iframe>
            </div>
            <!-- 图表 5 -->
            <div class="grid-item scale-container">
                <iframe :src="src5"></iframe>
            </div>
            <!-- 图表 6 -->
            <div class="grid-item scale-container">
                <iframe :src="src6"></iframe>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: 'TheDashboard',
        data() {
            return {
                src1: "/data/knowledge_heatmap.html",
                src2: "/data/class_radar_5dims_normalized.html",
                src3: "/data/student_behavior_3d_clusters.html",
                src4: "/data/knowledge_method_scatter3d_tab.html",
                src5: "/data/network_graph.html",
                src6: "/data/all_classes_timeline_tab.html"
            }
        },
    }
</script>

<style>
    /* 白底 + 深色文字 */
    html, body {
        margin: 0;
        padding: 0;
        background-color: #fff;
        color: #333;
        font-family: sans-serif;
        height: 100%;
    }

    .dashboard {
        width: 100%;
        min-height: 100vh;
        padding: 20px;
        box-sizing: border-box;
    }

        .dashboard h2 {
            text-align: center;
            margin-bottom: 20px;
            font-weight: normal;
        }

    /* Grid 布局 */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        grid-template-rows: 400px 400px;
        gap: 20px;
        max-width: 1920px;
        margin: 0 auto;
    }

    .grid-item {
        background-color: #fafafa;
        border: 1px solid #ddd;
        border-radius: 8px;
        position: relative;
        overflow: hidden;
    }

    /* 用 transform 强制缩放 */
    .scale-container {
        /* 先给容器固定大小，然后内部iframe超出时不会出现滚动条 */
    }

        /* 让 iframe 占据一个原始“画布”，再整体缩放 */
        .scale-container iframe {
            width: 800px; /* 假设iframe内容默认是800宽 */
            height: 600px; /* 假设iframe内容默认是600高 */
            transform: scale(0.5); /* 缩放到 50% */
            transform-origin: top left; /* 以左上角为基准缩放 */
            border: none;
        }

            /* 隐藏滚动条 */
            .scale-container iframe::-webkit-scrollbar {
                display: none;
            }
</style>
