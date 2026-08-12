// Technoreboot Avito Popup Script (v0.1.2)

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
    const resultMsg = document.getElementById("resultMsg");

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
            statusMsg.textContent = "✕ Нет подключения к локальному серверу Техноребут (localhost:8011). Запустите Техноребут.";
            pairSection.style.display = "none";
            actionSection.style.display = "none";
            return;
        }

        isServerOnline = true;
        isPaired = response.paired === true;

        if (isPaired) {
            // STATE D: Server Reachable & Paired
            connBadge.className = "badge badge-paired";
            connBadge.textContent = "Расширение привязано";
            statusMsg.textContent = "✓ Сервер доступен. Расширение привязано к Техноребут.";
            pairSection.style.display = "none";
            actionSection.style.display = "block";
            inspectActiveTab();
        } else {
            // STATE B/C: Server Reachable, UNPAIRED
            connBadge.className = "badge badge-online";
            connBadge.textContent = "Сервер доступен";
            statusMsg.textContent = response.has_token ? 
                "✕ Привязка устарела. Введите новый код подключения." : 
                "✓ Сервер Техноребут доступен. Введите код для подключения расширения.";
            pairSection.style.display = "block";
            actionSection.style.display = "block";
            inspectActiveTab();
        }
    });

    // Pair button click
    pairBtn.addEventListener("click", () => {
        const rawCode = pairCodeInput.value ? pairCodeInput.value.trim() : "";
        const cleanCode = rawCode.replace(/\D/g, "");

        if (!cleanCode || cleanCode.length !== 6) {
            pairMsg.className = "msg msg-error";
            pairMsg.textContent = "Введите ровно 6 цифр кода подключения.";
            return;
        }

        pairMsg.className = "msg";
        pairMsg.textContent = "Проверка кода...";
        pairBtn.disabled = true;

        chrome.runtime.sendMessage({ action: "pair", code: cleanCode }, res => {
            pairBtn.disabled = false;
            if (res && res.success) {
                pairMsg.className = "msg msg-success";
                pairMsg.textContent = res.message;
                setTimeout(() => window.location.reload(), 800);
            } else {
                pairMsg.className = "msg msg-error";
                pairMsg.textContent = (res && res.message) || "Ошибка привязки кода.";
            }
        });
    });

    // Inspect Active Tab
    function inspectActiveTab() {
        chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
            if (!tabs || tabs.length === 0) return;
            const activeTab = tabs[0];
            if (!activeTab.url || !activeTab.url.includes("avito.ru")) {
                pageTypeTitle.textContent = "Страница Avito";
                pageDetectInfo.textContent = "Откройте объявление на сайте avito.ru";
                sendBtn.disabled = true;
                return;
            }

            chrome.tabs.sendMessage(activeTab.id, { action: "extract_current_page" }, response => {
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
                    pageDetectInfo.innerHTML = `<strong>${item.title}</strong><br>ID: ${item.external_item_id}<br>Цена: ${item.price ? item.price + ' ₽' : 'Не указана'}`;
                    
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
                resultMsg.className = "msg msg-success";
                resultMsg.innerHTML = `✓ Объявление импортировано в Техноребут.<br>Product ID: <strong>${res.product_id}</strong><br>Результат: ${res.result || 'Created'}`;
            } else {
                resultMsg.className = "msg msg-error";
                const errDetail = res && res.message ? res.message : "Ошибка импорта товара в Core API.";
                resultMsg.innerHTML = `✕ Объявление получено, но импорт товара завершился ошибкой.<br>${errDetail}`;
            }
        });
    });
});
