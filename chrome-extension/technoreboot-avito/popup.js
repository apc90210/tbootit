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
    const resultMsg = document.getElementById("resultMsg");

    let currentExtractionData = null;

    // Check status
    chrome.runtime.sendMessage({ action: "get_status" }, response => {
        if (response && response.online) {
            if (response.paired) {
                connBadge.className = "badge badge-paired";
                connBadge.textContent = "Подключен";
                statusMsg.textContent = "✓ Подключено к локальному серверу Техноребут.";
                pairSection.style.display = "none";
                actionSection.style.display = "block";
                inspectActiveTab();
            } else {
                connBadge.className = "badge badge-online";
                connBadge.textContent = "Требуется привязка";
                statusMsg.textContent = "Локальный сервер доступен. Требуется код подключения.";
                pairSection.style.display = "block";
                actionSection.style.display = "none";
            }
        } else {
            connBadge.className = "badge badge-offline";
            connBadge.textContent = "Offline";
            statusMsg.textContent = "✕ Нет подключения к локальному серверу Техноребут (localhost:8011). Запустите Техноребут.";
            pairSection.style.display = "none";
            actionSection.style.display = "none";
        }
    });

    // Pair button click
    pairBtn.addEventListener("click", () => {
        const code = pairCodeInput.value.trim();
        if (!code || code.length !== 6) {
            pairMsg.className = "msg msg-error";
            pairMsg.textContent = "Введите 6-значный код подключения.";
            return;
        }
        pairMsg.className = "msg";
        pairMsg.textContent = "Проверка кода...";
        chrome.runtime.sendMessage({ action: "pair", code: code }, res => {
            if (res && res.success) {
                pairMsg.className = "msg msg-success";
                pairMsg.textContent = res.message;
                setTimeout(() => window.location.reload(), 1000);
            } else {
                pairMsg.className = "msg msg-error";
                pairMsg.textContent = (res && res.message) || "Ошибка привязкой кода.";
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
                    sendBtn.disabled = false;
                    sendBtn.textContent = "Передать объявление в Техноребут";
                } else if (response.page_type === "my_listings") {
                    pageTypeTitle.textContent = "Мои объявления";
                    pageDetectInfo.textContent = `Обнаружено объявлений на странице: ${response.listings_count}`;
                    sendBtn.disabled = false;
                    sendBtn.textContent = "Передать список в Техноребут";
                }
            });
        });
    }

    // Send Button click
    sendBtn.addEventListener("click", () => {
        if (!currentExtractionData) return;
        sendBtn.disabled = true;
        resultMsg.className = "msg";
        resultMsg.textContent = "Передача данных...";

        const action = currentExtractionData.page_type === "listing" ? "ingest_listing" : "ingest_my_listings";
        chrome.runtime.sendMessage({ action: action, payload: currentExtractionData }, res => {
            sendBtn.disabled = false;
            if (res && res.success) {
                resultMsg.className = "msg msg-success";
                resultMsg.textContent = res.message;
            } else {
                resultMsg.className = "msg msg-error";
                resultMsg.textContent = (res && res.message) || "Ошибка передачи.";
            }
        });
    });
});
