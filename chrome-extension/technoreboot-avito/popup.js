// Technoreboot Avito Popup Script

document.addEventListener("DOMContentLoaded", async () => {
    const connBadge = document.getElementById("connBadge");
    const statusMsg = document.getElementById("statusMsg");
    const pairSection = document.getElementById("pairSection");
    const actionSection = document.getElementById("actionSection");
    const pairCodeInput = document.getElementById("pairCodeInput");
    const pairBtn = document.getElementById("pairBtn");
    const pairMsg = document.getElementById("pairMsg");
    const pageTypeTitle = document.getElementById("pageTypeTitle");
    const pageDetectInfo = document.getElementById("pageDetectInfo");
    const sendBtn = document.getElementById("sendBtn");
    const productLinkContainer = document.getElementById("productLinkContainer");
    const openProductBtn = document.getElementById("openProductBtn");
    const resultMsg = document.getElementById("resultMsg");
    const versionLabel = document.getElementById("versionLabel");

    // Dynamic version label from manifest.json
    if (versionLabel) {
        let manifestVer = "0.1.9";
        try {
            if (typeof chrome !== "undefined" && chrome.runtime && typeof chrome.runtime.getManifest === "function") {
                const manifest = chrome.runtime.getManifest();
                if (manifest && manifest.version) {
                    manifestVer = manifest.version;
                }
            }
        } catch (e) {}
        versionLabel.textContent = `Техноребут Avito v${manifestVer}`;
    }

    let currentExtractionData = null;
    let isPaired = false;
    let isServerOnline = false;

    // Check status on popup open
    chrome.runtime.sendMessage({ action: "get_status" }, response => {
        if (!response || !response.online) {
            // STATE A: Server Offline
            isServerOnline = false;
            isPaired = false;
            connBadge.className = "badge badge-offline";
            connBadge.textContent = "Offline";
            statusMsg.textContent = "Сервер Техноребут недоступен (проверьте, запущен ли контейнер core / admin-shell).";
            pairSection.style.display = "none";
            actionSection.style.display = "none";
            if (productLinkContainer) productLinkContainer.style.display = "none";
            return;
        } else if (!response.paired) {
            // STATE B: Online, Unpaired
            isServerOnline = true;
            isPaired = false;
            connBadge.className = "badge badge-offline";
            connBadge.textContent = "Не привязан";
            statusMsg.textContent = "Сервер Техноребут в сети. Требуется привязка расширения.";
            pairSection.style.display = "block";
            actionSection.style.display = "block";
            if (productLinkContainer) productLinkContainer.style.display = "none";
            inspectActiveTab();
        } else {
            // STATE C: Online, Paired
            isServerOnline = true;
            isPaired = true;
            connBadge.className = "badge badge-online";
            connBadge.textContent = "Подключен";
            statusMsg.textContent = "Расширение успешно привязано и готово к передаче данных.";
            pairSection.style.display = "none";
            actionSection.style.display = "block";
            if (productLinkContainer) productLinkContainer.style.display = "none";
            inspectActiveTab();
        }
    });

    // Pair Button click
    pairBtn.addEventListener("click", () => {
        const rawCode = pairCodeInput.value ? pairCodeInput.value.trim() : "";
        const cleanCode = rawCode.replace(/\D/g, "");

        if (!cleanCode || cleanCode.length !== 6) {
            pairMsg.className = "msg msg-error";
            pairMsg.textContent = "Введите 6-значный цифровой код.";
            return;
        }

        pairMsg.className = "msg";
        pairMsg.textContent = "Подключение...";
        pairBtn.disabled = true;

        chrome.runtime.sendMessage({ action: "pair", code: cleanCode }, res => {
            pairBtn.disabled = false;
            if (res && res.success) {
                isPaired = true;
                connBadge.className = "badge badge-online";
                connBadge.textContent = "Подключен";
                statusMsg.textContent = "Расширение успешно привязано и готово к передаче данных.";
                pairSection.style.display = "none";
                pairMsg.textContent = "";
                inspectActiveTab();
            } else {
                pairMsg.className = "msg msg-error";
                pairMsg.textContent = (res && res.message) || "Ошибка привязки кода.";
            }
        });
    });

    // Inspect Active Tab
    function inspectActiveTab() {
        if (productLinkContainer) productLinkContainer.style.display = "none";
        chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
            if (!tabs || tabs.length === 0) return;
            const activeTab = tabs[0];
            if (!activeTab.url || !activeTab.url.includes("avito.ru")) {
                pageTypeTitle.textContent = "Страница Avito";
                pageDetectInfo.textContent = "Откройте объявление на сайте avito.ru";
                sendBtn.disabled = true;
                return;
            }

            chrome.tabs.sendMessage(activeTab.id, { action: "extract_current_page", deepScan: false }, response => {
                if (!response) {
                    pageDetectInfo.textContent = "Обновите страницу Avito для активации расширения.";
                    sendBtn.disabled = true;
                    return;
                }

                currentExtractionData = response;
                if (response.error) {
                    pageDetectInfo.textContent = response.error;
                    sendBtn.disabled = true;
                } else if (response.page_type === "listing") {
                    pageTypeTitle.textContent = "Карточка объявления";
                    const item = response.listing;
                    const detectedPhotosCount = (item.photos && item.photos.length) || 0;
                    pageDetectInfo.innerHTML = `<strong>${item.title}</strong><br>ID: ${item.external_item_id}<br>Цена: ${item.price ? item.price + ' ₽' : 'Не указана'}<br>Обнаружено фото: <strong>${detectedPhotosCount}</strong> <span style="font-size: 11px; color: #888;">(сканирование...)</span>`;
                    
                    if (isPaired) {
                        sendBtn.disabled = false;
                        sendBtn.textContent = "Передать объявление в Техноребут";
                        resultMsg.textContent = "";
                    } else {
                        sendBtn.disabled = true;
                        sendBtn.textContent = "Передать объявление в Техноребут";
                        resultMsg.className = "msg msg-error";
                        resultMsg.textContent = "Передача станет доступна после привязки расширения (введите код выше).";
                    }

                    // Run asynchronous deep multi-pass scan
                    chrome.tabs.sendMessage(activeTab.id, { action: "extract_current_page", deepScan: true }, deepResponse => {
                        if (deepResponse && deepResponse.listing) {
                            currentExtractionData = deepResponse;
                            const deepCount = (deepResponse.listing.photos && deepResponse.listing.photos.length) || 0;
                            pageDetectInfo.innerHTML = `<strong>${deepResponse.listing.title}</strong><br>ID: ${deepResponse.listing.external_item_id}<br>Цена: ${deepResponse.listing.price ? deepResponse.listing.price + ' ₽' : 'Не указана'}<br>Обнаружено фото: <strong>${deepCount}</strong> ✓`;
                        }
                    });
                } else if (response.page_type === "my_listings") {
                    pageTypeTitle.textContent = "Мои объявления";
                    pageDetectInfo.textContent = `Обнаружено объявлений на странице: ${response.listings_count}`;
                    
                    if (isPaired) {
                        sendBtn.disabled = false;
                        sendBtn.textContent = "Передать список в Техноребут";
                        resultMsg.textContent = "";
                    } else {
                        sendBtn.disabled = true;
                        sendBtn.textContent = "Передать список в Техноребут";
                        resultMsg.className = "msg msg-error";
                        resultMsg.textContent = "Передача станет доступна после привязки расширения.";
                    }
                }
            });
        });
    }

    // Send Button click
    sendBtn.addEventListener("click", () => {
        if (!isPaired) {
            resultMsg.className = "msg msg-error";
            resultMsg.textContent = "Расширение не привязано. Введите код подключения выше.";
            return;
        }
        if (!currentExtractionData) return;

        sendBtn.disabled = true;
        resultMsg.className = "msg";
        resultMsg.textContent = "Передача данных...";

        const action = currentExtractionData.page_type === "listing" ? "ingest_listing" : "ingest_my_listings";
        chrome.runtime.sendMessage({ action: action, payload: currentExtractionData }, res => {
            sendBtn.disabled = false;
            if (res && res.success && res.product_id != null) {
                const photosImported = res.photos_imported || (res.details && res.details.photos_imported) || 0;
                const photosSkipped = res.photos_skipped || (res.details && res.details.photos_skipped) || 0;
                const photosTotal = res.photos_total !== undefined ? res.photos_total : 
                    ((res.details && res.details.photos_total !== undefined) ? res.details.photos_total : 
                    (photosImported + photosSkipped));

                if (openProductBtn && productLinkContainer) {
                    const targetUrl = `http://localhost:8011/products/${res.product_id}`;
                    openProductBtn.onclick = () => {
                        chrome.tabs.create({ url: targetUrl });
                    };
                    productLinkContainer.style.display = "block";
                }

                if (res.status === "partial" || (res.details && res.details.result === "partial")) {
                    resultMsg.className = "msg msg-warning";
                    resultMsg.innerHTML = `Основные данные обновлены, но фотографии импортировать не удалось.<br>Product ID: <strong>${res.product_id}</strong>`;
                } else {
                    resultMsg.className = "msg msg-success";
                    if (photosImported > 0 && photosSkipped > 0) {
                        resultMsg.innerHTML = `✓ Объявление обновлено.<br>Product ID: <strong>${res.product_id}</strong><br>Добавлено новых фото: <strong>${photosImported}</strong> (всего в товаре: <strong>${photosTotal}</strong>)`;
                    } else if (photosImported === 0 && photosSkipped > 0) {
                        resultMsg.innerHTML = `✓ Карточка актуальна.<br>Product ID: <strong>${res.product_id}</strong><br>Все фотографии синхронизированы (всего: <strong>${photosTotal}</strong>)`;
                    } else {
                        resultMsg.innerHTML = `✓ Объявление импортировано.<br>Product ID: <strong>${res.product_id}</strong><br>Фотографий: <strong>${photosTotal}</strong>`;
                    }
                }
            } else {
                resultMsg.className = "msg msg-error";
                const errDetail = res && res.message ? res.message : "Ошибка импорта товара в Core API.";
                resultMsg.innerHTML = `✕ Объявление получено, но импорт товара завершился ошибкой.<br>${errDetail}`;
            }
        });
    });
});
