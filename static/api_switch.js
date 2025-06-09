let sourceType = 'bus'; // 預設官方資料

function fetchEta(route, direction, updateUI = false) {
    let apiUrl = sourceType === 'bus'
        ? `/api/eta?route=${route}&direction=${direction}`
        : `/api/model_eta?route=${route}&direction=${direction}`;
    fetch(apiUrl)
        .then(res => res.json())
        .then(data => {
            // ...更新畫面...
        });
}

// 切換資料來源按鈕事件
document.getElementById('source-bus').addEventListener('click', function() {
    sourceType = 'bus';
    this.classList.add('active');
    document.getElementById('source-model').classList.remove('active');
    fetchEta(currentRoute, currentDirection, true);
});
document.getElementById('source-model').addEventListener('click', function() {
    sourceType = 'model';
    this.classList.add('active');
    document.getElementById('source-bus').classList.remove('active');
    fetchEta(currentRoute, currentDirection, true);
});

document.getElementById('direction-go').addEventListener('click', function() {
    if (!this.classList.contains('active')) {
        currentDirection = "0";
        fetchEta(currentRoute, currentDirection, true);
        startAutoUpdate();
    }
});
document.getElementById('direction-back').addEventListener('click', function() {
    if (!this.classList.contains('active')) {
        currentDirection = "1";
        fetchEta(currentRoute, currentDirection, true);
        startAutoUpdate();
    }
});