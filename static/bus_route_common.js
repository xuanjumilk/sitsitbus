function setActiveButton(direction) {
    const goBtn = document.getElementById('direction-go');
    const backBtn = document.getElementById('direction-back');
    if (direction === "0") {
        goBtn.classList.add('active');
        backBtn.classList.remove('active');
    } else {
        goBtn.classList.remove('active');
        backBtn.classList.add('active');
    }
}

// 頁面載入時取得 skin_id
window.currentSkinId = 1;
fetch('/skin/get_skin')
    .then(res => res.json())
    .then(data => {
        window.currentSkinId = data.skin_id || 1;
    });

// 根據 skin_id 和方向產生 bus 圖片
// isLeft: true 代表右向(去程)，false 代表左向(返程)
function getBusImgTag(isLeft) {
    const skinId = window.currentSkinId || 1;
    const dir = isLeft ? 'right' : 'left';
    return `<img src="/static/skins/skin${skinId}_${dir}.gif" class="bus-img" style="width:28px;height:17px;">`;
}

function fetchEta(route, direction, isInit = false) {
    currentRoute = route;
    currentDirection = direction;
    setActiveButton(direction);
    const directionText = direction === "0" ? "去程" : "返程";

    const routeData = allStopNames[route];
    if (!routeData) {
        document.getElementById('route-map').innerHTML = '找不到該路線的資料';
        return;
    }
    const stopGroups = routeData[direction];
    if (!stopGroups || stopGroups.length === 0) {
        document.getElementById('route-map').innerHTML = `找不到路線 ${route} 方向 ${directionText} 的站牌資訊`;
        return;
    }

    // 根據 sourceType 切換 API
    let apiUrl;
    if (typeof sourceType !== 'undefined' && sourceType === 'model') {
        apiUrl = `/model/api/model_eta?route=${route}&direction=${direction}`;
    } else {
        apiUrl = `/bus/api/eta?route=${route}&direction=${direction}`;
    }

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (currentRoute !== route || currentDirection !== direction) return;

            let html = '<div id="plMapStops" class="map_stops">';
            let globalIndex = 0;
            for (let row = 0; row < stopGroups.length; row++) {
                let group = stopGroups[row];
                // 判斷是否為最後一行
                let isLastRow = (row === stopGroups.length - 1);
                // 計算本行"space"數量
                let spaceCount = group.filter(x => x === "space").length;

                // 補空白格：奇數行插前面，偶數行插行尾
                if (isLastRow && spaceCount > 0) {
                    if (row % 2 === 0) {
                        // 偶數行：空白格插在行尾，稍後處理
                    } else {
                        // 奇數行：空白格插在行首
                        for (let i = 0; i < spaceCount; i++) {
                            html += `<div class="sm left" style="visibility:hidden"></div>`;
                        }
                    }
                }

                for (let col = 0; col < group.length; col++) {
                    const item = group[col];

                    // 補齊空白格，讓最後一行對齊
                    if (item === "space") {
                        // 已在最前面補過空白格，這裡不再插入
                        continue;
                    }

                    // 判斷是否為第一個站點
                    let isFirst = false;
                    if (row === 0) {
                        let firstRealIdx = group.findIndex(x =>
                            x !== "head" && x !== "tail" &&
                            x !== "right_down" && x !== "down_left" &&
                            x !== "left_down" && x !== "down_right" && x !== "space"
                        );
                        if (col === firstRealIdx) isFirst = true;
                    }

                    // 判斷是否為最後一站（本行左右有 "tail" 標籤即為最後一站）
                    let isLast = false;
                    if (
                        (col > 0 && group[col - 1] === "tail") ||
                        (col < group.length - 1 && group[col + 1] === "tail")
                    ) {
                        isLast = true;
                    }
                    // 若自己就是最後一個元素且自己前面是 tail，也要判斷
                    if (
                        (col === group.length - 1 && group.length > 1 && group[col - 1] === "tail")
                    ) {
                        isLast = true;
                    }
                    // 若自己就是第一個元素且自己後面是 tail，也要判斷
                    if (
                        (col === 0 && group.length > 1 && group[1] === "tail")
                    ) {
                        isLast = true;
                    }

                    // 插入轉折標籤，依資料順序，並與站點同層
                    if (item === "right_down") {
                        html += `<div class="srt left" style="position:relative;display:block;float:left;"></div>`;
                        continue;
                    }
                    if (item === "down_left") {
                        html += `<div class="srb right" style="position:relative;display:block;float:left;top:0;"></div>`;
                        continue;
                    }
                    if (item === "left_down") {
                        html += `<div class="slt right" style="position:relative;display:block;float:left;"></div>`;
                        continue;
                    }
                    if (item === "down_right") {
                        html += `<div class="slb left" style="position:relative;display:block;float:left;top:0;"></div>`;
                        continue;
                    }
                    if (item === "head" || item === "tail") continue;

                    // 取得站點資料
                    const stopName = item;
                    const stopData = data.find(item => item.stop_name === stopName);

                    // 預估到站時間（根據不同API格式）
                    let etaText = '';
                    if (stopData) {
                        // 先檢查站牌狀態代碼
                        if ('stop_status' in stopData && stopData.stop_status !== 0) {
                            // 非正常狀態，顯示狀態文字
                            switch (stopData.stop_status) {
                                case 1:
                                    etaText = '尚未發車';
                                    break;
                                case 2:
                                    etaText = '交管不停靠';
                                    break;
                                case 3:
                                    etaText = '末班車已過';
                                    break;
                                case 4:
                                    etaText = '今日未營運';
                                    break;
                                default:
                                    etaText = stopData.stop_status_text || '未知狀態';
                            }
                        } else if ('wait' in stopData && stopData.wait !== null) {
                            // model 預測
                            if (stopData.wait <= 30) {
                                etaText = '進站中';
                            } else {
                                etaText = `約${Math.round(stopData.wait / 60)}分`;
                            }
                        } else if ('minutes' in stopData && stopData.minutes !== null && stopData.seconds !== null) {
                            // 官方 ETA
                            if (stopData.minutes * 60 + stopData.seconds <= 30) {
                                etaText = '進站中';
                            } else {
                                etaText = `約${stopData.minutes}分`;
                            }
                        }
                    }

                    // block_x id 必須用 globalIndex，確保與資料順序一致
                    let stopClass = '';
                    let stopId = '';
                    let snzClass = '';
                    let sflagClass = '';
                    let siconClass = '';
                    let etaClass = '';
                    let busiClass = '';

                    if (isFirst) {
                        stopClass = 'sb left';
                        stopId = 'block_0';
                        snzClass = 'snz';
                        sflagClass = 'sflag';
                        siconClass = 'sicon-endpoint';
                        etaClass = 'eta';
                        busiClass = 'busi';
                    } else if (isLast && row % 2 === 0) {
                        // 偶數行最後一站靠左對齊
                        stopClass = 'se left';
                        stopId = `block_${globalIndex}`;
                        snzClass = 'snz';
                        sflagClass = 'sflag';
                        siconClass = 'sicon-endpoint';
                        etaClass = 'eta';
                        busiClass = 'busi';
                    } else if (isLast) {
                        // 奇數行最後一站（如有特殊需求可再補充）
                        stopClass = 'se2 right';
                        stopId = `block_${globalIndex}`;
                        snzClass = 'snz2';
                        sflagClass = 'sflag2';
                        siconClass = 'sicon2-endpoint';
                        etaClass = 'eta2';
                        busiClass = 'busi2';
                    } else if (row % 2 === 0) {
                        stopClass = 'sm left';
                        stopId = `block_${globalIndex}`;
                        snzClass = 'snz';
                        sflagClass = 'sflag';
                        siconClass = 'sicon';
                        etaClass = 'eta';
                        busiClass = 'busi';
                    } else {
                        stopClass = 'sm right';
                        stopId = `block_${globalIndex}`;
                        snzClass = 'snz2';
                        sflagClass = 'sflag2';
                        siconClass = 'sicon2';
                        etaClass = 'eta2';
                        busiClass = 'busi2';
                    }

                    // 決定左右方向
                    let isLeft = row % 2 === 0;
                    let busoClass = isLeft ? 'buso' : 'buso2';
                    let bpniClass = isLeft ? 'bpni' : 'bpni2';
                    let bpnoClass = isLeft ? 'bpno' : 'bpno2';

                    // 車輛與車牌動態區塊
                    let busiHtml = `<div class="${busiClass}" id="busi_${globalIndex}"></div>`;
                    let busoHtml = `<div class="${busoClass}" id="buso_${globalIndex}"></div>`;
                    let bpniHtml = `<div class="${bpniClass}" id="bni_${globalIndex}"></div>`;
                    let bpnoHtml = `<div class="${bpnoClass}" id="bno_${globalIndex}"></div>`;

                    if (stopData && stopData.plate_numbers && stopData.plate_numbers.length > 0) {
                        let etaSec = (stopData.minutes !== null && stopData.seconds !== null)
                            ? stopData.minutes * 60 + stopData.seconds
                            : null;

                        // 根據是否為接近中的車輛調整顯示
                        let isApproaching = stopData.is_approaching || false;

                        stopData.plate_numbers.forEach(plate => {
                            // 判斷車輛是在前一站往本站行駛還是已在本站
                            if (isApproaching) {
                                // 車輛正在前一站往本站行駛，顯示在線上
                                busoHtml = `<div class="${busoClass}" id="buso_${globalIndex}">
                            <span class="bnl">${plate}</span>
                             ${getBusImgTag(isLeft)}
                             </div>`;
                                bpnoHtml = `<div class="${bpnoClass}" id="bno_${globalIndex}"></div>`;
                            } else if (etaSec !== null && etaSec <= 60) {
                                // 車輛在當前站，且預計 1 分鐘內離站
                                busiHtml = `<div class="${busiClass}" id="busi_${globalIndex}">
                            <span class="bnl center">${plate}</span>
                             ${getBusImgTag(isLeft)}
                            </div>`;
                                bpniHtml = `<div class="${bpniClass}" id="bni_${globalIndex}"></div>`;
                            } else {
                                // 車輛在當前站，預計 1 分鐘後離站
                                busoHtml = `<div class="${busoClass}" id="buso_${globalIndex}">
                            <span class="bnl">${plate}</span>
                             ${getBusImgTag(isLeft)}
                            </div>`;
                                bpnoHtml = `<div class="${bpnoClass}" id="bno_${globalIndex}"></div>`;
                            }
                        });
                    }

                    let etaHtml = `<div class="${etaClass}" id="eta_${globalIndex}">
                        <span class="${etaText === '進站中' ? 'eta_coming' : 'eta_onroad'}">${etaText}</span>
                    </div>`;

                    let stopNameHtml = `<div class="${snzClass}"><span>${stopName}</span></div>`;
                    let stopIcon = `<div class="${siconClass}"></div>`;
                    let sflagHtml = `<div class="${sflagClass}" id="sflag_${globalIndex}"></div>`;

                    html += `<div class="${stopClass}" id="${stopId}" data-floating="${isLeft ? 'left' : 'right'}" data-stop="${stopName}">
                        ${stopNameHtml}
                        ${sflagHtml}
                        ${stopIcon}
                        ${etaHtml}
                        ${busiHtml}
                        ${busoHtml}
                        ${bpniHtml}
                        ${bpnoHtml}
                    </div>`;
                    globalIndex++;
                }
                // 行尾補空白格（偶數行最後一行）
                if (isLastRow && spaceCount > 0 && row % 2 === 0) {
                    for (let i = 0; i < spaceCount; i++) {
                        html += `<div class="sm left" style="visibility:hidden"></div>`;
                    }
                }
            }
            html += '<div style="clear:both;"></div>';
            html += '<div class="clear"></div></div>';
            document.getElementById('route-map').innerHTML = html;
        })
        .catch(error => {
            document.getElementById('route-map').innerHTML = '查詢失敗';
        });
}

function startAutoUpdate() {
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(() => {
        fetchEta(currentRoute, currentDirection, false);
    }, 30000);
}