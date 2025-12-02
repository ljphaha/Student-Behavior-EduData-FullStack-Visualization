<template>
    <div id="app">
        <div class="container">
            <header>
                <h1>可视化大屏</h1>
            </header>
            <main>
                <TheDashboard />
            </main>
        </div>
    </div>
</template>

<script>
    // 确保路径正确
    import TheDashboard from './views/TheDashboard.vue';

    export default {
        name: 'App',
        components: {
            TheDashboard
        }
    }
</script>

<style>
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    header {
        text-align: center;
        margin-bottom: 30px;
    }

    main {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
    }
</style>